import base64
import hashlib
import hmac
import secrets
import time
import uuid
from datetime import UTC, datetime

import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from redis.exceptions import RedisError

from .auth_challenge_store import (
    AuthChallengeRecord,
    RedisAuthChallengeStore,
)
from .calls import registry, utc_now_iso
from .config import get_settings
from .models import (
    AuthChallengeRequest,
    AuthChallengeResponse,
    AuthVerifyRequest,
    AuthVerifyResponse,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    HealthResponse,
    IceServerConfig,
    IceServersResponse,
    ObservabilitySnapshotResponse,
    ReadinessResponse,
    TurnCredentialsMeta,
)
from .observability import observability
from .operational_logging import clear_request_context, log_event, set_request_context
from .signaling import hub
from .tracing import configure_tracing, extract_context, shutdown_tracing, start_span

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:
    request_id = _as_non_empty_string(request.headers.get("x-request-id")) or uuid.uuid4().hex
    request.state.request_id = request_id
    set_request_context(
        request_id=request_id,
        route=request.url.path,
        method=request.method,
    )
    observability.incr(f"http.requests.{request.method.lower()}.{request.url.path}")
    started_at = time.perf_counter()
    trace_context = extract_context(dict(request.headers))
    try:
        with start_span(
            "http.request",
            context=trace_context,
            attributes={
                "http.method": request.method,
                "http.path": request.url.path,
                "request.id": request_id,
            },
        ) as span:
            try:
                response = await call_next(request)
            except Exception as exc:
                span.record_exception(exc)
                log_event(
                    level="ERROR",
                    event="http.request.failed",
                    message="HTTP request failed",
                    service=settings.app_name,
                    env="dev" if settings.debug else "prod",
                    component="http",
                    reason_code="exception",
                )
                raise
            span.set_attribute("http.status_code", response.status_code)
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            log_event(
                level="INFO",
                event="http.request.completed",
                message="HTTP request completed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="http",
                reason_code="ok" if response.status_code < 400 else "http_error",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        clear_request_context()


@app.on_event("startup")
async def startup_event() -> None:
    configure_tracing(settings)
    with start_span("app.startup"):
        await hub.start()
        hub.revoke_instance_presence()
        await _reconcile_sessions_after_restart()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    with start_span("app.shutdown"):
        await hub.stop()
    shutdown_tracing()

# Temporary in-memory store for local development.
registered_devices: dict[str, dict] = {}

auth_challenge_store = RedisAuthChallengeStore(
    redis_client=Redis.from_url(
        settings.auth_challenge_redis_url,
        decode_responses=True,
    ),
    key_prefix=settings.auth_challenge_store_prefix,
)

CLIENT_MESSAGE_TYPES = {
    "call.invite",
    "call.ringing",
    "call.accept",
    "call.reject",
    "call.cancel",
    "call.hangup",
    "webrtc.offer",
    "webrtc.answer",
    "webrtc.ice-candidate",
    "webrtc.ice-restart",
    "system.ping",
}

EVENT_ALLOWED_STATES: dict[str, set[str]] = {
    "call.ringing": {"ringing"},
    "call.accept": {"ringing"},
    "call.reject": {"ringing"},
    "call.cancel": {"ringing"},
    "call.hangup": {"connecting", "connected"},
    "webrtc.offer": {"connecting", "connected"},
    "webrtc.answer": {"connecting", "connected"},
    "webrtc.ice-candidate": {"connecting", "connected"},
    "webrtc.ice-restart": {"connecting", "connected"},
}


def _as_non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _base_message(
    *,
    message_type: str,
    from_nickname: str,
    to_nickname: str,
    call_id: str | None = None,
    from_device_id: str | None = None,
    target_device_id: str | None = None,
    payload: object | None = None,
    error: str | None = None,
) -> dict[str, object]:
    message: dict[str, object] = {
        "type": message_type,
        "timestamp": utc_now_iso(),
        "from_nickname": from_nickname,
        "to_nickname": to_nickname,
    }
    if call_id is not None:
        message["call_id"] = call_id
    if from_device_id is not None:
        message["from_device_id"] = from_device_id
    if target_device_id is not None:
        message["target_device_id"] = target_device_id
    if payload is not None:
        message["payload"] = payload
    if error is not None:
        message["error"] = error
    return message


def _state_transition_error_message(*, event: str, state: str) -> str:
    return (
        f"invalid_state_transition:{event}:state={state}. "
        f"Use protocol-allowed action for current call state."
    )


def _random_nonce_b64url(num_bytes: int) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(num_bytes)).decode("ascii").rstrip("=")


def _build_auth_canonical_payload(
    *,
    challenge_id: str,
    nickname: str,
    device_id: str,
    nonce: str,
    issued_at: int,
    expires_at: int,
) -> str:
    return "\n".join(
        [
            "flexphone-auth-v1",
            f"challenge_id={challenge_id}",
            f"nickname={nickname}",
            f"device_id={device_id}",
            f"nonce={nonce}",
            f"issued_at={issued_at}",
            f"expires_at={expires_at}",
        ]
    )


def _base64url_decode(value: str) -> bytes:
    normalized = value.strip()
    if not normalized:
        raise ValueError("empty base64url payload")
    padded = normalized + ("=" * (-len(normalized) % 4))
    return base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)


def _load_registered_public_key(public_key_spki_base64: str) -> ec.EllipticCurvePublicKey:
    try:
        spki_bytes = base64.b64decode(public_key_spki_base64.encode("ascii"), validate=True)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid public key encoding") from exc

    try:
        public_key = serialization.load_der_public_key(spki_bytes)
    except ValueError as exc:
        raise ValueError("invalid public key format") from exc

    if not isinstance(public_key, ec.EllipticCurvePublicKey):
        raise ValueError("public key is not elliptic curve")
    if not isinstance(public_key.curve, ec.SECP256R1):
        raise ValueError("public key curve must be P-256")
    return public_key


def _verify_auth_signature(
    *,
    public_key_spki_base64: str,
    canonical_payload: str,
    signature_b64url: str,
) -> bool:
    try:
        signature_bytes = _base64url_decode(signature_b64url)
        public_key = _load_registered_public_key(public_key_spki_base64)
        public_key.verify(
            signature_bytes,
            canonical_payload.encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except (InvalidSignature, TypeError, ValueError):
        return False


def _issue_signaling_access_token(
    *,
    nickname: str,
    device_id: str,
    now_unix: int,
) -> tuple[str, int]:
    auth_jwt_secret = settings.auth_jwt_secret
    if not auth_jwt_secret:
        raise HTTPException(status_code=500, detail="auth_jwt_secret_missing")

    expires_at = now_unix + settings.auth_jwt_ttl_seconds
    claims = {
        "iss": settings.auth_jwt_issuer,
        "sub": f"{nickname}:{device_id}",
        "nickname": nickname,
        "device_id": device_id,
        "aud": settings.auth_jwt_audience,
        "iat": now_unix,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(claims, auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)
    if isinstance(token, bytes):
        token = token.decode("ascii")
    return token, expires_at


def _decode_signaling_access_token(access_token: str) -> dict[str, object]:
    auth_jwt_secret = settings.auth_jwt_secret
    if not auth_jwt_secret:
        raise ValueError("token_invalid")

    try:
        decoded = jwt.decode(
            access_token,
            auth_jwt_secret,
            algorithms=[settings.auth_jwt_algorithm],
            audience=settings.auth_jwt_audience,
            issuer=settings.auth_jwt_issuer,
            options={"require": ["iss", "sub", "aud", "iat", "exp", "jti"]},
            leeway=settings.auth_clock_skew_seconds,
        )
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("token_expired") from exc
    except jwt.InvalidAudienceError as exc:
        raise ValueError("token_wrong_audience") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("token_invalid") from exc

    if not isinstance(decoded, dict):
        raise ValueError("token_invalid")
    return decoded


def _validate_signaling_token_claims(*, nickname: str, claims: dict[str, object]) -> str:
    token_nickname = _as_non_empty_string(claims.get("nickname"))
    token_device_id = _as_non_empty_string(claims.get("device_id"))
    token_sub = _as_non_empty_string(claims.get("sub"))

    if token_nickname != nickname:
        raise ValueError("token_wrong_nickname")
    if token_device_id is None:
        raise ValueError("token_wrong_device")
    if token_sub != f"{token_nickname}:{token_device_id}":
        raise ValueError("token_wrong_device")

    registration = registered_devices.get(nickname)
    if registration is None or registration.get("device_id") != token_device_id:
        raise ValueError("token_wrong_device")

    return token_device_id


def _build_turn_rest_credential(secret: str, username: str) -> str:
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=username.encode("utf-8"),
        digestmod=hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _build_turn_meta() -> tuple[IceServerConfig, TurnCredentialsMeta]:
    if settings.webrtc_turn_auth_secret:
        now_unix = int(time.time())
        expires_at_unix = now_unix + settings.webrtc_turn_auth_ttl_seconds
        turn_username = f"{expires_at_unix}:{settings.webrtc_turn_auth_user_label}"
        turn_credential = _build_turn_rest_credential(
            settings.webrtc_turn_auth_secret,
            turn_username,
        )
        return (
            IceServerConfig(
                urls=settings.webrtc_turn_urls,
                username=turn_username,
                credential=turn_credential,
            ),
            TurnCredentialsMeta(
                mode="ephemeral",
                username=turn_username,
                ttl_seconds=settings.webrtc_turn_auth_ttl_seconds,
                expires_at_unix=expires_at_unix,
                clock_skew_tolerance_seconds=settings.webrtc_turn_auth_clock_skew_seconds,
                username_scheme="timestamp:user_label",
            ),
        )

    if settings.webrtc_turn_username and settings.webrtc_turn_password:
        return (
            IceServerConfig(
                urls=settings.webrtc_turn_urls,
                username=settings.webrtc_turn_username,
                credential=settings.webrtc_turn_password,
            ),
            TurnCredentialsMeta(
                mode="static",
                username=settings.webrtc_turn_username,
            ),
        )

    raise HTTPException(
        status_code=500,
        detail=(
            "TURN URLs are configured but TURN credentials are missing. "
            "Set either FLEXPHONE_WEBRTC_TURN_AUTH_SECRET (ephemeral TURN REST auth) "
            "or FLEXPHONE_WEBRTC_TURN_USERNAME/FLEXPHONE_WEBRTC_TURN_PASSWORD (static dev auth)."
        ),
    )


async def _cleanup_expired_ringing_sessions() -> None:
    with start_span("reconcile.cleanup_expired_ringing") as span:
        expired_sessions = registry.expire_ringing(max_age_seconds=45)
        span.set_attribute("reconcile.expired_count", len(expired_sessions))
        log_event(
            level="INFO",
            event="reconcile.cleanup.started",
            message="Expired ringing cleanup started",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="reconcile",
            reason_code="reconcile_started",
            expired_count=len(expired_sessions),
        )
        for session in expired_sessions:
            observability.incr("reconcile.cleanup.ringing_timeout")
            timeout_message = _base_message(
                message_type="call.cancel",
                from_nickname="server",
                to_nickname=session.caller,
                call_id=session.call_id,
                payload={"reason": "invite_timeout"},
            )
            await hub.send_to(session.caller, timeout_message)
            await hub.send_to(
                session.callee,
                _base_message(
                    message_type="call.cancel",
                    from_nickname="server",
                    to_nickname=session.callee,
                    call_id=session.call_id,
                    payload={"reason": "invite_timeout"},
                ),
            )
        log_event(
            level="INFO",
            event="reconcile.cleanup.completed",
            message="Expired ringing cleanup completed",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="reconcile",
            reason_code="reconcile_completed",
            cleaned_count=len(expired_sessions),
        )


async def _deliver_or_queue_system_message(*, nickname: str, message: dict[str, object]) -> None:
    delivered = await hub.send_to(nickname, message)
    if delivered:
        return
    await hub.enqueue_notice(nickname, message)


async def _reconcile_sessions_after_restart() -> None:
    with start_span("reconcile.startup") as span:
        sessions = registry.all_sessions()
        span.set_attribute("reconcile.session_count", len(sessions))
        log_event(
            level="INFO",
            event="reconcile.startup.started",
            message="Startup reconciliation started",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="reconcile",
            reason_code="reconcile_started",
            session_count=len(sessions),
        )
        now = datetime.now(UTC)
        cleaned_ringing = 0
        cleaned_connected = 0
        for session in sessions:
            if session.state == "ringing":
                try:
                    created_at = datetime.fromisoformat(session.created_at)
                except ValueError:
                    created_at = now
                age_seconds = (now - created_at).total_seconds()
                caller_online = hub.is_online(session.caller)
                callee_online = hub.is_online(session.callee)
                if age_seconds <= 45 and caller_online and callee_online:
                    continue

                removed = registry.remove(session.call_id)
                if removed is None:
                    continue
                observability.incr("reconcile.cleanup.ringing_restart")
                cleaned_ringing += 1
                await _deliver_or_queue_system_message(
                    nickname=removed.caller,
                    message=_base_message(
                        message_type="call.cancel",
                        from_nickname="server",
                        to_nickname=removed.caller,
                        call_id=removed.call_id,
                        payload={"reason": "backend_restart_cleanup"},
                    ),
                )
                await _deliver_or_queue_system_message(
                    nickname=removed.callee,
                    message=_base_message(
                        message_type="call.cancel",
                        from_nickname="server",
                        to_nickname=removed.callee,
                        call_id=removed.call_id,
                        payload={"reason": "backend_restart_cleanup"},
                    ),
                )
                continue

            if session.state in {"connecting", "connected"}:
                removed = registry.remove(session.call_id)
                if removed is None:
                    continue
                observability.incr("reconcile.cleanup.connected_restart")
                cleaned_connected += 1
                for participant, peer in (
                    (removed.caller, removed.callee),
                    (removed.callee, removed.caller),
                ):
                    await _deliver_or_queue_system_message(
                        nickname=participant,
                        message=_base_message(
                            message_type="call.hangup",
                            from_nickname="server",
                            to_nickname=participant,
                            call_id=removed.call_id,
                            payload={
                                "reason": "call_terminated_backend_restart",
                                "peer_nickname": peer,
                            },
                        ),
                    )
        log_event(
            level="INFO",
            event="reconcile.startup.completed",
            message="Startup reconciliation completed",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="reconcile",
            reason_code="reconcile_completed",
            cleaned_ringing=cleaned_ringing,
            cleaned_connected=cleaned_connected,
        )


def _check_redis_dependency(redis_url: str) -> str:
    try:
        redis_client = Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        return "ok" if redis_client.ping() else "unavailable"
    except RedisError:
        return "unavailable"


def _collect_runtime_readiness_checks() -> dict[str, str]:
    return {
        "auth_challenge_redis": _check_redis_dependency(settings.auth_challenge_redis_url),
        "signaling_redis": _check_redis_dependency(settings.signaling_redis_url),
        "otel_exporter": settings.otel_exporter,
    }


def _is_runtime_ready(checks: dict[str, str]) -> bool:
    return (
        checks.get("auth_challenge_redis") == "ok"
        and checks.get("signaling_redis") == "ok"
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    observability.incr("health.ok")
    return HealthResponse(status="ok", app=settings.app_name)


@app.get("/ready", response_model=ReadinessResponse)
async def ready() -> ReadinessResponse | JSONResponse:
    with start_span("runtime.readiness") as span:
        checks = _collect_runtime_readiness_checks()
        status = "ok" if _is_runtime_ready(checks) else "degraded"
        span.set_attribute("runtime.readiness.status", status)

        response_payload = ReadinessResponse(
            status=status,
            app=settings.app_name,
            checks=checks,
        )

        if status == "ok":
            observability.incr("ready.ok")
            log_event(
                level="INFO",
                event="runtime.ready.ok",
                message="Runtime dependencies are ready",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="runtime",
                reason_code="dependency_ready",
                auth_challenge_redis=checks.get("auth_challenge_redis"),
                signaling_redis=checks.get("signaling_redis"),
                otel_exporter=checks.get("otel_exporter"),
            )
            return response_payload

        observability.incr("ready.degraded")
        log_event(
            level="WARNING",
            event="runtime.ready.degraded",
            message="Runtime dependencies are degraded",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="runtime",
            reason_code="dependency_degraded",
            auth_challenge_redis=checks.get("auth_challenge_redis"),
            signaling_redis=checks.get("signaling_redis"),
            otel_exporter=checks.get("otel_exporter"),
        )
        return JSONResponse(status_code=503, content=response_payload.model_dump())


@app.get("/observability/snapshot", response_model=ObservabilitySnapshotResponse)
async def observability_snapshot() -> ObservabilitySnapshotResponse:
    snapshot = observability.snapshot()
    return ObservabilitySnapshotResponse(
        timestamp=str(snapshot["timestamp"]),
        uptime_seconds=int(snapshot["uptime_seconds"]),
        counters={str(k): int(v) for k, v in dict(snapshot["counters"]).items()},
    )


@app.get("/webrtc/ice-servers", response_model=IceServersResponse)
async def webrtc_ice_servers() -> IceServersResponse:
    ice_servers = [IceServerConfig(urls=settings.webrtc_stun_urls)]
    turn_credentials: TurnCredentialsMeta | None = None

    if settings.webrtc_turn_urls:
        turn_server, turn_credentials = _build_turn_meta()
        ice_servers.append(turn_server)

    return IceServersResponse(
        ice_servers=ice_servers,
        ice_transport_policy="relay" if settings.webrtc_force_relay else "all",
        turn_credentials=turn_credentials,
    )


@app.post("/devices/register", response_model=DeviceRegisterResponse)
async def register_device(payload: DeviceRegisterRequest) -> DeviceRegisterResponse:
    nickname = payload.nickname.strip()

    if not nickname.startswith("@"):
        observability.incr("auth.register.rejected.invalid_nickname")
        raise HTTPException(status_code=400, detail="Nickname must start with @")

    registered_devices[nickname] = {
        "device_id": payload.device_id,
        "public_key_spki_base64": payload.public_key_spki_base64,
    }
    observability.incr("auth.register.ok")

    return DeviceRegisterResponse(
        ok=True,
        nickname=nickname,
        device_id=payload.device_id,
    )


@app.post("/auth/challenge", response_model=AuthChallengeResponse)
async def create_auth_challenge(
    payload: AuthChallengeRequest,
    request: Request,
) -> AuthChallengeResponse:
    with start_span(
        "auth.challenge",
        context=extract_context(dict(request.headers)),
        attributes={
            "auth.nickname": payload.nickname,
            "auth.device_id": payload.device_id,
            "request.id": getattr(request.state, "request_id", None),
        },
    ) as span:
        nickname = payload.nickname.strip()

        if not nickname.startswith("@"):
            observability.incr("auth.challenge.rejected.invalid_nickname")
            span.set_attribute("auth.result", "rejected_invalid_nickname")
            log_event(
                level="WARNING",
                event="auth.challenge.rejected",
                message="Auth challenge rejected",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="invalid_nickname",
                nickname=nickname,
                device_id=payload.device_id,
                status_code=400,
            )
            raise HTTPException(status_code=400, detail="Nickname must start with @")

        registration = registered_devices.get(nickname)
        if registration is None:
            observability.incr("auth.challenge.rejected.device_not_registered")
            span.set_attribute("auth.result", "rejected_device_not_registered")
            log_event(
                level="WARNING",
                event="auth.challenge.rejected",
                message="Auth challenge rejected",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="device_not_registered",
                nickname=nickname,
                device_id=payload.device_id,
                status_code=404,
            )
            raise HTTPException(status_code=404, detail="Device is not registered for this nickname")

        if registration.get("device_id") != payload.device_id:
            observability.incr("auth.challenge.rejected.wrong_device")
            span.set_attribute("auth.result", "rejected_wrong_device")
            log_event(
                level="WARNING",
                event="auth.challenge.rejected",
                message="Auth challenge rejected",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="wrong_device",
                nickname=nickname,
                device_id=payload.device_id,
                status_code=403,
            )
            raise HTTPException(status_code=403, detail="Device ID does not match nickname registration")

        now_unix = int(time.time())
        challenge_id = str(uuid.uuid4())
        nonce = _random_nonce_b64url(settings.auth_challenge_nonce_bytes)
        issued_at = now_unix
        expires_at = now_unix + settings.auth_challenge_ttl_seconds
        canonical_payload = _build_auth_canonical_payload(
            challenge_id=challenge_id,
            nickname=nickname,
            device_id=payload.device_id,
            nonce=nonce,
            issued_at=issued_at,
            expires_at=expires_at,
        )

        challenge_record = AuthChallengeRecord(
            challenge_id=challenge_id,
            nickname=nickname,
            device_id=payload.device_id,
            nonce=nonce,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        try:
            auth_challenge_store.create(
                challenge_record,
                clock_skew_seconds=settings.auth_clock_skew_seconds,
                retention_seconds=settings.auth_challenge_retention_seconds,
            )
        except RedisError as exc:
            observability.incr("auth.challenge.rejected.store_unavailable")
            span.set_attribute("auth.result", "rejected_store_unavailable")
            log_event(
                level="ERROR",
                event="auth.challenge.rejected",
                message="Auth challenge store unavailable",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_store_unavailable",
                nickname=nickname,
                device_id=payload.device_id,
                status_code=503,
            )
            raise HTTPException(status_code=503, detail="challenge_store_unavailable") from exc

        observability.incr("auth.challenge.ok")
        span.set_attribute("auth.result", "ok")
        span.set_attribute("auth.challenge_id", challenge_id)
        log_event(
            level="INFO",
            event="auth.challenge.issued",
            message="Auth challenge issued",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="auth",
            reason_code="ok",
            nickname=nickname,
            device_id=payload.device_id,
            status_code=200,
        )

        return AuthChallengeResponse(
            challenge_id=challenge_id,
            nickname=nickname,
            device_id=payload.device_id,
            nonce=nonce,
            issued_at=issued_at,
            expires_at=expires_at,
            canonical_payload=canonical_payload,
        )


@app.post("/auth/verify", response_model=AuthVerifyResponse)
async def verify_auth_challenge(
    payload: AuthVerifyRequest,
    request: Request,
) -> AuthVerifyResponse:
    with start_span(
        "auth.verify",
        context=extract_context(dict(request.headers)),
        attributes={
            "auth.challenge_id": payload.challenge_id,
            "auth.nickname": payload.nickname,
            "auth.device_id": payload.device_id,
            "request.id": getattr(request.state, "request_id", None),
        },
    ) as span:
        now_unix = int(time.time())
        try:
            challenge = auth_challenge_store.get(payload.challenge_id)
        except RedisError as exc:
            observability.incr("auth.verify.rejected.store_unavailable")
            span.set_attribute("auth.result", "rejected_store_unavailable")
            log_event(
                level="ERROR",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_store_unavailable",
                nickname=payload.nickname,
                device_id=payload.device_id,
                status_code=503,
            )
            raise HTTPException(status_code=503, detail="challenge_store_unavailable") from exc

        if challenge is None:
            observability.incr("auth.verify.rejected.challenge_not_found")
            span.set_attribute("auth.result", "rejected_challenge_not_found")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_not_found",
                nickname=payload.nickname,
                device_id=payload.device_id,
                status_code=404,
            )
            raise HTTPException(status_code=404, detail="challenge_not_found")

        if challenge.expires_at + settings.auth_clock_skew_seconds < now_unix:
            observability.incr("auth.verify.rejected.challenge_expired")
            span.set_attribute("auth.result", "rejected_challenge_expired")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_expired",
                nickname=payload.nickname,
                device_id=payload.device_id,
                status_code=401,
            )
            raise HTTPException(status_code=401, detail="challenge_expired")

        if challenge.consumed:
            observability.incr("auth.verify.rejected.challenge_consumed")
            span.set_attribute("auth.result", "rejected_challenge_consumed")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_consumed",
                nickname=payload.nickname,
                device_id=payload.device_id,
                status_code=409,
            )
            raise HTTPException(status_code=409, detail="challenge_consumed")

        nickname = payload.nickname.strip()
        device_id = payload.device_id
        if nickname != challenge.nickname or device_id != challenge.device_id:
            observability.incr("auth.verify.rejected.wrong_nickname_or_device")
            span.set_attribute("auth.result", "rejected_wrong_nickname_or_device")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="wrong_nickname_or_device",
                nickname=payload.nickname,
                device_id=payload.device_id,
                status_code=403,
            )
            raise HTTPException(status_code=403, detail="wrong_nickname_or_device")

        registration = registered_devices.get(nickname)
        if registration is None or registration.get("device_id") != device_id:
            observability.incr("auth.verify.rejected.device_not_registered")
            span.set_attribute("auth.result", "rejected_device_not_registered")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="device_not_registered",
                nickname=nickname,
                device_id=device_id,
                status_code=404,
            )
            raise HTTPException(status_code=404, detail="device_not_registered")

        public_key_spki_base64 = registration.get("public_key_spki_base64")
        if not isinstance(public_key_spki_base64, str) or not public_key_spki_base64.strip():
            observability.incr("auth.verify.rejected.device_not_registered")
            span.set_attribute("auth.result", "rejected_device_not_registered")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="device_not_registered",
                nickname=nickname,
                device_id=device_id,
                status_code=404,
            )
            raise HTTPException(status_code=404, detail="device_not_registered")

        canonical_payload = _build_auth_canonical_payload(
            challenge_id=challenge.challenge_id,
            nickname=challenge.nickname,
            device_id=challenge.device_id,
            nonce=challenge.nonce,
            issued_at=challenge.issued_at,
            expires_at=challenge.expires_at,
        )
        if not _verify_auth_signature(
            public_key_spki_base64=public_key_spki_base64,
            canonical_payload=canonical_payload,
            signature_b64url=payload.signature,
        ):
            observability.incr("auth.verify.rejected.invalid_signature")
            span.set_attribute("auth.result", "rejected_invalid_signature")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="signature_mismatch",
                nickname=nickname,
                device_id=device_id,
                status_code=401,
            )
            raise HTTPException(status_code=401, detail="invalid_signature")

        try:
            consume_status = auth_challenge_store.consume(
                payload.challenge_id,
                now_unix=now_unix,
                clock_skew_seconds=settings.auth_clock_skew_seconds,
            )
        except RedisError as exc:
            observability.incr("auth.verify.rejected.store_unavailable")
            span.set_attribute("auth.result", "rejected_store_unavailable")
            log_event(
                level="ERROR",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_store_unavailable",
                nickname=nickname,
                device_id=device_id,
                status_code=503,
            )
            raise HTTPException(status_code=503, detail="challenge_store_unavailable") from exc

        if consume_status == "not_found":
            observability.incr("auth.verify.rejected.challenge_not_found")
            span.set_attribute("auth.result", "rejected_challenge_not_found")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_not_found",
                nickname=nickname,
                device_id=device_id,
                status_code=404,
            )
            raise HTTPException(status_code=404, detail="challenge_not_found")
        if consume_status == "expired":
            observability.incr("auth.verify.rejected.challenge_expired")
            span.set_attribute("auth.result", "rejected_challenge_expired")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_expired",
                nickname=nickname,
                device_id=device_id,
                status_code=401,
            )
            raise HTTPException(status_code=401, detail="challenge_expired")
        if consume_status == "consumed":
            observability.incr("auth.verify.rejected.challenge_consumed")
            span.set_attribute("auth.result", "rejected_challenge_consumed")
            log_event(
                level="WARNING",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_consumed",
                nickname=nickname,
                device_id=device_id,
                status_code=409,
            )
            raise HTTPException(status_code=409, detail="challenge_consumed")
        if consume_status != "ok":
            observability.incr("auth.verify.rejected.store_unavailable")
            span.set_attribute("auth.result", "rejected_store_unavailable")
            log_event(
                level="ERROR",
                event="auth.verify.failed",
                message="Auth verify failed",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="auth",
                reason_code="challenge_store_unavailable",
                nickname=nickname,
                device_id=device_id,
                status_code=503,
            )
            raise HTTPException(status_code=503, detail="challenge_store_unavailable")

        access_token, expires_at = _issue_signaling_access_token(
            nickname=nickname,
            device_id=device_id,
            now_unix=now_unix,
        )
        observability.incr("auth.verify.ok")
        span.set_attribute("auth.result", "ok")
        log_event(
            level="INFO",
            event="auth.verify.succeeded",
            message="Auth verify completed",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="auth",
            reason_code="ok",
            nickname=nickname,
            device_id=device_id,
            status_code=200,
        )
        return AuthVerifyResponse(access_token=access_token, expires_at=expires_at)


@app.websocket("/ws/signaling/{nickname}")
async def signaling_ws(websocket: WebSocket, nickname: str) -> None:
    ws_request_id = _as_non_empty_string(websocket.headers.get("x-request-id")) or uuid.uuid4().hex
    set_request_context(
        request_id=ws_request_id,
        route=websocket.url.path,
        method="WS",
    )
    connect_context = extract_context(dict(websocket.headers))
    with start_span(
        "ws.connect",
        context=connect_context,
        attributes={"ws.nickname": nickname, "ws.path": websocket.url.path},
    ) as connect_span:
        if not nickname.startswith("@"):
            observability.incr("ws.connect.rejected.invalid_nickname")
            connect_span.set_attribute("ws.result", "rejected")
            with start_span(
                "ws.reject",
                attributes={"ws.nickname": nickname, "ws.reject_reason": "invalid_nickname"},
            ):
                log_event(
                    level="WARNING",
                    event="ws.connect.rejected",
                    message="WebSocket pre-connect rejected",
                    service=settings.app_name,
                    env="dev" if settings.debug else "prod",
                    component="ws",
                    reason_code="ws_rejected_preconnect",
                    ws_nickname=nickname,
                    ws_reason="invalid_nickname",
                )
                await websocket.close(code=1008, reason="Nickname must start with @")
            clear_request_context()
            return

        access_token = _as_non_empty_string(websocket.query_params.get("access_token"))
        if access_token is None:
            observability.incr("ws.connect.rejected.token_missing")
            connect_span.set_attribute("ws.result", "rejected")
            with start_span(
                "ws.reject",
                attributes={"ws.nickname": nickname, "ws.reject_reason": "token_missing"},
            ):
                log_event(
                    level="WARNING",
                    event="ws.connect.rejected",
                    message="WebSocket pre-connect rejected",
                    service=settings.app_name,
                    env="dev" if settings.debug else "prod",
                    component="ws",
                    reason_code="token_missing",
                    ws_nickname=nickname,
                    ws_reason="token_missing",
                )
                await websocket.close(code=1008, reason="token_missing")
            clear_request_context()
            return

        try:
            claims = _decode_signaling_access_token(access_token)
            token_device_id = _validate_signaling_token_claims(nickname=nickname, claims=claims)
            token_jti = _as_non_empty_string(claims.get("jti"))
        except ValueError as exc:
            reason = str(exc)
            observability.incr(f"ws.connect.rejected.{reason}")
            connect_span.set_attribute("ws.result", "rejected")
            with start_span(
                "ws.reject",
                attributes={"ws.nickname": nickname, "ws.reject_reason": reason},
            ):
                log_event(
                    level="WARNING",
                    event="ws.connect.rejected",
                    message="WebSocket pre-connect rejected",
                    service=settings.app_name,
                    env="dev" if settings.debug else "prod",
                    component="ws",
                    reason_code=reason,
                    ws_nickname=nickname,
                    ws_reason=reason,
                )
                await websocket.close(code=1008, reason=reason)
            clear_request_context()
            return

        await hub.connect(
            nickname,
            websocket,
            device_id=token_device_id,
            token_jti=token_jti,
        )
        observability.incr("ws.connect.accepted")
        connect_span.set_attribute("ws.result", "accepted")
        connect_span.set_attribute("ws.device_id", token_device_id)
        log_event(
            level="INFO",
            event="ws.connect.accepted",
            message="WebSocket signaling connection accepted",
            service=settings.app_name,
            env="dev" if settings.debug else "prod",
            component="ws",
            reason_code="ok",
            ws_nickname=nickname,
            ws_device_id=token_device_id,
        )

    try:
        with start_span("ws.session", attributes={"ws.nickname": nickname}):
            await websocket.send_json(
                {
                    "type": "system.connected",
                    "timestamp": utc_now_iso(),
                    "from_nickname": "server",
                    "to_nickname": nickname,
                }
            )
            queued_notices = await hub.pop_notices(nickname)
            for queued_notice in queued_notices:
                await websocket.send_json(queued_notice)

            while True:
                incoming = await websocket.receive_json()
                await hub.touch_presence(nickname)
                await _cleanup_expired_ringing_sessions()
                if not isinstance(incoming, dict):
                    await websocket.send_json(
                        _base_message(
                            message_type="call.error",
                            from_nickname="server",
                            to_nickname=nickname,
                            error="Invalid signaling message format",
                        )
                    )
                    continue

                message_type = _as_non_empty_string(incoming.get("type"))
                if message_type not in CLIENT_MESSAGE_TYPES:
                    await websocket.send_json(
                        _base_message(
                            message_type="call.error",
                            from_nickname="server",
                            to_nickname=nickname,
                            call_id=_as_non_empty_string(incoming.get("call_id")),
                            error="Unsupported signaling message type",
                        )
                    )
                    continue

                call_id = _as_non_empty_string(incoming.get("call_id"))
                from_device_id = _as_non_empty_string(incoming.get("from_device_id"))
                target_device_id = _as_non_empty_string(incoming.get("target_device_id"))
                payload = incoming.get("payload")

                if message_type == "system.ping":
                    await websocket.send_json(
                        _base_message(
                            message_type="system.pong",
                            from_nickname="server",
                            to_nickname=nickname,
                            payload={"pong": True},
                        )
                    )
                    continue

                if message_type == "call.invite":
                    to_nickname = _as_non_empty_string(incoming.get("to_nickname"))
                    if not call_id:
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                error="call_id is required for call.invite",
                            )
                        )
                        continue
                    if not to_nickname or not to_nickname.startswith("@"):
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error="Invalid callee nickname",
                            )
                        )
                        continue
                    if not hub.is_online(to_nickname):
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error=f"Target {to_nickname} is offline",
                            )
                        )
                        continue

                    created, reason = registry.create_invite(call_id, nickname, to_nickname)
                    if not created:
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error=reason or "Failed to create call session",
                            )
                        )
                        continue

                    await hub.send_to(
                        to_nickname,
                        _base_message(
                            message_type="call.invite",
                            from_nickname=nickname,
                            to_nickname=to_nickname,
                            call_id=call_id,
                            from_device_id=from_device_id,
                            target_device_id=target_device_id,
                            payload=payload if isinstance(payload, dict) else {},
                        ),
                    )
                    continue

                if not call_id:
                    await websocket.send_json(
                        _base_message(
                            message_type="call.error",
                            from_nickname="server",
                            to_nickname=nickname,
                            error=f"call_id is required for {message_type}",
                        )
                    )
                    continue

                session = registry.get(call_id)
                if session is None:
                    await websocket.send_json(
                        _base_message(
                            message_type="call.error",
                            from_nickname="server",
                            to_nickname=nickname,
                            call_id=call_id,
                            error="Unknown call_id",
                        )
                    )
                    continue

                if nickname not in {session.caller, session.callee}:
                    await websocket.send_json(
                        _base_message(
                            message_type="call.error",
                            from_nickname="server",
                            to_nickname=nickname,
                            call_id=call_id,
                            error="Sender is not a participant of this call",
                        )
                    )
                    continue

                peer_nickname = registry.peer_for(call_id, nickname)
                if not peer_nickname:
                    await websocket.send_json(
                        _base_message(
                            message_type="call.error",
                            from_nickname="server",
                            to_nickname=nickname,
                            call_id=call_id,
                            error="Failed to resolve call peer",
                        )
                    )
                    continue

                allowed_states = EVENT_ALLOWED_STATES.get(message_type)
                if allowed_states is not None and session.state not in allowed_states:
                    await websocket.send_json(
                        _base_message(
                            message_type="call.error",
                            from_nickname="server",
                            to_nickname=nickname,
                            call_id=call_id,
                            error=_state_transition_error_message(
                                event=message_type,
                                state=session.state,
                            ),
                            payload={
                                "reason_code": "invalid_state_transition",
                                "event": message_type,
                                "current_state": session.state,
                                "allowed_states": sorted(allowed_states),
                            },
                        )
                    )
                    continue

                if message_type == "call.ringing":
                    if nickname != session.callee:
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error="Only callee can emit call.ringing",
                            )
                        )
                        continue

                    await hub.send_to(
                        session.caller,
                        _base_message(
                            message_type="call.ringing",
                            from_nickname=nickname,
                            to_nickname=session.caller,
                            call_id=call_id,
                            from_device_id=from_device_id,
                            payload=payload if isinstance(payload, dict) else {},
                        ),
                    )
                    continue

                if message_type == "call.accept":
                    if nickname != session.callee:
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error="Only callee can accept the call",
                            )
                        )
                        continue

                    registry.set_state(call_id, "connecting")
                    await hub.send_to(
                        session.caller,
                        _base_message(
                            message_type="call.accept",
                            from_nickname=nickname,
                            to_nickname=session.caller,
                            call_id=call_id,
                            from_device_id=from_device_id,
                            payload=payload if isinstance(payload, dict) else {},
                        ),
                    )
                    continue

                if message_type == "call.reject":
                    if nickname != session.callee:
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error="Only callee can reject the call",
                            )
                        )
                        continue

                    await hub.send_to(
                        session.caller,
                        _base_message(
                            message_type="call.reject",
                            from_nickname=nickname,
                            to_nickname=session.caller,
                            call_id=call_id,
                            from_device_id=from_device_id,
                            payload=payload if isinstance(payload, dict) else {},
                        ),
                    )
                    registry.remove(call_id)
                    continue

                if message_type == "call.cancel":
                    if nickname != session.caller:
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error="Only caller can cancel the call",
                            )
                        )
                        continue

                    await hub.send_to(
                        session.callee,
                        _base_message(
                            message_type="call.cancel",
                            from_nickname=nickname,
                            to_nickname=session.callee,
                            call_id=call_id,
                            from_device_id=from_device_id,
                            payload=payload if isinstance(payload, dict) else {},
                        ),
                    )
                    registry.remove(call_id)
                    continue

                if message_type == "call.hangup":
                    await hub.send_to(
                        peer_nickname,
                        _base_message(
                            message_type="call.hangup",
                            from_nickname=nickname,
                            to_nickname=peer_nickname,
                            call_id=call_id,
                            from_device_id=from_device_id,
                            payload=payload if isinstance(payload, dict) else {},
                        ),
                    )
                    registry.remove(call_id)
                    continue

                if message_type in {
                    "webrtc.offer",
                    "webrtc.answer",
                    "webrtc.ice-candidate",
                    "webrtc.ice-restart",
                }:
                    if message_type == "webrtc.offer" and session.state == "connecting":
                        registry.set_state(call_id, "connecting")
                    if message_type == "webrtc.answer":
                        registry.set_state(call_id, "connected")

                    forwarded = await hub.send_to(
                        peer_nickname,
                        _base_message(
                            message_type=message_type,
                            from_nickname=nickname,
                            to_nickname=peer_nickname,
                            call_id=call_id,
                            from_device_id=from_device_id,
                            target_device_id=target_device_id,
                            payload=payload if isinstance(payload, dict) else {},
                        ),
                    )

                    if not forwarded:
                        await websocket.send_json(
                            _base_message(
                                message_type="call.error",
                                from_nickname="server",
                                to_nickname=nickname,
                                call_id=call_id,
                                error=f"Peer {peer_nickname} is offline",
                            )
                        )
                        registry.remove(call_id)
                    continue

    except WebSocketDisconnect:
        observability.incr("ws.disconnect")
        with start_span("ws.disconnect", attributes={"ws.nickname": nickname}):
            log_event(
                level="INFO",
                event="ws.disconnect",
                message="WebSocket signaling disconnected",
                service=settings.app_name,
                env="dev" if settings.debug else "prod",
                component="ws",
                reason_code="peer_disconnected",
                ws_nickname=nickname,
            )
            while True:
                session = registry.get_for_participant(nickname)
                if session is None:
                    break

                peer_nickname = registry.peer_for(session.call_id, nickname)
                registry.remove(session.call_id)
                if peer_nickname:
                    await hub.send_to(
                        peer_nickname,
                        _base_message(
                            message_type="call.hangup",
                            from_nickname=nickname,
                            to_nickname=peer_nickname,
                            call_id=session.call_id,
                            payload={"reason": "peer_disconnected"},
                        ),
                    )
    finally:
        hub.disconnect(nickname)
        clear_request_context()

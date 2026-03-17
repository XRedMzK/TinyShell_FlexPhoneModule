from __future__ import annotations

import asyncio
import base64
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import redis
import websockets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from redis.exceptions import ResponseError


ROOT = Path(__file__).resolve().parents[1]
PYTHON_BIN = ROOT / ".venv_tmpcheck" / "bin" / "python"
if not PYTHON_BIN.exists():
    PYTHON_BIN = Path(sys.executable)

REQUEST_TIMEOUT_SECONDS = 5
HEALTH_TIMEOUT_SECONDS = 30
REDIS_TIMEOUT_SECONDS = 20


class DurableSignalingSmokeError(RuntimeError):
    pass


class _ApplyTracker:
    def __init__(self) -> None:
        self.applied_event_ids: set[str] = set()
        self.apply_count_by_event_id: dict[str, int] = {}
        self.dedup_hits = 0

    def apply(self, event_id: str) -> str:
        if event_id in self.applied_event_ids:
            self.dedup_hits += 1
            return "dedup_hit"
        self.applied_event_ids.add(event_id)
        self.apply_count_by_event_id[event_id] = self.apply_count_by_event_id.get(event_id, 0) + 1
        return "applied"


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _pick_free_port_from_candidates(candidates: range) -> int:
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise DurableSignalingSmokeError("No free port available in candidate range")


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )
    if check and completed.returncode != 0:
        raise DurableSignalingSmokeError(
            "Command failed: "
            + " ".join(cmd)
            + f"\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def _wait_redis_ready(redis_port: int, timeout_seconds: int = REDIS_TIMEOUT_SECONDS) -> redis.Redis:
    client = redis.Redis(host="127.0.0.1", port=redis_port, decode_responses=True)
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            if client.ping():
                return client
        except Exception as exc:  # pragma: no cover - runtime smoke diagnostic
            last_error = exc
        time.sleep(0.25)
    raise DurableSignalingSmokeError(f"Redis did not become ready on port {redis_port}: {last_error}")


def _wait_redis_url_ready(redis_url: str, timeout_seconds: int = REDIS_TIMEOUT_SECONDS) -> redis.Redis:
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            if client.ping():
                return client
        except Exception as exc:  # pragma: no cover - runtime smoke diagnostic
            last_error = exc
        time.sleep(0.25)
    raise DurableSignalingSmokeError(f"Redis did not become ready for URL {redis_url}: {last_error}")


def _wait_http_status(url: str, expected_status: int, timeout_seconds: int = HEALTH_TIMEOUT_SECONDS) -> httpx.Response:
    deadline = time.time() + timeout_seconds
    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == expected_status:
                return response
        except Exception as exc:  # pragma: no cover - runtime smoke diagnostic
            last_exc = exc
        time.sleep(0.3)
    raise DurableSignalingSmokeError(
        f"Timed out waiting for {url} status={expected_status}; last_exc={last_exc}"
    )


def _generate_identity() -> tuple[ec.EllipticCurvePrivateKey, str, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_key_spki_base64 = base64.b64encode(public_der).decode("ascii")
    device_id = secrets.token_hex(32)
    return private_key, public_key_spki_base64, device_id


def _sign_canonical_payload(private_key: ec.EllipticCurvePrivateKey, canonical_payload: str) -> str:
    signature = private_key.sign(canonical_payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")


def _register_and_auth(
    *,
    base_url: str,
    nickname: str,
    private_key: ec.EllipticCurvePrivateKey,
    public_key_spki_base64: str,
    device_id: str,
) -> str:
    register_response = httpx.post(
        f"{base_url}/devices/register",
        json={
            "nickname": nickname,
            "device_id": device_id,
            "public_key_spki_base64": public_key_spki_base64,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if register_response.status_code != 200:
        raise DurableSignalingSmokeError(
            f"Device register failed for {nickname}: {register_response.status_code} {register_response.text}"
        )

    challenge_response = httpx.post(
        f"{base_url}/auth/challenge",
        json={"nickname": nickname, "device_id": device_id},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if challenge_response.status_code != 200:
        raise DurableSignalingSmokeError(
            f"Auth challenge failed for {nickname}: {challenge_response.status_code} {challenge_response.text}"
        )
    challenge_payload = challenge_response.json()
    signature_b64url = _sign_canonical_payload(private_key, challenge_payload["canonical_payload"])

    verify_response = httpx.post(
        f"{base_url}/auth/verify",
        json={
            "challenge_id": challenge_payload["challenge_id"],
            "nickname": nickname,
            "device_id": device_id,
            "signature": signature_b64url,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if verify_response.status_code != 200:
        raise DurableSignalingSmokeError(
            f"Auth verify failed for {nickname}: {verify_response.status_code} {verify_response.text}"
        )
    token = verify_response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise DurableSignalingSmokeError(f"Auth verify returned invalid token for {nickname}")
    return token


async def _ws_connect(base_ws_url: str, nickname: str, access_token: str):
    ws = await websockets.connect(f"{base_ws_url}/{nickname}?access_token={access_token}", open_timeout=5, close_timeout=2)
    raw = await asyncio.wait_for(ws.recv(), timeout=5)
    message = json.loads(raw)
    if message.get("type") != "system.connected":
        raise DurableSignalingSmokeError(f"{nickname}: expected system.connected, got {message}")
    return ws


async def _recv_until(
    ws,
    *,
    predicate,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        remaining = max(0.1, deadline - time.time())
        raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
        message = json.loads(raw)
        if predicate(message):
            return message
    raise DurableSignalingSmokeError("Timed out waiting for expected websocket message")


def _stream_extract_entries(stream_response: Any) -> list[tuple[str, dict[str, str]]]:
    if not stream_response:
        return []
    entries: list[tuple[str, dict[str, str]]] = []
    for _stream_name, items in stream_response:
        for entry_id, fields in items:
            entries.append((entry_id, fields))
    return entries


def _find_entry_by_event_id(entries: list[tuple[str, dict[str, str]]], event_id: str) -> tuple[str, dict[str, str]] | None:
    for entry_id, fields in entries:
        if fields.get("event_id") == event_id:
            return entry_id, fields
    return None


def _xpending_count(client: redis.Redis, stream_key: str, group_name: str) -> int:
    pending = client.xpending(stream_key, group_name)
    if isinstance(pending, dict):
        return int(pending.get("pending", 0))
    if isinstance(pending, (list, tuple)) and pending:
        return int(pending[0])
    return 0


def _xautoclaim_entries(result: Any) -> list[tuple[str, dict[str, str]]]:
    if not isinstance(result, (list, tuple)):
        return []
    if len(result) == 3:
        _, entries, _ = result
        return entries
    if len(result) == 2:
        _, entries = result
        return entries
    return []


def _append_authoritative_event(
    client: redis.Redis,
    stream_key: str,
    *,
    event_id: str,
    event_type: str,
    scope_id: str,
    producer_instance_id: str,
) -> str:
    entry_id = client.xadd(
        stream_key,
        {
            "event_id": event_id,
            "event_type": event_type,
            "scope_id": scope_id,
            "producer_instance_id": producer_instance_id,
            "schema_version": "1",
            "issued_at": str(int(time.time())),
        },
    )
    return str(entry_id)


async def _run_smoke_flow(
    *,
    base_url: str,
    base_ws_url: str,
    redis_client: redis.Redis,
    stream_key: str,
    group_name: str,
    producer_instance_id: str,
) -> dict[str, Any]:
    identity_a = _generate_identity()
    identity_b = _generate_identity()

    nickname_a = "@durable_a"
    nickname_b = "@durable_b"

    token_a = _register_and_auth(
        base_url=base_url,
        nickname=nickname_a,
        private_key=identity_a[0],
        public_key_spki_base64=identity_a[1],
        device_id=identity_a[2],
    )
    token_b = _register_and_auth(
        base_url=base_url,
        nickname=nickname_b,
        private_key=identity_b[0],
        public_key_spki_base64=identity_b[1],
        device_id=identity_b[2],
    )

    ws_a = await _ws_connect(base_ws_url, nickname_a, token_a)
    ws_b = await _ws_connect(base_ws_url, nickname_b, token_b)

    tracker = _ApplyTracker()
    proof: dict[str, Any] = {
        "stream_key": stream_key,
        "consumer_group": group_name,
        "scenario_a": {},
        "scenario_b": {},
        "scenario_c": {},
        "scenario_d": {},
    }

    try:
        # A) durable append + live delivery
        call_id_a = f"call-{uuid.uuid4().hex[:10]}"
        event_id_a = f"evt-{uuid.uuid4().hex}"
        stream_entry_id_a = _append_authoritative_event(
            redis_client,
            stream_key,
            event_id=event_id_a,
            event_type="negotiation.offer-created",
            scope_id=call_id_a,
            producer_instance_id=producer_instance_id,
        )

        await ws_a.send(
            json.dumps(
                {
                    "type": "call.invite",
                    "to_nickname": nickname_b,
                    "call_id": call_id_a,
                    "from_device_id": identity_a[2],
                    "target_device_id": identity_b[2],
                    "payload": {"event_id": event_id_a, "stream_entry_id": stream_entry_id_a},
                }
            )
        )

        invite_message = await _recv_until(
            ws_b,
            predicate=lambda m: m.get("type") == "call.invite" and m.get("call_id") == call_id_a,
        )
        invite_payload = invite_message.get("payload", {})
        if invite_payload.get("event_id") != event_id_a:
            raise DurableSignalingSmokeError("Scenario A: live payload event_id mismatch")

        group_entries = _stream_extract_entries(
            redis_client.xreadgroup(
                group_name,
                "consumer-b-live",
                {stream_key: ">"},
                count=20,
                block=2000,
            )
        )
        matched = _find_entry_by_event_id(group_entries, event_id_a)
        if matched is None:
            raise DurableSignalingSmokeError("Scenario A: durable stream read did not include event_id_a")
        matched_entry_id, _ = matched
        redis_client.xack(stream_key, group_name, matched_entry_id)
        apply_result_a = tracker.apply(event_id_a)
        if apply_result_a != "applied":
            raise DurableSignalingSmokeError("Scenario A: first apply must be applied")

        # Clean up call session to avoid stale ringing state.
        await ws_a.send(
            json.dumps(
                {
                    "type": "call.cancel",
                    "call_id": call_id_a,
                    "from_device_id": identity_a[2],
                    "payload": {"reason": "sandbox_cleanup"},
                }
            )
        )
        await _recv_until(
            ws_b,
            predicate=lambda m: m.get("type") == "call.cancel" and m.get("call_id") == call_id_a,
        )

        proof["scenario_a"] = {
            "status": "PASS",
            "event_id": event_id_a,
            "stream_entry_id": stream_entry_id_a,
            "live_delivery": "received_once",
            "durable_read_ack": "ok",
            "apply_result": apply_result_a,
        }

        # B) disconnect before live delivery, then replay.
        await ws_b.close()
        call_id_b = f"call-{uuid.uuid4().hex[:10]}"
        event_id_b = f"evt-{uuid.uuid4().hex}"
        stream_entry_id_b = _append_authoritative_event(
            redis_client,
            stream_key,
            event_id=event_id_b,
            event_type="negotiation.answer-committed",
            scope_id=call_id_b,
            producer_instance_id=producer_instance_id,
        )

        await ws_a.send(
            json.dumps(
                {
                    "type": "call.invite",
                    "to_nickname": nickname_b,
                    "call_id": call_id_b,
                    "from_device_id": identity_a[2],
                    "target_device_id": identity_b[2],
                    "payload": {"event_id": event_id_b, "stream_entry_id": stream_entry_id_b},
                }
            )
        )
        await _recv_until(
            ws_a,
            predicate=lambda m: m.get("type") == "call.error"
            and m.get("call_id") == call_id_b
            and "offline" in str(m.get("error", "")).lower(),
        )

        ws_b = await _ws_connect(base_ws_url, nickname_b, token_b)
        replay_entries = _stream_extract_entries(
            redis_client.xreadgroup(
                group_name,
                "consumer-b-replay",
                {stream_key: ">"},
                count=20,
                block=2000,
            )
        )
        replay_match = _find_entry_by_event_id(replay_entries, event_id_b)
        if replay_match is None:
            raise DurableSignalingSmokeError("Scenario B: replay read did not include event_id_b")
        replay_entry_id, _ = replay_match
        redis_client.xack(stream_key, group_name, replay_entry_id)
        apply_result_b = tracker.apply(event_id_b)
        if apply_result_b != "applied":
            raise DurableSignalingSmokeError("Scenario B: replay apply must be applied")

        proof["scenario_b"] = {
            "status": "PASS",
            "event_id": event_id_b,
            "stream_entry_id": stream_entry_id_b,
            "live_fanout": "missed_due_to_disconnect",
            "replay_delivery": "received_after_reconnect",
            "apply_result": apply_result_b,
        }

        # C) read without ack -> pending recovery via consumer restart.
        call_id_c = f"call-{uuid.uuid4().hex[:10]}"
        event_id_c = f"evt-{uuid.uuid4().hex}"
        stream_entry_id_c = _append_authoritative_event(
            redis_client,
            stream_key,
            event_id=event_id_c,
            event_type="session.authoritative-state-changed",
            scope_id=call_id_c,
            producer_instance_id=producer_instance_id,
        )
        pre_pending = _xpending_count(redis_client, stream_key, group_name)

        crash_entries = _stream_extract_entries(
            redis_client.xreadgroup(
                group_name,
                "consumer-crash-before-ack",
                {stream_key: ">"},
                count=5,
                block=2000,
            )
        )
        crash_match = _find_entry_by_event_id(crash_entries, event_id_c)
        if crash_match is None:
            raise DurableSignalingSmokeError("Scenario C: initial consumer read did not include event_id_c")
        crash_entry_id, _ = crash_match

        mid_pending = _xpending_count(redis_client, stream_key, group_name)
        if mid_pending <= pre_pending:
            raise DurableSignalingSmokeError("Scenario C: pending count did not increase after read-without-ack")

        claimed_result = redis_client.xautoclaim(
            stream_key,
            group_name,
            "consumer-recovery-after-crash",
            min_idle_time=0,
            start_id="0-0",
            count=10,
        )
        claimed_entries = _xautoclaim_entries(claimed_result)
        claimed_match = _find_entry_by_event_id(claimed_entries, event_id_c)
        if claimed_match is None:
            raise DurableSignalingSmokeError("Scenario C: recovery consumer did not claim pending event_id_c")
        claimed_entry_id, _ = claimed_match
        redis_client.xack(stream_key, group_name, claimed_entry_id)
        post_pending = _xpending_count(redis_client, stream_key, group_name)
        if post_pending >= mid_pending:
            raise DurableSignalingSmokeError("Scenario C: pending count did not decrease after ack")
        if claimed_entry_id != crash_entry_id:
            raise DurableSignalingSmokeError("Scenario C: claimed entry id does not match originally read entry id")

        apply_result_c = tracker.apply(event_id_c)
        if apply_result_c != "applied":
            raise DurableSignalingSmokeError("Scenario C: first apply of recovered event must be applied")

        proof["scenario_c"] = {
            "status": "PASS",
            "event_id": event_id_c,
            "stream_entry_id": stream_entry_id_c,
            "pending_before": pre_pending,
            "pending_after_read_without_ack": mid_pending,
            "pending_after_recovery_ack": post_pending,
            "apply_result": apply_result_c,
        }

        # D) duplicate delivery attempt -> idempotent apply.
        duplicate_entry_id = _append_authoritative_event(
            redis_client,
            stream_key,
            event_id=event_id_b,
            event_type="negotiation.answer-committed",
            scope_id=call_id_b,
            producer_instance_id=producer_instance_id,
        )
        duplicate_entries = _stream_extract_entries(
            redis_client.xreadgroup(
                group_name,
                "consumer-dedup-check",
                {stream_key: ">"},
                count=10,
                block=2000,
            )
        )
        duplicate_match = _find_entry_by_event_id(duplicate_entries, event_id_b)
        if duplicate_match is None:
            raise DurableSignalingSmokeError("Scenario D: duplicate delivery event was not read from durable stream")
        duplicate_read_entry_id, _ = duplicate_match
        redis_client.xack(stream_key, group_name, duplicate_read_entry_id)

        apply_count_before = tracker.apply_count_by_event_id.get(event_id_b, 0)
        apply_result_d = tracker.apply(event_id_b)
        apply_count_after = tracker.apply_count_by_event_id.get(event_id_b, 0)
        if apply_result_d != "dedup_hit":
            raise DurableSignalingSmokeError("Scenario D: duplicate apply must be dedup_hit")
        if apply_count_after != apply_count_before:
            raise DurableSignalingSmokeError("Scenario D: duplicate apply changed apply_count")

        proof["scenario_d"] = {
            "status": "PASS",
            "event_id": event_id_b,
            "duplicate_stream_entry_id": duplicate_entry_id,
            "apply_result": apply_result_d,
            "apply_count_before": apply_count_before,
            "apply_count_after": apply_count_after,
            "dedup_hits": tracker.dedup_hits,
        }

        proof["summary"] = {
            "status": "PASS",
            "applied_event_ids": sorted(tracker.applied_event_ids),
            "apply_count_by_event_id": tracker.apply_count_by_event_id,
            "dedup_hits": tracker.dedup_hits,
        }
        return proof

    finally:
        try:
            await ws_a.close()
        except Exception:
            pass
        try:
            await ws_b.close()
        except Exception:
            pass


def run_durable_signaling_sandbox_smoke(*, redis_url: str | None = None) -> int:
    if not PYTHON_BIN.exists():
        raise DurableSignalingSmokeError(f"Python runtime not found: {PYTHON_BIN}")

    server_port = _pick_free_port_from_candidates(range(18100, 18200))
    redis_port = _pick_free_port_from_candidates(range(26379, 26479))
    redis_container = f"flexphone-durable-smoke-redis-{uuid.uuid4().hex[:8]}"
    stream_key = f"signaling:durable:smoke:{uuid.uuid4().hex}"
    group_name = "durable-smoke-group"
    producer_instance_id = f"durable-smoke-{uuid.uuid4().hex[:8]}"
    docker_managed_redis = redis_url is None

    if redis_url is None:
        # In WSL + Docker Desktop setups, random high ephemeral host ports may fail to expose.
        # Use stable low ranges for sandbox compatibility.
        redis_url = f"redis://127.0.0.1:{redis_port}/0"

    backend_log_file = tempfile.NamedTemporaryFile(
        prefix="flexphone-durable-smoke-backend-",
        suffix=".log",
        delete=False,
    )
    backend_log_path = Path(backend_log_file.name)
    backend_log_file.close()

    backend_process: subprocess.Popen[str] | None = None

    try:
        if docker_managed_redis:
            _run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-d",
                    "--name",
                    redis_container,
                    "-p",
                    f"{redis_port}:6379",
                    "redis:7-alpine",
                ],
                cwd=ROOT,
            )
            redis_client = _wait_redis_ready(redis_port)
        else:
            parsed = urlparse(redis_url)
            if parsed.scheme != "redis":
                raise DurableSignalingSmokeError(f"Unsupported redis URL scheme for simulation: {redis_url}")
            redis_client = _wait_redis_url_ready(redis_url)

        try:
            redis_client.xgroup_create(stream_key, group_name, id="$", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

        backend_env = os.environ.copy()
        backend_env.update(
            {
                "FLEXPHONE_AUTH_CHALLENGE_REDIS_URL": redis_url,
                "FLEXPHONE_SIGNALING_REDIS_URL": redis_url,
                "FLEXPHONE_AUTH_JWT_SECRET": "durable-smoke-auth-secret-32-bytes-minimum",
                "FLEXPHONE_OTEL_EXPORTER": "none",
                "FLEXPHONE_SIGNALING_INSTANCE_ID": producer_instance_id,
            }
        )

        with backend_log_path.open("w", encoding="utf-8") as log_handle:
            backend_process = subprocess.Popen(
                [
                    str(PYTHON_BIN),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(server_port),
                ],
                cwd=str(ROOT),
                env=backend_env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )

        base_url = f"http://127.0.0.1:{server_port}"
        _wait_http_status(f"{base_url}/health", 200)
        _wait_http_status(f"{base_url}/ready", 200)

        proof = asyncio.run(
            _run_smoke_flow(
                base_url=base_url,
                base_ws_url=f"ws://127.0.0.1:{server_port}/ws/signaling",
                redis_client=redis_client,
                stream_key=stream_key,
                group_name=group_name,
                producer_instance_id=producer_instance_id,
            )
        )

        print("Durable signaling sandbox smoke proof:")
        print(json.dumps(proof, ensure_ascii=True, sort_keys=True, indent=2))
        print("Durable signaling sandbox smoke: OK")
        return 0

    finally:
        if backend_process is not None:
            backend_process.send_signal(signal.SIGTERM)
            try:
                backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        if docker_managed_redis:
            _run(["docker", "rm", "-f", redis_container], cwd=ROOT, check=False)
        if backend_log_path.exists():
            try:
                backend_log_path.unlink()
            except OSError:
                pass


def main() -> int:
    try:
        redis_url = os.getenv("FLEXPHONE_DURABLE_SMOKE_REDIS_URL")
        return run_durable_signaling_sandbox_smoke(redis_url=redis_url)
    except Exception as exc:  # pragma: no cover - runtime harness
        print(f"Durable signaling sandbox smoke: FAILED - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

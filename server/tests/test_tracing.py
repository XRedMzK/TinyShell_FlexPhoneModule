from __future__ import annotations

import contextlib
import time
import uuid

from fastapi.testclient import TestClient
import jwt
import pytest
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from app import main, tracing
from app.auth_challenge_store import InMemoryAuthChallengeStore
from app.calls import InMemoryCallRegistry
from app.config import Settings
from app.main import app, registered_devices, settings
from app.signaling import InMemorySignalingHub


class _RecordingSpan:
    def __init__(self, event: dict[str, object]) -> None:
        self._event = event

    def set_attribute(self, key: str, value: object) -> None:
        attributes = self._event.setdefault("attributes", {})
        assert isinstance(attributes, dict)
        attributes[str(key)] = value

    def record_exception(self, exc: BaseException) -> None:
        exceptions = self._event.setdefault("exceptions", [])
        assert isinstance(exceptions, list)
        exceptions.append(type(exc).__name__)


def _mint_token(*, nickname: str, device_id: str, ttl_seconds: int = 300) -> str:
    now_unix = int(time.time())
    claims = {
        "iss": settings.auth_jwt_issuer,
        "sub": f"{nickname}:{device_id}",
        "nickname": nickname,
        "device_id": device_id,
        "aud": settings.auth_jwt_audience,
        "iat": now_unix,
        "exp": now_unix + ttl_seconds,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(claims, settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


@pytest.fixture(autouse=True)
def reset_state(
    monkeypatch: pytest.MonkeyPatch,
) -> list[dict[str, object]]:
    recorded_spans: list[dict[str, object]] = []

    @contextlib.contextmanager
    def _record_span(
        name: str,
        *,
        attributes: dict[str, object] | None = None,
        context: object | None = None,
    ):
        del context
        event = {"name": name, "attributes": dict(attributes or {})}
        recorded_spans.append(event)
        yield _RecordingSpan(event)

    registered_devices.clear()
    monkeypatch.setattr(main, "auth_challenge_store", InMemoryAuthChallengeStore())
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    monkeypatch.setattr(main, "start_span", _record_span)
    monkeypatch.setattr(settings, "auth_clock_skew_seconds", 0)
    monkeypatch.setattr(settings, "auth_jwt_secret", "test-auth-secret-32-bytes-minimum-key")
    monkeypatch.setattr(settings, "auth_jwt_ttl_seconds", 300)
    monkeypatch.setattr(settings, "auth_jwt_issuer", "flexphone-backend")
    monkeypatch.setattr(settings, "auth_jwt_audience", "signaling")
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "otel_exporter", "none")
    yield recorded_spans
    registered_devices.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_tracing_span_coverage_for_auth_ws_and_reconcile(
    client: TestClient,
    reset_state: list[dict[str, object]],
) -> None:
    # auth challenge / verify coverage
    challenge_response = client.post(
        "/auth/challenge",
        json={"nickname": "@ghost", "device_id": "a" * 64},
    )
    assert challenge_response.status_code == 404

    verify_response = client.post(
        "/auth/verify",
        json={
            "challenge_id": str(uuid.uuid4()),
            "nickname": "@ghost",
            "device_id": "a" * 64,
            "signature": "ZmFrZV9zaWc",
        },
    )
    assert verify_response.status_code == 404

    # ws reject coverage
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/signaling/@ghost") as ws:
            ws.receive_json()

    # ws connect + disconnect coverage
    register_response = client.post(
        "/devices/register",
        json={
            "nickname": "@alice",
            "device_id": "a" * 64,
            "public_key_spki_base64": "ZmFrZV9wdWJsaWNfa2V5X3Nwa2lfYmFzZTY0",
        },
    )
    assert register_response.status_code == 200

    access_token = _mint_token(nickname="@alice", device_id="a" * 64)
    with client.websocket_connect(f"/ws/signaling/@alice?access_token={access_token}") as ws:
        connected = ws.receive_json()
        assert connected["type"] == "system.connected"

    span_names = [str(item.get("name")) for item in reset_state]
    for expected in (
        "reconcile.startup",
        "auth.challenge",
        "auth.verify",
        "ws.connect",
        "ws.reject",
        "ws.disconnect",
    ):
        assert expected in span_names


def test_otel_exporter_setting_validation() -> None:
    with pytest.raises(ValidationError):
        Settings(otel_exporter="invalid-exporter")


def test_configure_tracing_supports_none_and_console_exporters() -> None:
    tracing.configure_tracing(Settings(otel_exporter="none"))
    assert tracing.runtime.enabled is False
    assert tracing.runtime.exporter == "none"

    tracing.configure_tracing(Settings(otel_exporter="console"))
    if tracing.trace is None:
        assert tracing.runtime.enabled is False
        assert tracing.runtime.exporter == "none"
    else:
        assert tracing.runtime.enabled is True
        assert tracing.runtime.exporter == "console"
    tracing.shutdown_tracing()

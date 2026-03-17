from __future__ import annotations

import time
import uuid

from fastapi.testclient import TestClient
import jwt
import pytest
from starlette.websockets import WebSocketDisconnect

from app import main
from app.auth_challenge_store import InMemoryAuthChallengeStore
from app.calls import InMemoryCallRegistry
from app.main import app, registered_devices, settings
from app.observability import observability
from app.signaling import InMemorySignalingHub


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
def reset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    registered_devices.clear()
    observability.reset()
    monkeypatch.setattr(main, "auth_challenge_store", InMemoryAuthChallengeStore())
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    monkeypatch.setattr(settings, "auth_clock_skew_seconds", 0)
    monkeypatch.setattr(settings, "auth_jwt_secret", "test-auth-secret-32-bytes-minimum-key")
    monkeypatch.setattr(settings, "auth_jwt_ttl_seconds", 300)
    monkeypatch.setattr(settings, "auth_jwt_issuer", "flexphone-backend")
    monkeypatch.setattr(settings, "auth_jwt_audience", "signaling")
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256")
    yield
    registered_devices.clear()
    observability.reset()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_observability_snapshot_tracks_http_and_rejections(client: TestClient) -> None:
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.headers.get("X-Request-ID")

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

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/signaling/@ghost") as ws:
            ws.receive_json()
    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "token_missing"

    snapshot_response = client.get("/observability/snapshot")
    assert snapshot_response.status_code == 200
    assert snapshot_response.headers.get("X-Request-ID")
    counters = snapshot_response.json()["counters"]

    assert counters["health.ok"] >= 1
    assert counters["auth.challenge.rejected.device_not_registered"] >= 1
    assert counters["auth.verify.rejected.challenge_not_found"] >= 1
    assert counters["ws.connect.rejected.token_missing"] >= 1


def test_observability_snapshot_tracks_ws_accept_and_disconnect(client: TestClient) -> None:
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

    snapshot_response = client.get("/observability/snapshot")
    assert snapshot_response.status_code == 200
    counters = snapshot_response.json()["counters"]

    assert counters["ws.connect.accepted"] >= 1
    assert counters["ws.disconnect"] >= 1

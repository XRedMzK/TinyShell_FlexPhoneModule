from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.calls import InMemoryCallRegistry
from app.auth_challenge_store import InMemoryAuthChallengeStore
from app.signaling import InMemorySignalingHub
from app import main
from app.main import app, registered_devices


@pytest.fixture(autouse=True)
def reset_auth_challenge_state(monkeypatch: pytest.MonkeyPatch) -> None:
    registered_devices.clear()
    monkeypatch.setattr(main, "auth_challenge_store", InMemoryAuthChallengeStore())
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    yield
    registered_devices.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _register_device(client: TestClient, nickname: str = "@alice", device_id: str = "a" * 64) -> None:
    response = client.post(
        "/devices/register",
        json={
            "nickname": nickname,
            "device_id": device_id,
            "public_key_spki_base64": "ZmFrZV9wdWJsaWNfa2V5X3Nwa2lfYmFzZTY0",
        },
    )
    assert response.status_code == 200


def test_auth_challenge_success(client: TestClient) -> None:
    nickname = "@alice"
    device_id = "a" * 64
    _register_device(client, nickname=nickname, device_id=device_id)

    response = client.post(
        "/auth/challenge",
        json={"nickname": nickname, "device_id": device_id},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["nickname"] == nickname
    assert payload["device_id"] == device_id
    assert payload["algorithm"] == "ECDSA_P256_SHA256"
    assert payload["payload_version"] == "flexphone-auth-v1"

    assert payload["issued_at"] < payload["expires_at"]
    assert payload["expires_at"] - payload["issued_at"] == 60

    canonical_payload = payload["canonical_payload"]
    assert canonical_payload.startswith("flexphone-auth-v1\n")
    assert f"challenge_id={payload['challenge_id']}" in canonical_payload
    assert f"nickname={nickname}" in canonical_payload
    assert f"device_id={device_id}" in canonical_payload
    assert f"nonce={payload['nonce']}" in canonical_payload
    assert f"issued_at={payload['issued_at']}" in canonical_payload
    assert f"expires_at={payload['expires_at']}" in canonical_payload

    stored = main.auth_challenge_store.get(payload["challenge_id"])
    assert stored is not None
    assert stored.consumed is False


def test_auth_challenge_rejects_invalid_nickname(client: TestClient) -> None:
    response = client.post(
        "/auth/challenge",
        json={"nickname": "alice", "device_id": "a" * 64},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Nickname must start with @"


def test_auth_challenge_rejects_unregistered_nickname(client: TestClient) -> None:
    response = client.post(
        "/auth/challenge",
        json={"nickname": "@alice", "device_id": "a" * 64},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Device is not registered for this nickname"


def test_auth_challenge_rejects_wrong_device_for_registered_nickname(client: TestClient) -> None:
    _register_device(client, nickname="@alice", device_id="a" * 64)

    response = client.post(
        "/auth/challenge",
        json={"nickname": "@alice", "device_id": "b" * 64},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Device ID does not match nickname registration"

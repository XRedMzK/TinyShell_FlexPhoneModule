from __future__ import annotations

import base64
import time
import uuid

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
import jwt
import pytest

from app.calls import InMemoryCallRegistry
from app.auth_challenge_store import InMemoryAuthChallengeStore
from app.signaling import InMemorySignalingHub
from app import main
from app.main import app, registered_devices, settings


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _register_device(
    client: TestClient,
    *,
    nickname: str = "@alice",
    device_id: str = "a" * 64,
) -> ec.EllipticCurvePrivateKey:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key_spki = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    response = client.post(
        "/devices/register",
        json={
            "nickname": nickname,
            "device_id": device_id,
            "public_key_spki_base64": base64.b64encode(public_key_spki).decode("ascii"),
        },
    )
    assert response.status_code == 200
    return private_key


def _request_challenge(
    client: TestClient,
    *,
    nickname: str = "@alice",
    device_id: str = "a" * 64,
) -> dict[str, object]:
    response = client.post(
        "/auth/challenge",
        json={"nickname": nickname, "device_id": device_id},
    )
    assert response.status_code == 200
    return response.json()


def _sign_challenge_payload(private_key: ec.EllipticCurvePrivateKey, canonical_payload: str) -> str:
    signature = private_key.sign(canonical_payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return _b64url_encode(signature)


@pytest.fixture(autouse=True)
def reset_auth_verify_state(monkeypatch: pytest.MonkeyPatch) -> None:
    registered_devices.clear()
    monkeypatch.setattr(main, "auth_challenge_store", InMemoryAuthChallengeStore())
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    monkeypatch.setattr(settings, "auth_clock_skew_seconds", 0)
    monkeypatch.setattr(
        settings,
        "auth_jwt_secret",
        "test-auth-secret-32-bytes-minimum-key",
    )
    monkeypatch.setattr(settings, "auth_jwt_ttl_seconds", 300)
    monkeypatch.setattr(settings, "auth_jwt_issuer", "flexphone-backend")
    monkeypatch.setattr(settings, "auth_jwt_audience", "signaling")
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256")
    yield
    registered_devices.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_auth_verify_success_issues_access_token(client: TestClient) -> None:
    nickname = "@alice"
    device_id = "a" * 64
    private_key = _register_device(client, nickname=nickname, device_id=device_id)
    challenge = _request_challenge(client, nickname=nickname, device_id=device_id)

    signature = _sign_challenge_payload(private_key, str(challenge["canonical_payload"]))
    response = client.post(
        "/auth/verify",
        json={
            "challenge_id": challenge["challenge_id"],
            "nickname": nickname,
            "device_id": device_id,
            "signature": signature,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "Bearer"
    assert payload["expires_at"] > int(time.time())

    claims = jwt.decode(
        payload["access_token"],
        settings.auth_jwt_secret,
        algorithms=[settings.auth_jwt_algorithm],
        audience=settings.auth_jwt_audience,
        issuer=settings.auth_jwt_issuer,
    )
    assert claims["iss"] == settings.auth_jwt_issuer
    assert claims["sub"] == f"{nickname}:{device_id}"
    assert claims["nickname"] == nickname
    assert claims["device_id"] == device_id
    assert claims["aud"] == settings.auth_jwt_audience
    assert isinstance(claims["iat"], int)
    assert isinstance(claims["exp"], int)
    assert isinstance(claims["jti"], str)
    assert claims["exp"] == payload["expires_at"]

    challenge_record = main.auth_challenge_store.get(str(challenge["challenge_id"]))
    assert challenge_record is not None
    assert challenge_record.consumed is True
    assert challenge_record.consumed_at is not None


def test_auth_verify_rejects_challenge_not_found(client: TestClient) -> None:
    response = client.post(
        "/auth/verify",
        json={
            "challenge_id": str(uuid.uuid4()),
            "nickname": "@alice",
            "device_id": "a" * 64,
            "signature": _b64url_encode(b"placeholder"),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "challenge_not_found"


def test_auth_verify_rejects_expired_challenge(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nickname = "@alice"
    device_id = "a" * 64
    private_key = _register_device(client, nickname=nickname, device_id=device_id)
    challenge = _request_challenge(client, nickname=nickname, device_id=device_id)

    monkeypatch.setattr(
        main.time,
        "time",
        lambda: int(challenge["expires_at"]) + settings.auth_clock_skew_seconds + 1,
    )

    signature = _sign_challenge_payload(private_key, str(challenge["canonical_payload"]))
    response = client.post(
        "/auth/verify",
        json={
            "challenge_id": challenge["challenge_id"],
            "nickname": nickname,
            "device_id": device_id,
            "signature": signature,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "challenge_expired"


def test_auth_verify_rejects_consumed_challenge_replay(client: TestClient) -> None:
    nickname = "@alice"
    device_id = "a" * 64
    private_key = _register_device(client, nickname=nickname, device_id=device_id)
    challenge = _request_challenge(client, nickname=nickname, device_id=device_id)
    signature = _sign_challenge_payload(private_key, str(challenge["canonical_payload"]))

    first_response = client.post(
        "/auth/verify",
        json={
            "challenge_id": challenge["challenge_id"],
            "nickname": nickname,
            "device_id": device_id,
            "signature": signature,
        },
    )
    assert first_response.status_code == 200

    replay_response = client.post(
        "/auth/verify",
        json={
            "challenge_id": challenge["challenge_id"],
            "nickname": nickname,
            "device_id": device_id,
            "signature": signature,
        },
    )
    assert replay_response.status_code == 409
    assert replay_response.json()["detail"] == "challenge_consumed"


def test_auth_verify_rejects_wrong_nickname_or_device(client: TestClient) -> None:
    nickname = "@alice"
    device_id = "a" * 64
    private_key = _register_device(client, nickname=nickname, device_id=device_id)
    challenge = _request_challenge(client, nickname=nickname, device_id=device_id)
    signature = _sign_challenge_payload(private_key, str(challenge["canonical_payload"]))

    response = client.post(
        "/auth/verify",
        json={
            "challenge_id": challenge["challenge_id"],
            "nickname": "@bob",
            "device_id": device_id,
            "signature": signature,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "wrong_nickname_or_device"


def test_auth_verify_rejects_invalid_signature(client: TestClient) -> None:
    nickname = "@alice"
    device_id = "a" * 64
    _ = _register_device(client, nickname=nickname, device_id=device_id)
    challenge = _request_challenge(client, nickname=nickname, device_id=device_id)

    response = client.post(
        "/auth/verify",
        json={
            "challenge_id": challenge["challenge_id"],
            "nickname": nickname,
            "device_id": device_id,
            "signature": _b64url_encode(b"not-a-valid-ecdsa-signature"),
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_signature"


def test_auth_verify_rejects_device_not_registered(client: TestClient) -> None:
    nickname = "@alice"
    device_id = "a" * 64
    private_key = _register_device(client, nickname=nickname, device_id=device_id)
    challenge = _request_challenge(client, nickname=nickname, device_id=device_id)
    signature = _sign_challenge_payload(private_key, str(challenge["canonical_payload"]))

    registered_devices.clear()
    response = client.post(
        "/auth/verify",
        json={
            "challenge_id": challenge["challenge_id"],
            "nickname": nickname,
            "device_id": device_id,
            "signature": signature,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "device_not_registered"

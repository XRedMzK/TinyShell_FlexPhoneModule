from __future__ import annotations

import time
import uuid

from fastapi.testclient import TestClient
import jwt
import pytest
from starlette.websockets import WebSocketDisconnect

from app.calls import InMemoryCallRegistry
from app.signaling import InMemorySignalingHub
from app import main
from app.main import app, registered_devices, settings


def _receive_connected_message(ws) -> None:
    message = ws.receive_json()
    assert message["type"] == "system.connected"


def _register_signaling_device(nickname: str, device_id: str) -> None:
    registered_devices[nickname] = {
        "device_id": device_id,
        "public_key_spki_base64": "test-public-key",
    }


def _mint_signaling_token(
    *,
    nickname: str,
    device_id: str,
    ttl_seconds: int = 300,
    audience: str | None = None,
    issued_at: int | None = None,
) -> str:
    now_unix = int(time.time()) if issued_at is None else issued_at
    expires_at = now_unix + ttl_seconds
    claims = {
        "iss": settings.auth_jwt_issuer,
        "sub": f"{nickname}:{device_id}",
        "nickname": nickname,
        "device_id": device_id,
        "aud": settings.auth_jwt_audience if audience is None else audience,
        "iat": now_unix,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(claims, settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def _ws_path(nickname: str, access_token: str | None) -> str:
    if access_token is None:
        return f"/ws/signaling/{nickname}"
    return f"/ws/signaling/{nickname}?access_token={access_token}"


def _tamper_token_signature(token: str) -> str:
    header, payload, signature = token.split(".", maxsplit=2)
    # Append an extra base64url character so the signature bytes change deterministically.
    return f"{header}.{payload}.{signature}A"


def _simulate_runtime_restart() -> None:
    main.registry.clear()
    main.hub.clear()
    registered_devices.clear()


def _assert_ws_rejected(client: TestClient, path: str, expected_reason: str) -> None:
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(path) as ws:
            ws.receive_json()

    assert exc_info.value.code == 1008
    assert exc_info.value.reason == expected_reason


@pytest.fixture(autouse=True)
def reset_signaling_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    main.registry.clear()
    main.hub.clear()
    registered_devices.clear()
    monkeypatch.setattr(
        settings,
        "auth_jwt_secret",
        "test-auth-secret-32-bytes-minimum-key",
    )
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "auth_jwt_issuer", "flexphone-backend")
    monkeypatch.setattr(settings, "auth_jwt_audience", "signaling")
    monkeypatch.setattr(settings, "auth_clock_skew_seconds", 0)
    yield
    main.registry.clear()
    main.hub.clear()
    registered_devices.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_ws_without_token_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    _assert_ws_rejected(client, _ws_path("@alice", None), "token_missing")


def test_ws_with_invalid_token_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    _assert_ws_rejected(client, _ws_path("@alice", "not-a-jwt"), "token_invalid")


def test_ws_with_expired_token_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    expired_token = _mint_signaling_token(
        nickname="@alice",
        device_id="a" * 64,
        ttl_seconds=-1,
    )
    _assert_ws_rejected(client, _ws_path("@alice", expired_token), "token_expired")


def test_ws_with_wrong_audience_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    wrong_audience_token = _mint_signaling_token(
        nickname="@alice",
        device_id="a" * 64,
        audience="webrtc",
    )
    _assert_ws_rejected(
        client,
        _ws_path("@alice", wrong_audience_token),
        "token_wrong_audience",
    )


def test_token_for_other_nickname_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    token_for_bob = _mint_signaling_token(nickname="@bob", device_id="b" * 64)
    _assert_ws_rejected(client, _ws_path("@alice", token_for_bob), "token_wrong_nickname")


def test_token_for_other_device_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    token_with_other_device = _mint_signaling_token(nickname="@alice", device_id="b" * 64)
    _assert_ws_rejected(client, _ws_path("@alice", token_with_other_device), "token_wrong_device")


def test_tampered_token_signature_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    valid_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    tampered_token = _tamper_token_signature(valid_token)
    _assert_ws_rejected(client, _ws_path("@alice", tampered_token), "token_invalid")


def test_reconnect_with_expired_token_then_fresh_token_succeeds(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)

    expired_token = _mint_signaling_token(
        nickname="@alice",
        device_id="a" * 64,
        ttl_seconds=-1,
    )
    _assert_ws_rejected(client, _ws_path("@alice", expired_token), "token_expired")

    fresh_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64, ttl_seconds=300)
    with client.websocket_connect(_ws_path("@alice", fresh_token)) as ws_alice:
        _receive_connected_message(ws_alice)


def test_reconnect_with_valid_token_after_runtime_restart_succeeds(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    still_valid_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64, ttl_seconds=300)

    _simulate_runtime_restart()
    _register_signaling_device("@alice", "a" * 64)

    with client.websocket_connect(_ws_path("@alice", still_valid_token)) as ws_alice:
        _receive_connected_message(ws_alice)


def test_reconnect_with_expired_token_after_runtime_restart_rejected(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    expired_token = _mint_signaling_token(
        nickname="@alice",
        device_id="a" * 64,
        ttl_seconds=-1,
    )

    _simulate_runtime_restart()
    _register_signaling_device("@alice", "a" * 64)

    _assert_ws_rejected(client, _ws_path("@alice", expired_token), "token_expired")


def test_system_ping_returns_pong(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)

    with client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice:
        _receive_connected_message(ws_alice)

        ws_alice.send_json({"type": "system.ping"})
        response = ws_alice.receive_json()

        assert response["type"] == "system.pong"
        assert response["from_nickname"] == "server"
        assert response["to_nickname"] == "@alice"
        assert response["payload"] == {"pong": True}


def test_invite_and_accept_flow(client: TestClient) -> None:
    call_id = "call-invite-accept-1"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json(
            {
                "type": "call.invite",
                "call_id": call_id,
                "to_nickname": "@bob",
                "payload": {"mode": "audio"},
            }
        )

        invite = ws_bob.receive_json()
        assert invite["type"] == "call.invite"
        assert invite["call_id"] == call_id
        assert invite["from_nickname"] == "@alice"
        assert invite["to_nickname"] == "@bob"

        ws_bob.send_json({"type": "call.accept", "call_id": call_id})
        accepted = ws_alice.receive_json()
        assert accepted["type"] == "call.accept"
        assert accepted["call_id"] == call_id
        assert accepted["from_nickname"] == "@bob"
        assert accepted["to_nickname"] == "@alice"

        session = main.registry.get(call_id)
        assert session is not None
        assert session.state == "connecting"


def test_invite_and_reject_flow(client: TestClient) -> None:
    call_id = "call-invite-reject-1"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json(
            {
                "type": "call.invite",
                "call_id": call_id,
                "to_nickname": "@bob",
            }
        )
        _ = ws_bob.receive_json()

        ws_bob.send_json(
            {
                "type": "call.reject",
                "call_id": call_id,
                "payload": {"reason": "busy"},
            }
        )
        rejected = ws_alice.receive_json()
        assert rejected["type"] == "call.reject"
        assert rejected["call_id"] == call_id
        assert rejected["from_nickname"] == "@bob"
        assert rejected["to_nickname"] == "@alice"

        assert main.registry.get(call_id) is None


def test_invite_and_cancel_flow(client: TestClient) -> None:
    call_id = "call-invite-cancel-1"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json(
            {
                "type": "call.invite",
                "call_id": call_id,
                "to_nickname": "@bob",
            }
        )
        _ = ws_bob.receive_json()

        ws_alice.send_json(
            {
                "type": "call.cancel",
                "call_id": call_id,
                "payload": {"reason": "caller_canceled"},
            }
        )
        canceled = ws_bob.receive_json()
        assert canceled["type"] == "call.cancel"
        assert canceled["call_id"] == call_id
        assert canceled["from_nickname"] == "@alice"
        assert canceled["to_nickname"] == "@bob"

        assert main.registry.get(call_id) is None


def test_invite_accept_and_hangup_flow(client: TestClient) -> None:
    call_id = "call-hangup-1"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json(
            {
                "type": "call.invite",
                "call_id": call_id,
                "to_nickname": "@bob",
            }
        )
        _ = ws_bob.receive_json()

        ws_bob.send_json({"type": "call.accept", "call_id": call_id})
        _ = ws_alice.receive_json()

        ws_alice.send_json(
            {
                "type": "call.hangup",
                "call_id": call_id,
                "payload": {"reason": "local_hangup"},
            }
        )
        hung_up = ws_bob.receive_json()
        assert hung_up["type"] == "call.hangup"
        assert hung_up["call_id"] == call_id
        assert hung_up["from_nickname"] == "@alice"
        assert hung_up["to_nickname"] == "@bob"

        assert main.registry.get(call_id) is None


def test_ringing_cleanup_timeout_sends_call_cancel(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    call_id = "call-timeout-1"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json(
            {
                "type": "call.invite",
                "call_id": call_id,
                "to_nickname": "@bob",
            }
        )
        _ = ws_bob.receive_json()

        def fake_expire_ringing(max_age_seconds: int):
            del max_age_seconds
            removed = main.registry.remove(call_id)
            return [removed] if removed is not None else []

        monkeypatch.setattr(main.registry, "expire_ringing", fake_expire_ringing)

        ws_alice.send_json({"type": "system.ping"})

        alice_message_1 = ws_alice.receive_json()
        alice_message_2 = ws_alice.receive_json()
        bob_message = ws_bob.receive_json()

        alice_types = {alice_message_1["type"], alice_message_2["type"]}
        assert "call.cancel" in alice_types
        assert "system.pong" in alice_types
        assert bob_message["type"] == "call.cancel"
        assert bob_message["payload"]["reason"] == "invite_timeout"


def test_accept_without_invite_returns_unknown_call_error(client: TestClient) -> None:
    _register_signaling_device("@alice", "a" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)

    with client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice:
        _receive_connected_message(ws_alice)

        ws_alice.send_json({"type": "call.accept", "call_id": "missing-call"})
        error_message = ws_alice.receive_json()

        assert error_message["type"] == "call.error"
        assert error_message["error"] == "Unknown call_id"


def test_hangup_is_rejected_while_call_is_ringing(client: TestClient) -> None:
    call_id = "call-invalid-hangup-ringing"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json({"type": "call.invite", "call_id": call_id, "to_nickname": "@bob"})
        _ = ws_bob.receive_json()

        ws_alice.send_json({"type": "call.hangup", "call_id": call_id})
        error_message = ws_alice.receive_json()

        assert error_message["type"] == "call.error"
        assert "invalid_state_transition:call.hangup:state=ringing" in error_message["error"]
        assert error_message["payload"]["reason_code"] == "invalid_state_transition"
        assert main.registry.get(call_id) is not None


def test_cancel_is_rejected_after_call_is_connecting(client: TestClient) -> None:
    call_id = "call-invalid-cancel-connecting"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json({"type": "call.invite", "call_id": call_id, "to_nickname": "@bob"})
        _ = ws_bob.receive_json()

        ws_bob.send_json({"type": "call.accept", "call_id": call_id})
        _ = ws_alice.receive_json()

        ws_alice.send_json(
            {
                "type": "call.cancel",
                "call_id": call_id,
                "payload": {"reason": "late_cancel"},
            }
        )
        error_message = ws_alice.receive_json()
        assert error_message["type"] == "call.error"
        assert "invalid_state_transition:call.cancel:state=connecting" in error_message["error"]
        assert error_message["payload"]["reason_code"] == "invalid_state_transition"
        assert main.registry.get(call_id) is not None


def test_webrtc_offer_is_rejected_before_accept(client: TestClient) -> None:
    call_id = "call-invalid-offer-ringing"
    _register_signaling_device("@alice", "a" * 64)
    _register_signaling_device("@bob", "b" * 64)
    alice_token = _mint_signaling_token(nickname="@alice", device_id="a" * 64)
    bob_token = _mint_signaling_token(nickname="@bob", device_id="b" * 64)

    with (
        client.websocket_connect(_ws_path("@alice", alice_token)) as ws_alice,
        client.websocket_connect(_ws_path("@bob", bob_token)) as ws_bob,
    ):
        _receive_connected_message(ws_alice)
        _receive_connected_message(ws_bob)

        ws_alice.send_json({"type": "call.invite", "call_id": call_id, "to_nickname": "@bob"})
        _ = ws_bob.receive_json()

        ws_alice.send_json(
            {
                "type": "webrtc.offer",
                "call_id": call_id,
                "payload": {"sdp": {"type": "offer", "sdp": "dummy"}},
            }
        )
        error_message = ws_alice.receive_json()

        assert error_message["type"] == "call.error"
        assert "invalid_state_transition:webrtc.offer:state=ringing" in error_message["error"]
        assert error_message["payload"]["reason_code"] == "invalid_state_transition"

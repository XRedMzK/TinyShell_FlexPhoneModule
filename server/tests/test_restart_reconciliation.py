from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app import main
from app.calls import InMemoryCallRegistry
from app.signaling import InMemorySignalingHub


class _FakeWebSocket:
    async def accept(self) -> None:
        return

    async def send_json(self, message: dict) -> None:
        del message
        return


@pytest.fixture(autouse=True)
def reset_reconcile_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    yield
    main.registry.clear()
    main.hub.clear()


def test_reconcile_connected_session_queues_restart_hangup_notice() -> None:
    created, reason = main.registry.create_invite("call-restart-1", "@alice", "@bob")
    assert created is True
    assert reason is None
    main.registry.set_state("call-restart-1", "connected")

    asyncio.run(main._reconcile_sessions_after_restart())

    assert main.registry.get("call-restart-1") is None
    alice_notices = asyncio.run(main.hub.pop_notices("@alice"))
    bob_notices = asyncio.run(main.hub.pop_notices("@bob"))

    assert alice_notices
    assert bob_notices
    assert alice_notices[0]["type"] == "call.hangup"
    assert bob_notices[0]["type"] == "call.hangup"
    assert alice_notices[0]["payload"]["reason"] == "call_terminated_backend_restart"
    assert bob_notices[0]["payload"]["reason"] == "call_terminated_backend_restart"


def test_reconcile_stale_ringing_session_queues_cleanup_notice() -> None:
    created, reason = main.registry.create_invite("call-restart-2", "@alice", "@bob")
    assert created is True
    assert reason is None

    session = main.registry.get("call-restart-2")
    assert session is not None
    session.created_at = (datetime.now(UTC) - timedelta(seconds=120)).isoformat()

    asyncio.run(main._reconcile_sessions_after_restart())

    assert main.registry.get("call-restart-2") is None
    alice_notices = asyncio.run(main.hub.pop_notices("@alice"))
    bob_notices = asyncio.run(main.hub.pop_notices("@bob"))
    assert alice_notices[0]["type"] == "call.cancel"
    assert bob_notices[0]["type"] == "call.cancel"
    assert alice_notices[0]["payload"]["reason"] == "backend_restart_cleanup"
    assert bob_notices[0]["payload"]["reason"] == "backend_restart_cleanup"


def test_reconcile_keeps_fresh_ringing_session_when_both_participants_online() -> None:
    created, reason = main.registry.create_invite("call-restart-3", "@alice", "@bob")
    assert created is True
    assert reason is None

    async def _connect_both() -> None:
        await main.hub.connect("@alice", _FakeWebSocket(), device_id="a" * 64, token_jti="jti-a")
        await main.hub.connect("@bob", _FakeWebSocket(), device_id="b" * 64, token_jti="jti-b")

    asyncio.run(_connect_both())
    asyncio.run(main._reconcile_sessions_after_restart())

    session = main.registry.get("call-restart-3")
    assert session is not None
    assert session.state == "ringing"
    assert asyncio.run(main.hub.pop_notices("@alice")) == []
    assert asyncio.run(main.hub.pop_notices("@bob")) == []

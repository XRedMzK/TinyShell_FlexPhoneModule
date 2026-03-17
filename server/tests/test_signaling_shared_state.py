from __future__ import annotations

import asyncio
import time

import fakeredis

from app.calls import RedisCallRegistry
from app.signaling import RedisSignalingHub


class _FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.sent_messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent_messages.append(message)


def test_redis_call_registry_shared_state_roundtrip() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    registry = RedisCallRegistry(redis_client=redis_client, key_prefix="test:signaling:session")

    created, reason = registry.create_invite("call-1", "@alice", "@bob")
    assert created is True
    assert reason is None

    duplicate_created, duplicate_reason = registry.create_invite("call-1", "@alice", "@bob")
    assert duplicate_created is False
    assert duplicate_reason == "call_id already exists"

    session = registry.get("call-1")
    assert session is not None
    assert session.state == "ringing"
    assert session.revision == 1
    assert registry.is_busy("@alice") is True
    assert registry.is_busy("@bob") is True

    by_participant = registry.get_for_participant("@alice")
    assert by_participant is not None
    assert by_participant.call_id == "call-1"

    registry.set_state("call-1", "connecting")
    updated_session = registry.get("call-1")
    assert updated_session is not None
    assert updated_session.state == "connecting"
    assert updated_session.revision >= 2

    removed_session = registry.remove("call-1")
    assert removed_session is not None
    assert registry.get("call-1") is None
    assert registry.is_busy("@alice") is False
    assert registry.is_busy("@bob") is False


def test_redis_presence_connect_touch_disconnect_lifecycle() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    hub = RedisSignalingHub(
        redis_client=redis_client,
        instance_id="instance-a",
        presence_key_prefix="test:signaling:presence",
        pubsub_channel_prefix="test:signaling:fanout",
        presence_ttl_seconds=30,
    )

    async def _scenario() -> None:
        await hub.start()
        try:
            ws = _FakeWebSocket()
            await hub.connect("@alice", ws, device_id="a" * 64, token_jti="jti-1")
            assert ws.accepted is True
            assert hub.is_online("@alice") is True

            presence_key = "test:signaling:presence:@alice"
            first_snapshot = redis_client.hgetall(presence_key)
            assert first_snapshot["instance_id"] == "instance-a"
            first_seen = first_snapshot["last_seen_at"]

            time.sleep(1)
            await hub.touch_presence("@alice")
            second_snapshot = redis_client.hgetall(presence_key)
            assert int(second_snapshot["last_seen_at"]) >= int(first_seen)

            hub.disconnect("@alice")
            assert redis_client.exists(presence_key) == 0
            assert hub.is_online("@alice") is False
        finally:
            await hub.stop()

    asyncio.run(_scenario())


def test_cross_instance_fanout_and_rebind_prevents_stale_delivery() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    hub_a = RedisSignalingHub(
        redis_client=redis_client,
        instance_id="instance-a",
        presence_key_prefix="test:signaling:presence",
        pubsub_channel_prefix="test:signaling:fanout",
        presence_ttl_seconds=30,
    )
    hub_b = RedisSignalingHub(
        redis_client=redis_client,
        instance_id="instance-b",
        presence_key_prefix="test:signaling:presence",
        pubsub_channel_prefix="test:signaling:fanout",
        presence_ttl_seconds=30,
    )

    async def _scenario() -> None:
        await hub_a.start()
        await hub_b.start()
        try:
            stale_ws = _FakeWebSocket()
            fresh_ws = _FakeWebSocket()

            await hub_a.connect("@bob", stale_ws, device_id="b" * 64, token_jti="jti-stale")
            await hub_b.connect("@bob", fresh_ws, device_id="b" * 64, token_jti="jti-fresh")

            delivered = await hub_a.send_to("@bob", {"type": "call.invite", "call_id": "call-2"})
            assert delivered is True

            for _ in range(30):
                if fresh_ws.sent_messages:
                    break
                await asyncio.sleep(0.02)

            assert fresh_ws.sent_messages, "Expected remote instance to receive fan-out message"
            assert fresh_ws.sent_messages[0]["type"] == "call.invite"
            assert stale_ws.sent_messages == []
        finally:
            await hub_a.stop()
            await hub_b.stop()

    asyncio.run(_scenario())

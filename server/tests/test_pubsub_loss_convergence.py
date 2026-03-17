from __future__ import annotations

import asyncio
import time

import fakeredis

from app import main
from app.calls import RedisCallRegistry
from app.signaling import RedisSignalingHub


class _FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        del message
        return


def _presence_mapping(*, nickname: str, instance_id: str, connection_id: str, now_unix: int) -> dict[str, str]:
    return {
        "nickname": nickname,
        "instance_id": instance_id,
        "connection_id": connection_id,
        "device_id": "a" * 64,
        "token_jti": "jti",
        "connected_at": str(now_unix),
        "last_seen_at": str(now_unix),
    }


def test_missed_pubsub_fanout_still_converges_via_shared_state() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    registry = RedisCallRegistry(redis_client=redis_client, key_prefix="test:restart:session")
    hub = RedisSignalingHub(
        redis_client=redis_client,
        instance_id="instance-a",
        presence_key_prefix="test:restart:presence",
        pubsub_channel_prefix="test:restart:fanout",
        presence_ttl_seconds=30,
    )

    original_registry = main.registry
    original_hub = main.hub
    main.registry = registry
    main.hub = hub

    async def _scenario() -> None:
        await hub.start()
        try:
            created, reason = registry.create_invite("call-loss-1", "@alice", "@bob")
            assert created is True
            assert reason is None
            registry.set_state("call-loss-1", "connected")

            # Simulate stale ownership on another instance: publish target has no subscribers.
            now_unix = int(time.time())
            redis_client.hset(
                "test:restart:presence:@alice",
                mapping=_presence_mapping(
                    nickname="@alice",
                    instance_id="instance-b",
                    connection_id="conn-a",
                    now_unix=now_unix,
                ),
            )
            redis_client.hset(
                "test:restart:presence:@bob",
                mapping=_presence_mapping(
                    nickname="@bob",
                    instance_id="instance-b",
                    connection_id="conn-b",
                    now_unix=now_unix,
                ),
            )
            redis_client.expire("test:restart:presence:@alice", 30)
            redis_client.expire("test:restart:presence:@bob", 30)

            await main._reconcile_sessions_after_restart()

            assert registry.get("call-loss-1") is None
            assert redis_client.exists("test:restart:session:participant:@alice") == 0
            assert redis_client.exists("test:restart:session:participant:@bob") == 0

            # Reconnect to current instance and read queued notices.
            ws_alice = _FakeWebSocket()
            ws_bob = _FakeWebSocket()
            await hub.connect("@alice", ws_alice, device_id="a" * 64, token_jti="jti-a")
            await hub.connect("@bob", ws_bob, device_id="b" * 64, token_jti="jti-b")
            assert ws_alice.accepted is True
            assert ws_bob.accepted is True

            alice_notices = await hub.pop_notices("@alice")
            bob_notices = await hub.pop_notices("@bob")

            assert len(alice_notices) == 1
            assert len(bob_notices) == 1
            assert alice_notices[0]["type"] == "call.hangup"
            assert bob_notices[0]["type"] == "call.hangup"
            assert alice_notices[0]["payload"]["reason"] == "call_terminated_backend_restart"
            assert bob_notices[0]["payload"]["reason"] == "call_terminated_backend_restart"

            # Canonical shared state converged: no stale active session keys.
            assert list(redis_client.scan_iter("test:restart:session:session:*")) == []
            assert list(redis_client.scan_iter("test:restart:session:participant:*")) == []
        finally:
            await hub.stop()

    try:
        asyncio.run(_scenario())
    finally:
        main.registry = original_registry
        main.hub = original_hub

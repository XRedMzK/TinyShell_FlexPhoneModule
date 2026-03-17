from __future__ import annotations

import time
import uuid

import fakeredis

from app.auth_challenge_store import AuthChallengeRecord, RedisAuthChallengeStore


def _build_store(redis_client: fakeredis.FakeRedis) -> RedisAuthChallengeStore:
    return RedisAuthChallengeStore(
        redis_client=redis_client,
        key_prefix="test:auth:challenge",
    )


def _build_record(*, challenge_id: str, now_unix: int, expires_at: int) -> AuthChallengeRecord:
    return AuthChallengeRecord(
        challenge_id=challenge_id,
        nickname="@alice",
        device_id="a" * 64,
        nonce="nonce-value",
        issued_at=now_unix,
        expires_at=expires_at,
    )


def test_challenge_survives_store_restart_before_ttl_expiry() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    now_unix = int(time.time())
    challenge_id = f"challenge-{uuid.uuid4()}"

    first_store = _build_store(redis_client)
    first_store.create(
        _build_record(
            challenge_id=challenge_id,
            now_unix=now_unix,
            expires_at=now_unix + 30,
        ),
        clock_skew_seconds=0,
        retention_seconds=60,
    )

    second_store = _build_store(redis_client)
    loaded = second_store.get(challenge_id)

    assert loaded is not None
    assert loaded.challenge_id == challenge_id
    assert loaded.nickname == "@alice"
    assert loaded.device_id == "a" * 64
    assert loaded.consumed is False


def test_challenge_expires_across_store_restart_when_ttl_elapses() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    now_unix = int(time.time())
    challenge_id = f"challenge-{uuid.uuid4()}"

    first_store = _build_store(redis_client)
    first_store.create(
        _build_record(
            challenge_id=challenge_id,
            now_unix=now_unix,
            expires_at=now_unix + 1,
        ),
        clock_skew_seconds=0,
        retention_seconds=0,
    )

    time.sleep(2)

    second_store = _build_store(redis_client)
    assert second_store.get(challenge_id) is None

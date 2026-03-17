from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal, Protocol

from redis import Redis

ChallengeConsumeStatus = Literal["ok", "not_found", "expired", "consumed"]

_CONSUME_CHALLENGE_SCRIPT = """
local key = KEYS[1]
local now_unix = tonumber(ARGV[1])
local clock_skew_seconds = tonumber(ARGV[2])

if redis.call('EXISTS', key) == 0 then
  return "not_found"
end

local expires_at = tonumber(redis.call('HGET', key, 'expires_at') or "0")
if (expires_at + clock_skew_seconds) < now_unix then
  return "expired"
end

local consumed = redis.call('HGET', key, 'consumed')
if consumed == "1" then
  return "consumed"
end

redis.call('HSET', key, 'consumed', '1', 'consumed_at', tostring(now_unix))
return "ok"
"""


@dataclass(slots=True)
class AuthChallengeRecord:
    challenge_id: str
    nickname: str
    device_id: str
    nonce: str
    issued_at: int
    expires_at: int
    consumed: bool = False
    consumed_at: int | None = None


class AuthChallengeStore(Protocol):
    def create(
        self,
        record: AuthChallengeRecord,
        *,
        clock_skew_seconds: int,
        retention_seconds: int,
    ) -> None:
        ...

    def get(self, challenge_id: str) -> AuthChallengeRecord | None:
        ...

    def consume(
        self,
        challenge_id: str,
        *,
        now_unix: int,
        clock_skew_seconds: int,
    ) -> ChallengeConsumeStatus:
        ...


class RedisAuthChallengeStore:
    def __init__(self, redis_client: Redis, *, key_prefix: str) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix.strip(":")
        self._consume_challenge_script = self._redis.register_script(
            _CONSUME_CHALLENGE_SCRIPT
        )

    def _key(self, challenge_id: str) -> str:
        return f"{self._key_prefix}:{challenge_id}"

    def create(
        self,
        record: AuthChallengeRecord,
        *,
        clock_skew_seconds: int,
        retention_seconds: int,
    ) -> None:
        expires_at_redis = max(
            int(time.time()) + 1,
            record.expires_at + clock_skew_seconds + retention_seconds,
        )
        challenge_key = self._key(record.challenge_id)
        pipeline = self._redis.pipeline()
        pipeline.hset(
            challenge_key,
            mapping={
                "challenge_id": record.challenge_id,
                "nickname": record.nickname,
                "device_id": record.device_id,
                "nonce": record.nonce,
                "issued_at": str(record.issued_at),
                "expires_at": str(record.expires_at),
                "consumed": "1" if record.consumed else "0",
                "consumed_at": "" if record.consumed_at is None else str(record.consumed_at),
            },
        )
        pipeline.expireat(challenge_key, expires_at_redis)
        pipeline.execute()

    def get(self, challenge_id: str) -> AuthChallengeRecord | None:
        raw_record = self._redis.hgetall(self._key(challenge_id))
        if not raw_record:
            return None

        consumed_at_raw = raw_record.get("consumed_at")
        consumed_at = int(consumed_at_raw) if consumed_at_raw else None

        return AuthChallengeRecord(
            challenge_id=raw_record["challenge_id"],
            nickname=raw_record["nickname"],
            device_id=raw_record["device_id"],
            nonce=raw_record["nonce"],
            issued_at=int(raw_record["issued_at"]),
            expires_at=int(raw_record["expires_at"]),
            consumed=raw_record.get("consumed", "0") == "1",
            consumed_at=consumed_at,
        )

    def consume(
        self,
        challenge_id: str,
        *,
        now_unix: int,
        clock_skew_seconds: int,
    ) -> ChallengeConsumeStatus:
        result = self._consume_challenge_script(
            keys=[self._key(challenge_id)],
            args=[str(now_unix), str(clock_skew_seconds)],
        )
        if isinstance(result, bytes):
            result = result.decode("utf-8")

        if result not in {"ok", "not_found", "expired", "consumed"}:
            raise ValueError("Unexpected consume status from auth challenge store")
        return result


class InMemoryAuthChallengeStore:
    def __init__(self) -> None:
        self._records: dict[str, AuthChallengeRecord] = {}
        self._drop_after: dict[str, int] = {}

    def _cleanup(self, *, now_unix: int) -> None:
        stale_ids = [
            challenge_id
            for challenge_id, drop_after in self._drop_after.items()
            if drop_after <= now_unix
        ]
        for challenge_id in stale_ids:
            self._drop_after.pop(challenge_id, None)
            self._records.pop(challenge_id, None)

    def create(
        self,
        record: AuthChallengeRecord,
        *,
        clock_skew_seconds: int,
        retention_seconds: int,
    ) -> None:
        now_unix = int(time.time())
        self._cleanup(now_unix=now_unix)
        self._records[record.challenge_id] = AuthChallengeRecord(
            challenge_id=record.challenge_id,
            nickname=record.nickname,
            device_id=record.device_id,
            nonce=record.nonce,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            consumed=record.consumed,
            consumed_at=record.consumed_at,
        )
        self._drop_after[record.challenge_id] = (
            record.expires_at + clock_skew_seconds + retention_seconds
        )

    def get(self, challenge_id: str) -> AuthChallengeRecord | None:
        self._cleanup(now_unix=int(time.time()))
        record = self._records.get(challenge_id)
        if record is None:
            return None
        return AuthChallengeRecord(
            challenge_id=record.challenge_id,
            nickname=record.nickname,
            device_id=record.device_id,
            nonce=record.nonce,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            consumed=record.consumed,
            consumed_at=record.consumed_at,
        )

    def consume(
        self,
        challenge_id: str,
        *,
        now_unix: int,
        clock_skew_seconds: int,
    ) -> ChallengeConsumeStatus:
        self._cleanup(now_unix=now_unix)
        record = self._records.get(challenge_id)
        if record is None:
            return "not_found"
        if record.expires_at + clock_skew_seconds < now_unix:
            return "expired"
        if record.consumed:
            return "consumed"
        record.consumed = True
        record.consumed_at = now_unix
        return "ok"

    def clear(self) -> None:
        self._records.clear()
        self._drop_after.clear()

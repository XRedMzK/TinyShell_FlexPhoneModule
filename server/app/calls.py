from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from redis import Redis
from redis.exceptions import RedisError

from .config import get_settings

CallState = Literal["ringing", "connecting", "connected"]


@dataclass
class CallSession:
    call_id: str
    caller: str
    callee: str
    state: CallState
    created_at: str
    updated_at: str
    revision: int = 0


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class InMemoryCallRegistry:
    def __init__(self) -> None:
        self._by_call_id: dict[str, CallSession] = {}
        self._by_participant: dict[str, str] = {}

    def get(self, call_id: str) -> CallSession | None:
        return self._by_call_id.get(call_id)

    def get_for_participant(self, nickname: str) -> CallSession | None:
        call_id = self._by_participant.get(nickname)
        if not call_id:
            return None
        return self._by_call_id.get(call_id)

    def is_busy(self, nickname: str) -> bool:
        return nickname in self._by_participant

    def create_invite(self, call_id: str, caller: str, callee: str) -> tuple[bool, str | None]:
        if call_id in self._by_call_id:
            return False, "call_id already exists"
        if caller == callee:
            return False, "caller and callee must differ"
        if self.is_busy(caller):
            return False, "caller is busy"
        if self.is_busy(callee):
            return False, "callee is busy"

        now = utc_now_iso()
        session = CallSession(
            call_id=call_id,
            caller=caller,
            callee=callee,
            state="ringing",
            created_at=now,
            updated_at=now,
            revision=1,
        )
        self._by_call_id[call_id] = session
        self._by_participant[caller] = call_id
        self._by_participant[callee] = call_id
        return True, None

    def set_state(self, call_id: str, state: CallState) -> None:
        session = self._by_call_id.get(call_id)
        if session is None:
            return
        session.state = state
        session.updated_at = utc_now_iso()
        session.revision += 1

    def peer_for(self, call_id: str, nickname: str) -> str | None:
        session = self._by_call_id.get(call_id)
        if session is None:
            return None
        if session.caller == nickname:
            return session.callee
        if session.callee == nickname:
            return session.caller
        return None

    def remove(self, call_id: str) -> CallSession | None:
        session = self._by_call_id.pop(call_id, None)
        if session is None:
            return None

        self._by_participant.pop(session.caller, None)
        self._by_participant.pop(session.callee, None)
        return session

    def expire_ringing(self, max_age_seconds: int) -> list[CallSession]:
        now = datetime.now(UTC)
        expired_ids: list[str] = []
        for call_id, session in self._by_call_id.items():
            if session.state != "ringing":
                continue

            created_at = datetime.fromisoformat(session.created_at)
            age_seconds = (now - created_at).total_seconds()
            if age_seconds > max_age_seconds:
                expired_ids.append(call_id)

        expired: list[CallSession] = []
        for call_id in expired_ids:
            removed = self.remove(call_id)
            if removed is not None:
                expired.append(removed)
        return expired

    def all_sessions(self) -> list[CallSession]:
        return list(self._by_call_id.values())

    def clear(self) -> None:
        self._by_call_id.clear()
        self._by_participant.clear()


class RedisCallRegistry:
    def __init__(self, redis_client: Redis, *, key_prefix: str) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix.strip(":")
        self._create_invite_script = self._redis.register_script(
            """
            local session_key = KEYS[1]
            local caller_key = KEYS[2]
            local callee_key = KEYS[3]
            local call_id = ARGV[1]
            local caller = ARGV[2]
            local callee = ARGV[3]
            local now_iso = ARGV[4]

            if redis.call('EXISTS', session_key) == 1 then
              return "call_exists"
            end
            if caller == callee then
              return "same_participant"
            end
            if redis.call('EXISTS', caller_key) == 1 then
              return "caller_busy"
            end
            if redis.call('EXISTS', callee_key) == 1 then
              return "callee_busy"
            end

            redis.call('HSET', session_key,
              'call_id', call_id,
              'caller', caller,
              'callee', callee,
              'state', 'ringing',
              'created_at', now_iso,
              'updated_at', now_iso,
              'revision', '1'
            )
            redis.call('SET', caller_key, call_id)
            redis.call('SET', callee_key, call_id)
            return "ok"
            """
        )

    def _session_key(self, call_id: str) -> str:
        return f"{self._key_prefix}:session:{call_id}"

    def _participant_key(self, nickname: str) -> str:
        return f"{self._key_prefix}:participant:{nickname}"

    def _parse_session(self, raw: dict[str, str]) -> CallSession:
        return CallSession(
            call_id=raw["call_id"],
            caller=raw["caller"],
            callee=raw["callee"],
            state=raw["state"],  # type: ignore[assignment]
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
            revision=int(raw.get("revision", "0")),
        )

    def get(self, call_id: str) -> CallSession | None:
        try:
            raw = self._redis.hgetall(self._session_key(call_id))
        except RedisError:
            return None
        if not raw:
            return None
        return self._parse_session(raw)

    def get_for_participant(self, nickname: str) -> CallSession | None:
        try:
            call_id = self._redis.get(self._participant_key(nickname))
        except RedisError:
            return None
        if not call_id:
            return None
        return self.get(call_id)

    def is_busy(self, nickname: str) -> bool:
        try:
            return self._redis.exists(self._participant_key(nickname)) == 1
        except RedisError:
            return False

    def create_invite(self, call_id: str, caller: str, callee: str) -> tuple[bool, str | None]:
        now_iso = utc_now_iso()
        try:
            result = self._create_invite_script(
                keys=[
                    self._session_key(call_id),
                    self._participant_key(caller),
                    self._participant_key(callee),
                ],
                args=[call_id, caller, callee, now_iso],
            )
        except RedisError:
            return self._create_invite_fallback(
                call_id=call_id,
                caller=caller,
                callee=callee,
                now_iso=now_iso,
            )

        if isinstance(result, bytes):
            result = result.decode("utf-8")
        if result == "ok":
            return True, None
        if result == "call_exists":
            return False, "call_id already exists"
        if result == "same_participant":
            return False, "caller and callee must differ"
        if result == "caller_busy":
            return False, "caller is busy"
        if result == "callee_busy":
            return False, "callee is busy"
        return False, "failed_to_create_invite"

    def _create_invite_fallback(
        self,
        *,
        call_id: str,
        caller: str,
        callee: str,
        now_iso: str,
    ) -> tuple[bool, str | None]:
        if caller == callee:
            return False, "caller and callee must differ"
        session_key = self._session_key(call_id)
        caller_key = self._participant_key(caller)
        callee_key = self._participant_key(callee)
        try:
            if self._redis.exists(session_key) == 1:
                return False, "call_id already exists"
            if self._redis.exists(caller_key) == 1:
                return False, "caller is busy"
            if self._redis.exists(callee_key) == 1:
                return False, "callee is busy"
            pipeline = self._redis.pipeline()
            pipeline.hset(
                session_key,
                mapping={
                    "call_id": call_id,
                    "caller": caller,
                    "callee": callee,
                    "state": "ringing",
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "revision": "1",
                },
            )
            pipeline.set(caller_key, call_id)
            pipeline.set(callee_key, call_id)
            pipeline.execute()
            return True, None
        except RedisError:
            return False, "session_store_unavailable"

    def set_state(self, call_id: str, state: CallState) -> None:
        session_key = self._session_key(call_id)
        try:
            if self._redis.exists(session_key) == 0:
                return
            pipeline = self._redis.pipeline()
            pipeline.hset(session_key, mapping={"state": state, "updated_at": utc_now_iso()})
            pipeline.hincrby(session_key, "revision", 1)
            pipeline.execute()
        except RedisError:
            return

    def peer_for(self, call_id: str, nickname: str) -> str | None:
        session = self.get(call_id)
        if session is None:
            return None
        if session.caller == nickname:
            return session.callee
        if session.callee == nickname:
            return session.caller
        return None

    def remove(self, call_id: str) -> CallSession | None:
        session = self.get(call_id)
        if session is None:
            return None
        try:
            pipeline = self._redis.pipeline()
            pipeline.delete(self._session_key(call_id))
            pipeline.delete(self._participant_key(session.caller))
            pipeline.delete(self._participant_key(session.callee))
            pipeline.execute()
        except RedisError:
            return session
        return session

    def expire_ringing(self, max_age_seconds: int) -> list[CallSession]:
        now = datetime.now(UTC)
        expired: list[CallSession] = []
        try:
            keys = list(self._redis.scan_iter(f"{self._key_prefix}:session:*"))
        except RedisError:
            return expired

        for session_key in keys:
            try:
                raw = self._redis.hgetall(session_key)
            except RedisError:
                continue
            if not raw:
                continue
            session = self._parse_session(raw)
            if session.state != "ringing":
                continue

            created_at = datetime.fromisoformat(session.created_at)
            age_seconds = (now - created_at).total_seconds()
            if age_seconds > max_age_seconds:
                removed = self.remove(session.call_id)
                if removed is not None:
                    expired.append(removed)
        return expired

    def all_sessions(self) -> list[CallSession]:
        sessions: list[CallSession] = []
        try:
            keys = list(self._redis.scan_iter(f"{self._key_prefix}:session:*"))
        except RedisError:
            return sessions
        for session_key in keys:
            try:
                raw = self._redis.hgetall(session_key)
            except RedisError:
                continue
            if not raw:
                continue
            sessions.append(self._parse_session(raw))
        return sessions

    def clear(self) -> None:
        try:
            keys = list(self._redis.scan_iter(f"{self._key_prefix}:*"))
        except RedisError:
            return
        if not keys:
            return
        try:
            self._redis.delete(*keys)
        except RedisError:
            return


settings = get_settings()
registry = RedisCallRegistry(
    redis_client=Redis.from_url(settings.signaling_redis_url, decode_responses=True),
    key_prefix=settings.signaling_session_key_prefix,
)

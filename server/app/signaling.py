from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from dataclasses import dataclass

from fastapi import WebSocket
from redis import Redis
from redis.exceptions import RedisError

from .config import get_settings


@dataclass(slots=True)
class _LocalConnection:
    websocket: WebSocket
    connection_id: str
    device_id: str
    token_jti: str | None


class InMemorySignalingHub:
    def __init__(self) -> None:
        self.connections: dict[str, WebSocket] = {}
        self._pending_notices: dict[str, list[dict]] = {}

    async def start(self) -> None:
        return

    async def stop(self) -> None:
        return

    async def connect(
        self,
        nickname: str,
        websocket: WebSocket,
        *,
        device_id: str = "",
        token_jti: str | None = None,
    ) -> None:
        del device_id, token_jti
        await websocket.accept()
        self.connections[nickname] = websocket

    def disconnect(self, nickname: str) -> None:
        self.connections.pop(nickname, None)

    async def send_to(self, nickname: str, message: dict) -> bool:
        websocket = self.connections.get(nickname)
        if websocket is None:
            return False
        await websocket.send_json(message)
        return True

    async def touch_presence(self, nickname: str) -> None:
        del nickname
        return

    async def enqueue_notice(self, nickname: str, message: dict) -> None:
        self._pending_notices.setdefault(nickname, []).append(message)

    async def pop_notices(self, nickname: str) -> list[dict]:
        return self._pending_notices.pop(nickname, [])

    def revoke_instance_presence(self) -> None:
        return

    def is_online(self, nickname: str) -> bool:
        return nickname in self.connections

    def clear(self) -> None:
        self.connections.clear()
        self._pending_notices.clear()


class RedisSignalingHub:
    def __init__(
        self,
        *,
        redis_client: Redis,
        instance_id: str,
        presence_key_prefix: str,
        pubsub_channel_prefix: str,
        presence_ttl_seconds: int,
    ) -> None:
        self._redis = redis_client
        self._instance_id = instance_id
        self._presence_key_prefix = presence_key_prefix.strip(":")
        self._pubsub_channel_prefix = pubsub_channel_prefix.strip(":")
        self._presence_ttl_seconds = presence_ttl_seconds
        self._connections: dict[str, _LocalConnection] = {}
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._listener_thread: threading.Thread | None = None
        self._listener_stop = threading.Event()
        self._pubsub = None
        self._notice_key_prefix = f"{self._presence_key_prefix}:notice"
        self._notice_ttl_seconds = 300
        self._touch_script = self._redis.register_script(
            """
            local key = KEYS[1]
            local instance_id = ARGV[1]
            local connection_id = ARGV[2]
            local now_unix = ARGV[3]
            local ttl_seconds = tonumber(ARGV[4])

            if redis.call('EXISTS', key) == 0 then
              return 0
            end
            if redis.call('HGET', key, 'instance_id') ~= instance_id then
              return 0
            end
            if redis.call('HGET', key, 'connection_id') ~= connection_id then
              return 0
            end
            redis.call('HSET', key, 'last_seen_at', now_unix)
            redis.call('EXPIRE', key, ttl_seconds)
            return 1
            """
        )
        self._delete_if_owned_script = self._redis.register_script(
            """
            local key = KEYS[1]
            local instance_id = ARGV[1]
            local connection_id = ARGV[2]

            if redis.call('EXISTS', key) == 0 then
              return 0
            end
            if redis.call('HGET', key, 'instance_id') ~= instance_id then
              return 0
            end
            if redis.call('HGET', key, 'connection_id') ~= connection_id then
              return 0
            end
            redis.call('DEL', key)
            return 1
            """
        )

    def _presence_key(self, nickname: str) -> str:
        return f"{self._presence_key_prefix}:{nickname}"

    def _channel_for_instance(self, instance_id: str) -> str:
        return f"{self._pubsub_channel_prefix}:{instance_id}"

    def _notice_key(self, nickname: str) -> str:
        return f"{self._notice_key_prefix}:{nickname}"

    def _get_presence(self, nickname: str) -> dict[str, str]:
        try:
            return self._redis.hgetall(self._presence_key(nickname))
        except RedisError:
            return {}

    def _is_locally_owned(self, nickname: str, connection_id: str) -> bool:
        presence = self._get_presence(nickname)
        if not presence:
            return False
        return (
            presence.get("instance_id") == self._instance_id
            and presence.get("connection_id") == connection_id
        )

    def revoke_instance_presence(self) -> None:
        try:
            keys = list(self._redis.scan_iter(f"{self._presence_key_prefix}:*"))
        except RedisError:
            return
        for key in keys:
            if ":notice:" in key:
                continue
            try:
                presence = self._redis.hgetall(key)
            except RedisError:
                continue
            if presence.get("instance_id") == self._instance_id:
                try:
                    self._redis.delete(key)
                except RedisError:
                    continue

    async def start(self) -> None:
        if self._listener_thread is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._listener_stop.clear()
        self._pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
        self._pubsub.subscribe(self._channel_for_instance(self._instance_id))
        self._listener_thread = threading.Thread(
            target=self._pubsub_listener_loop,
            name=f"signaling-pubsub-{self._instance_id}",
            daemon=True,
        )
        self._listener_thread.start()

    async def stop(self) -> None:
        self._listener_stop.set()
        if self._pubsub is not None:
            try:
                self._pubsub.close()
            except RedisError:
                pass
            self._pubsub = None
        if self._listener_thread is not None:
            self._listener_thread.join(timeout=1.0)
            self._listener_thread = None

    def _pubsub_listener_loop(self) -> None:
        if self._pubsub is None:
            return
        while not self._listener_stop.is_set():
            try:
                message = self._pubsub.get_message(timeout=0.25)
            except RedisError:
                time.sleep(0.25)
                continue
            except Exception:
                time.sleep(0.25)
                continue
            if message is None:
                continue
            data = message.get("data")
            if data is None:
                continue
            if isinstance(data, bytes):
                raw_payload = data.decode("utf-8")
            else:
                raw_payload = str(data)
            try:
                payload = json.loads(raw_payload)
            except json.JSONDecodeError:
                continue
            to_nickname = payload.get("to_nickname")
            forwarded_message = payload.get("message")
            if not isinstance(to_nickname, str) or not isinstance(forwarded_message, dict):
                continue
            if self._loop is None:
                continue
            asyncio.run_coroutine_threadsafe(
                self._deliver_to_local_connection(to_nickname, forwarded_message),
                self._loop,
            )

    async def _deliver_to_local_connection(self, nickname: str, message: dict) -> bool:
        with self._lock:
            connection = self._connections.get(nickname)
        if connection is None:
            return False
        try:
            await connection.websocket.send_json(message)
            return True
        except Exception:
            return False

    async def connect(
        self,
        nickname: str,
        websocket: WebSocket,
        *,
        device_id: str = "",
        token_jti: str | None = None,
    ) -> None:
        await websocket.accept()
        connection_id = uuid.uuid4().hex
        connection = _LocalConnection(
            websocket=websocket,
            connection_id=connection_id,
            device_id=device_id,
            token_jti=token_jti,
        )
        with self._lock:
            self._connections[nickname] = connection
        now_unix = str(int(time.time()))
        try:
            self._redis.hset(
                self._presence_key(nickname),
                mapping={
                    "nickname": nickname,
                    "instance_id": self._instance_id,
                    "connection_id": connection_id,
                    "device_id": device_id,
                    "token_jti": token_jti or "",
                    "connected_at": now_unix,
                    "last_seen_at": now_unix,
                },
            )
            self._redis.expire(self._presence_key(nickname), self._presence_ttl_seconds)
        except RedisError:
            return

    def disconnect(self, nickname: str) -> None:
        with self._lock:
            connection = self._connections.pop(nickname, None)
        if connection is None:
            return
        try:
            result = self._delete_if_owned_script(
                keys=[self._presence_key(nickname)],
                args=[self._instance_id, connection.connection_id],
            )
        except RedisError:
            result = 0
        if isinstance(result, bytes):
            try:
                result = int(result.decode("utf-8"))
            except ValueError:
                result = 0
        if int(result) == 1:
            return
        presence = self._get_presence(nickname)
        if (
            presence.get("instance_id") == self._instance_id
            and presence.get("connection_id") == connection.connection_id
        ):
            try:
                self._redis.delete(self._presence_key(nickname))
            except RedisError:
                return

    async def touch_presence(self, nickname: str) -> None:
        with self._lock:
            connection = self._connections.get(nickname)
        if connection is None:
            return
        try:
            result = self._touch_script(
                keys=[self._presence_key(nickname)],
                args=[
                    self._instance_id,
                    connection.connection_id,
                    str(int(time.time())),
                    str(self._presence_ttl_seconds),
                ],
            )
        except RedisError:
            result = 0
        if isinstance(result, bytes):
            try:
                result = int(result.decode("utf-8"))
            except ValueError:
                result = 0
        if int(result) == 1:
            return
        presence = self._get_presence(nickname)
        if (
            presence.get("instance_id") == self._instance_id
            and presence.get("connection_id") == connection.connection_id
        ):
            now_unix = str(int(time.time()))
            try:
                self._redis.hset(
                    self._presence_key(nickname),
                    mapping={"last_seen_at": now_unix},
                )
                self._redis.expire(self._presence_key(nickname), self._presence_ttl_seconds)
            except RedisError:
                return

    async def enqueue_notice(self, nickname: str, message: dict) -> None:
        payload = json.dumps(message)
        try:
            pipeline = self._redis.pipeline()
            pipeline.rpush(self._notice_key(nickname), payload)
            pipeline.expire(self._notice_key(nickname), self._notice_ttl_seconds)
            pipeline.execute()
        except RedisError:
            return

    async def pop_notices(self, nickname: str) -> list[dict]:
        key = self._notice_key(nickname)
        try:
            raw_items = self._redis.lrange(key, 0, -1)
            self._redis.delete(key)
        except RedisError:
            return []
        notices: list[dict] = []
        for raw_item in raw_items:
            try:
                parsed = json.loads(raw_item)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(parsed, dict):
                notices.append(parsed)
        return notices

    async def send_to(self, nickname: str, message: dict) -> bool:
        with self._lock:
            local_connection = self._connections.get(nickname)
        if local_connection is not None:
            if self._is_locally_owned(nickname, local_connection.connection_id):
                try:
                    await local_connection.websocket.send_json(message)
                    return True
                except Exception:
                    return False
            with self._lock:
                current_connection = self._connections.get(nickname)
                if (
                    current_connection is not None
                    and current_connection.connection_id == local_connection.connection_id
                ):
                    self._connections.pop(nickname, None)

        presence = self._get_presence(nickname)
        if not presence:
            return False

        target_instance_id = presence.get("instance_id")
        if not target_instance_id or target_instance_id == self._instance_id:
            return False

        payload = json.dumps({"to_nickname": nickname, "message": message})
        try:
            subscribers = self._redis.publish(
                self._channel_for_instance(target_instance_id),
                payload,
            )
        except RedisError:
            return False
        return subscribers > 0

    def is_online(self, nickname: str) -> bool:
        with self._lock:
            local_connection = self._connections.get(nickname)
        if local_connection is not None and self._is_locally_owned(
            nickname, local_connection.connection_id
        ):
            return True
        presence = self._get_presence(nickname)
        return bool(presence)

    def clear(self) -> None:
        with self._lock:
            self._connections.clear()


settings = get_settings()
hub = RedisSignalingHub(
    redis_client=Redis.from_url(settings.signaling_redis_url, decode_responses=True),
    instance_id=settings.signaling_instance_id,
    presence_key_prefix=settings.signaling_presence_key_prefix,
    pubsub_channel_prefix=settings.signaling_pubsub_channel_prefix,
    presence_ttl_seconds=settings.signaling_presence_ttl_seconds,
)

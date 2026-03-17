from __future__ import annotations

import threading
import time
from collections import Counter
from datetime import UTC, datetime


class ObservabilityState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_monotonic = time.monotonic()
        self._counters: Counter[str] = Counter()

    def incr(self, key: str, *, amount: int = 1) -> None:
        normalized = key.strip()
        if not normalized:
            return
        with self._lock:
            self._counters[normalized] += amount

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            counters = dict(self._counters)
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime_seconds": int(time.monotonic() - self._started_monotonic),
            "counters": counters,
        }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._started_monotonic = time.monotonic()


observability = ObservabilityState()

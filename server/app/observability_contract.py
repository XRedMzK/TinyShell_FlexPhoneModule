from __future__ import annotations

import re

REASON_CLASSES = {"operational", "security", "dependency"}

REASON_CLASS_BY_CODE: dict[str, str] = {
    # Operational lifecycle / control flow
    "ok": "operational",
    "http_error": "operational",
    "exception": "operational",
    "reconcile_started": "operational",
    "reconcile_completed": "operational",
    "peer_disconnected": "operational",
    # Dependency
    "dependency_ready": "dependency",
    "dependency_degraded": "dependency",
    "challenge_store_unavailable": "dependency",
    "session_store_unavailable": "dependency",
    # Security / auth / validation
    "invalid_nickname": "security",
    "device_not_registered": "security",
    "wrong_device": "security",
    "wrong_nickname_or_device": "security",
    "challenge_not_found": "security",
    "challenge_expired": "security",
    "challenge_consumed": "security",
    "signature_mismatch": "security",
    "ws_rejected_preconnect": "security",
    "token_missing": "security",
    "token_invalid": "security",
    "token_expired": "security",
    "token_wrong_audience": "security",
    "token_wrong_nickname": "security",
    "token_wrong_device": "security",
}

CANONICAL_EVENT_NAMES = {
    "http.request.completed",
    "http.request.failed",
    "runtime.ready.ok",
    "runtime.ready.degraded",
    "auth.challenge.issued",
    "auth.challenge.rejected",
    "auth.verify.succeeded",
    "auth.verify.failed",
    "ws.connect.accepted",
    "ws.connect.rejected",
    "ws.disconnect",
    "reconcile.cleanup.started",
    "reconcile.cleanup.completed",
    "reconcile.startup.started",
    "reconcile.startup.completed",
}

COUNTER_STATIC_PREFIXES = (
    "health.",
    "ready.",
    "auth.",
    "ws.",
    "reconcile.",
)

COUNTER_DYNAMIC_PREFIXES = (
    "http.requests.",
    "ws.connect.rejected.",
)

_EVENT_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+$")
_COUNTER_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")


def classify_reason_code(reason_code: str | None) -> str:
    normalized = (reason_code or "").strip().lower()
    if not normalized:
        return "operational"
    return REASON_CLASS_BY_CODE.get(normalized, "operational")


def is_canonical_event_name(event_name: str) -> bool:
    if event_name not in CANONICAL_EVENT_NAMES:
        return False
    return bool(_EVENT_NAME_RE.fullmatch(event_name))


def is_canonical_counter_name(counter_name: str) -> bool:
    normalized = counter_name.strip()
    if not normalized:
        return False
    if normalized.startswith(COUNTER_DYNAMIC_PREFIXES):
        return True
    if not normalized.startswith(COUNTER_STATIC_PREFIXES):
        return False
    return bool(_COUNTER_NAME_RE.fullmatch(normalized))

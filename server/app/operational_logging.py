from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from .observability_contract import classify_reason_code

logger = logging.getLogger("flexphone.ops")
logger.setLevel(logging.INFO)

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_route_ctx: ContextVar[str | None] = ContextVar("route", default=None)
_method_ctx: ContextVar[str | None] = ContextVar("method", default=None)

_SENSITIVE_KEYS = {
    "access_token",
    "authorization",
    "challenge",
    "password",
    "private_key",
    "secret",
    "signature",
    "token",
}


def set_request_context(*, request_id: str | None, route: str | None, method: str | None) -> None:
    _request_id_ctx.set(request_id)
    _route_ctx.set(route)
    _method_ctx.set(method)


def clear_request_context() -> None:
    _request_id_ctx.set(None)
    _route_ctx.set(None)
    _method_ctx.set(None)


def _trace_fields() -> tuple[str | None, str | None]:
    try:
        from opentelemetry import trace as otel_trace

        span = otel_trace.get_current_span()
        span_context = span.get_span_context() if span is not None else None
        if span_context is None or not span_context.is_valid:
            return None, None
        return f"{span_context.trace_id:032x}", f"{span_context.span_id:016x}"
    except Exception:
        return None, None


def _sanitize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in fields.items():
        normalized_key = key.lower()
        if normalized_key in _SENSITIVE_KEYS:
            sanitized[key] = "***redacted***"
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key] = value
            continue
        sanitized[key] = str(value)
    return sanitized


def log_event(
    *,
    level: str,
    event: str,
    message: str,
    service: str,
    env: str,
    component: str,
    reason_code: str,
    **fields: Any,
) -> None:
    trace_id, span_id = _trace_fields()
    payload: dict[str, Any] = {
        "ts": datetime.now(UTC).isoformat(),
        "level": level.upper(),
        "service": service,
        "env": env,
        "event": event,
        "message": message,
        "request_id": _request_id_ctx.get(),
        "trace_id": trace_id,
        "span_id": span_id,
        "route": _route_ctx.get(),
        "method": _method_ctx.get(),
        "component": component,
        "reason_code": reason_code,
        "reason_class": classify_reason_code(reason_code),
    }
    payload.update(_sanitize_fields(fields))
    level_no = getattr(logging, level.upper(), logging.INFO)
    logger.log(level_no, json.dumps(payload, ensure_ascii=True, separators=(",", ":")))

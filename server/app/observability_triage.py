from __future__ import annotations

from .observability_contract import REASON_CLASSES

CORRELATION_FIELDS_ALWAYS_REQUIRED = ("request_id",)
CORRELATION_FIELDS_REQUIRE_ACTIVE_SPAN = ("trace_id", "span_id")
CORRELATION_FIELDS_FOR_CLASSIFIED_EVENTS = ("reason_code", "reason_class")

TRIAGE_DASHBOARD_BY_REASON_CLASS = {
    "dependency": "runtime-dependency-health",
    "security": "auth-security-rejections",
    "operational": "signaling-runtime-operations",
}

TRIAGE_DOMAIN_HINTS = {
    "runtime.ready.": "runtime-dependency-health",
    "auth.": "auth-security-rejections",
    "ws.": "signaling-runtime-operations",
    "reconcile.": "signaling-runtime-operations",
    "http.request.": "signaling-runtime-operations",
}


def dashboard_for_reason_class(reason_class: str) -> str:
    normalized = reason_class.strip().lower()
    if normalized in TRIAGE_DASHBOARD_BY_REASON_CLASS:
        return TRIAGE_DASHBOARD_BY_REASON_CLASS[normalized]
    return TRIAGE_DASHBOARD_BY_REASON_CLASS["operational"]


def dashboard_for_event(event_name: str) -> str:
    for prefix, dashboard in TRIAGE_DOMAIN_HINTS.items():
        if event_name.startswith(prefix):
            return dashboard
    return TRIAGE_DASHBOARD_BY_REASON_CLASS["operational"]


def triage_classes_are_consistent() -> bool:
    return set(TRIAGE_DASHBOARD_BY_REASON_CLASS.keys()) == REASON_CLASSES

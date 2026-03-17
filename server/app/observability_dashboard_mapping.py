from __future__ import annotations

from dataclasses import dataclass
import re

from .observability_contract import (
    CANONICAL_EVENT_NAMES,
    REASON_CLASSES,
    is_canonical_counter_name,
    is_canonical_event_name,
)
from .observability_triage import dashboard_for_event


@dataclass(frozen=True)
class DashboardQuerySpec:
    signal: str
    scope: str
    description: str
    query_template: str
    counter_keys: tuple[str, ...] = ()
    event_names: tuple[str, ...] = ()
    reason_classes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AlertRuleSpec:
    reason_class: str
    severity: str
    description: str
    dashboard_id: str
    primary_event: str
    query_ref: str
    condition_template: str
    for_duration: str


# Baseline alias mapping from in-process counter keys to Prometheus-style names.
# This does not change runtime metrics behavior; it defines dashboard-ready naming.
PROM_COUNTER_ALIAS_BASELINE: dict[str, str] = {
    "health.ok": "flexphone_health_ok_total",
    "ready.ok": "flexphone_ready_ok_total",
    "ready.degraded": "flexphone_ready_degraded_total",
    "auth.challenge.ok": "flexphone_auth_challenge_ok_total",
    "auth.challenge.rejected.store_unavailable": "flexphone_auth_challenge_store_unavailable_total",
    "auth.verify.ok": "flexphone_auth_verify_ok_total",
    "auth.verify.rejected.invalid_signature": "flexphone_auth_verify_invalid_signature_total",
    "auth.verify.rejected.challenge_expired": "flexphone_auth_verify_challenge_expired_total",
    "ws.connect.accepted": "flexphone_ws_connect_accepted_total",
    "ws.connect.rejected.token_missing": "flexphone_ws_connect_token_missing_total",
    "ws.disconnect": "flexphone_ws_disconnect_total",
    "reconcile.cleanup.connected_restart": "flexphone_reconcile_cleanup_connected_restart_total",
}


DASHBOARD_QUERY_BASELINE: dict[str, DashboardQuerySpec] = {
    "readiness.degraded.rate": DashboardQuerySpec(
        signal="metrics",
        scope="readiness",
        description="Count readiness degraded transitions over a rolling window.",
        query_template="sum(increase(flexphone_ready_degraded_total[5m]))",
        counter_keys=("ready.degraded",),
        reason_classes=("dependency",),
    ),
    "auth.verify.reject.security.rate": DashboardQuerySpec(
        signal="metrics",
        scope="auth",
        description="Security-oriented auth verify rejects over time.",
        query_template=(
            "sum(increase(flexphone_auth_verify_invalid_signature_total[5m])) + "
            "sum(increase(flexphone_auth_verify_challenge_expired_total[5m]))"
        ),
        counter_keys=(
            "auth.verify.rejected.invalid_signature",
            "auth.verify.rejected.challenge_expired",
        ),
        reason_classes=("security",),
    ),
    "ws.connect.reject.security.rate": DashboardQuerySpec(
        signal="metrics",
        scope="ws",
        description="WebSocket security rejects (missing token) over time.",
        query_template="sum(increase(flexphone_ws_connect_token_missing_total[5m]))",
        counter_keys=("ws.connect.rejected.token_missing",),
        reason_classes=("security",),
    ),
    "reconcile.cleanup.operational.rate": DashboardQuerySpec(
        signal="metrics",
        scope="reconcile",
        description="Restart cleanup operations activity.",
        query_template="sum(increase(flexphone_reconcile_cleanup_connected_restart_total[15m]))",
        counter_keys=("reconcile.cleanup.connected_restart",),
        reason_classes=("operational",),
    ),
    "logs.dependency.degraded": DashboardQuerySpec(
        signal="logs",
        scope="readiness",
        description="Dependency degradations from structured logs.",
        query_template='event =~ "runtime.ready.degraded|auth.verify.failed|auth.challenge.rejected" '
        'AND reason_class="dependency"',
        event_names=(
            "runtime.ready.degraded",
            "auth.verify.failed",
            "auth.challenge.rejected",
        ),
        reason_classes=("dependency",),
    ),
    "logs.security.rejections": DashboardQuerySpec(
        signal="logs",
        scope="auth",
        description="Security reject paths from auth/ws logs.",
        query_template='event =~ "auth.verify.failed|auth.challenge.rejected|ws.connect.rejected" '
        'AND reason_class="security"',
        event_names=(
            "auth.verify.failed",
            "auth.challenge.rejected",
            "ws.connect.rejected",
        ),
        reason_classes=("security",),
    ),
    "traces.auth.verify.failures": DashboardQuerySpec(
        signal="traces",
        scope="auth",
        description="Auth verify spans where result is not successful.",
        query_template='span.name="auth.verify" AND attributes["auth.result"] =~ "^rejected_"',
        event_names=("auth.verify.failed",),
        reason_classes=("security", "dependency"),
    ),
}


ALERT_RULE_BASELINE: dict[str, AlertRuleSpec] = {
    "dependency.readiness_degraded": AlertRuleSpec(
        reason_class="dependency",
        severity="critical",
        description="Readiness degraded repeatedly in rolling window.",
        dashboard_id="runtime-dependency-health",
        primary_event="runtime.ready.degraded",
        query_ref="readiness.degraded.rate",
        condition_template="sum(increase(flexphone_ready_degraded_total[5m])) > 0",
        for_duration="2m",
    ),
    "security.auth_reject_spike": AlertRuleSpec(
        reason_class="security",
        severity="warning",
        description="Auth security reject rate spike.",
        dashboard_id="auth-security-rejections",
        primary_event="auth.verify.failed",
        query_ref="auth.verify.reject.security.rate",
        condition_template="sum(increase(flexphone_auth_verify_invalid_signature_total[5m])) > 10",
        for_duration="5m",
    ),
    "operational.ws_disconnect_spike": AlertRuleSpec(
        reason_class="operational",
        severity="warning",
        description="Operational disconnect spikes in signaling.",
        dashboard_id="signaling-runtime-operations",
        primary_event="ws.disconnect",
        query_ref="reconcile.cleanup.operational.rate",
        condition_template="sum(increase(flexphone_ws_disconnect_total[5m])) > 20",
        for_duration="5m",
    ),
}

_PROM_COUNTER_RE = re.compile(r"^[a-z][a-z0-9_]*_total$")
_VALID_SIGNALS = {"metrics", "logs", "traces"}
_REQUIRED_SCOPES = {"auth", "ws", "reconcile", "readiness"}


def validate_dashboard_alert_mapping_contract() -> list[str]:
    errors: list[str] = []

    for counter_key, prom_name in PROM_COUNTER_ALIAS_BASELINE.items():
        if not is_canonical_counter_name(counter_key):
            errors.append(f"PROM counter alias uses non-canonical counter key: {counter_key}")
        if not _PROM_COUNTER_RE.fullmatch(prom_name):
            errors.append(f"PROM counter alias name must be prom-style *_total: {prom_name}")

    scopes_in_queries = {spec.scope for spec in DASHBOARD_QUERY_BASELINE.values()}
    missing_scopes = _REQUIRED_SCOPES - scopes_in_queries
    for scope in sorted(missing_scopes):
        errors.append(f"Missing required dashboard query scope: {scope}")

    for query_id, spec in DASHBOARD_QUERY_BASELINE.items():
        if spec.signal not in _VALID_SIGNALS:
            errors.append(f"{query_id}: invalid signal type: {spec.signal}")

        for counter_key in spec.counter_keys:
            if not is_canonical_counter_name(counter_key):
                errors.append(f"{query_id}: non-canonical counter key: {counter_key}")
            if counter_key not in PROM_COUNTER_ALIAS_BASELINE:
                errors.append(f"{query_id}: counter key missing PROM alias baseline: {counter_key}")

        for event_name in spec.event_names:
            if event_name not in CANONICAL_EVENT_NAMES or not is_canonical_event_name(event_name):
                errors.append(f"{query_id}: non-canonical event name: {event_name}")

        for reason_class in spec.reason_classes:
            if reason_class not in REASON_CLASSES:
                errors.append(f"{query_id}: unknown reason class: {reason_class}")

    for alert_id, alert in ALERT_RULE_BASELINE.items():
        if alert.reason_class not in REASON_CLASSES:
            errors.append(f"{alert_id}: unknown reason class: {alert.reason_class}")

        if alert.primary_event not in CANONICAL_EVENT_NAMES:
            errors.append(f"{alert_id}: primary_event is not canonical: {alert.primary_event}")

        if alert.query_ref not in DASHBOARD_QUERY_BASELINE:
            errors.append(f"{alert_id}: query_ref not found: {alert.query_ref}")

        expected_dashboard = dashboard_for_event(alert.primary_event)
        if alert.dashboard_id != expected_dashboard:
            errors.append(
                f"{alert_id}: dashboard_id mismatch for event '{alert.primary_event}', "
                f"expected '{expected_dashboard}', got '{alert.dashboard_id}'"
            )

    return errors

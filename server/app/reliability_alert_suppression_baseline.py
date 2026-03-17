from __future__ import annotations

from dataclasses import dataclass
import re

from .reliability_alert_routing_baseline import (
    ALERT_ROUTING_LABEL_BASELINE,
    ROUTING_REQUIRED_LABEL_KEYS,
)


@dataclass(frozen=True)
class AlertGroupingSpec:
    alert_alias: str
    severity: str
    group_by: tuple[str, ...]
    dedup_mode: str


@dataclass(frozen=True)
class AlertGroupTimingSpec:
    severity: str
    group_wait: str
    group_interval: str
    repeat_interval: str


@dataclass(frozen=True)
class InhibitionRuleSpec:
    rule_id: str
    source_matchers: dict[str, str]
    target_matchers: dict[str, str]
    equal_labels: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class SilencePolicySpec:
    policy_id: str
    policy_type: str
    requires_owner: bool
    requires_reason: bool
    requires_time_bound: bool
    suppresses_notifications_only: bool
    allowed_severities: tuple[str, ...]
    max_duration_hours: int | None


_DURATION_RE = re.compile(r"^(?P<count>[1-9][0-9]*)(?P<unit>[smhd])$")
_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}

_ALLOWED_SEVERITIES = {"page", "ticket", "info"}
_REQUIRED_GROUP_LABELS = {"service", "severity", "routing_key"}

DEDUP_CONTROL_BASELINE = {
    "mode": "notification_noise_reduction",
    "exactly_once_guarantee": False,
    "ha_delivery_model": "fail_open_at_least_once",
}


def _group_by_for_severity(severity: str) -> tuple[str, ...]:
    if severity == "page":
        # Keep page alerts narrow to avoid hiding critical classes.
        return ("service", "component", "severity", "alert_class", "routing_key")
    if severity == "ticket":
        return ("service", "component", "severity", "routing_key")
    return ("service", "severity", "routing_key")


def _build_grouping_baseline() -> dict[str, AlertGroupingSpec]:
    out: dict[str, AlertGroupingSpec] = {}
    for alert_alias, routing_spec in sorted(ALERT_ROUTING_LABEL_BASELINE.items()):
        out[alert_alias] = AlertGroupingSpec(
            alert_alias=alert_alias,
            severity=routing_spec.severity,
            group_by=_group_by_for_severity(routing_spec.severity),
            dedup_mode=DEDUP_CONTROL_BASELINE["mode"],
        )
    return out


ALERT_GROUPING_BASELINE = _build_grouping_baseline()

ALERT_GROUP_TIMING_BASELINE: dict[str, AlertGroupTimingSpec] = {
    "page": AlertGroupTimingSpec(
        severity="page",
        group_wait="30s",
        group_interval="5m",
        repeat_interval="4h",
    ),
    "ticket": AlertGroupTimingSpec(
        severity="ticket",
        group_wait="60s",
        group_interval="10m",
        repeat_interval="8h",
    ),
    "info": AlertGroupTimingSpec(
        severity="info",
        group_wait="120s",
        group_interval="15m",
        repeat_interval="12h",
    ),
}

ALERT_INHIBITION_POLICY_BASELINE: dict[str, InhibitionRuleSpec] = {
    "page_inhibits_ticket_same_scope": InhibitionRuleSpec(
        rule_id="page_inhibits_ticket_same_scope",
        source_matchers={"severity": "page", "alert_class": "slo_burn_rate"},
        target_matchers={"severity": "ticket", "alert_class": "slo_burn_rate"},
        equal_labels=("service", "component", "routing_key"),
        description="Suppress ticket notifications when parent page alert is active in the same scope.",
    ),
    "page_inhibits_info_same_scope": InhibitionRuleSpec(
        rule_id="page_inhibits_info_same_scope",
        source_matchers={"severity": "page", "alert_class": "slo_burn_rate"},
        target_matchers={"severity": "info", "alert_class": "slo_burn_rate"},
        equal_labels=("service", "component", "routing_key"),
        description="Suppress info notifications when parent page alert is active in the same scope.",
    ),
}

ALERT_SILENCE_POLICY_BASELINE: dict[str, SilencePolicySpec] = {
    "one_time_maintenance_silence": SilencePolicySpec(
        policy_id="one_time_maintenance_silence",
        policy_type="silence",
        requires_owner=True,
        requires_reason=True,
        requires_time_bound=True,
        suppresses_notifications_only=True,
        allowed_severities=("page", "ticket", "info"),
        max_duration_hours=2,
    ),
    "recurring_mute_timing": SilencePolicySpec(
        policy_id="recurring_mute_timing",
        policy_type="mute_timing",
        requires_owner=True,
        requires_reason=True,
        requires_time_bound=True,
        suppresses_notifications_only=True,
        allowed_severities=("ticket", "info"),
        max_duration_hours=None,
    ),
}


def _parse_duration_to_seconds(value: str) -> int | None:
    match = _DURATION_RE.fullmatch(value)
    if match is None:
        return None
    count = int(match.group("count"))
    unit = match.group("unit")
    return count * _UNIT_SECONDS[unit]


def validate_reliability_alert_suppression_baseline_contract() -> list[str]:
    errors: list[str] = []

    expected_aliases = set(ALERT_ROUTING_LABEL_BASELINE.keys())
    if set(ALERT_GROUPING_BASELINE.keys()) != expected_aliases:
        errors.append("ALERT_GROUPING_BASELINE keys must match ALERT_ROUTING_LABEL_BASELINE")

    if DEDUP_CONTROL_BASELINE.get("mode") != "notification_noise_reduction":
        errors.append("DEDUP_CONTROL_BASELINE.mode must be notification_noise_reduction")
    if DEDUP_CONTROL_BASELINE.get("exactly_once_guarantee") is not False:
        errors.append("DEDUP_CONTROL_BASELINE.exactly_once_guarantee must be false")
    if DEDUP_CONTROL_BASELINE.get("ha_delivery_model") != "fail_open_at_least_once":
        errors.append("DEDUP_CONTROL_BASELINE.ha_delivery_model must be fail_open_at_least_once")

    for alert_alias, grouping_spec in ALERT_GROUPING_BASELINE.items():
        if grouping_spec.alert_alias != alert_alias:
            errors.append(f"{alert_alias}: alert_alias field must match dictionary key")

        routing_spec = ALERT_ROUTING_LABEL_BASELINE.get(alert_alias)
        if routing_spec is None:
            errors.append(f"{alert_alias}: missing routing spec for grouping")
            continue

        if grouping_spec.severity != routing_spec.severity:
            errors.append(
                f"{alert_alias}: grouping severity mismatch, expected {routing_spec.severity}, got {grouping_spec.severity}"
            )

        group_by_set = set(grouping_spec.group_by)
        if not _REQUIRED_GROUP_LABELS.issubset(group_by_set):
            errors.append(
                f"{alert_alias}: group_by must include {_REQUIRED_GROUP_LABELS}, got {grouping_spec.group_by}"
            )
        if not group_by_set.issubset(set(ROUTING_REQUIRED_LABEL_KEYS)):
            errors.append(
                f"{alert_alias}: group_by must be subset of routing labels {ROUTING_REQUIRED_LABEL_KEYS}"
            )

        if grouping_spec.severity == "page" and "component" not in group_by_set:
            errors.append(f"{alert_alias}: page grouping must include component label")

        if grouping_spec.dedup_mode != DEDUP_CONTROL_BASELINE["mode"]:
            errors.append(
                f"{alert_alias}: dedup_mode mismatch, expected {DEDUP_CONTROL_BASELINE['mode']}, got {grouping_spec.dedup_mode}"
            )

    if set(ALERT_GROUP_TIMING_BASELINE.keys()) != _ALLOWED_SEVERITIES:
        errors.append(
            f"ALERT_GROUP_TIMING_BASELINE must define exactly {_ALLOWED_SEVERITIES}"
        )
    for severity, timing_spec in ALERT_GROUP_TIMING_BASELINE.items():
        if timing_spec.severity != severity:
            errors.append(f"{severity}: timing severity field must match dictionary key")

        wait_seconds = _parse_duration_to_seconds(timing_spec.group_wait)
        interval_seconds = _parse_duration_to_seconds(timing_spec.group_interval)
        repeat_seconds = _parse_duration_to_seconds(timing_spec.repeat_interval)
        if wait_seconds is None:
            errors.append(f"{severity}: invalid group_wait duration: {timing_spec.group_wait}")
            continue
        if interval_seconds is None:
            errors.append(
                f"{severity}: invalid group_interval duration: {timing_spec.group_interval}"
            )
            continue
        if repeat_seconds is None:
            errors.append(
                f"{severity}: invalid repeat_interval duration: {timing_spec.repeat_interval}"
            )
            continue

        if wait_seconds > interval_seconds:
            errors.append(
                f"{severity}: group_wait must be <= group_interval ({timing_spec.group_wait} > {timing_spec.group_interval})"
            )
        if interval_seconds > repeat_seconds:
            errors.append(
                f"{severity}: group_interval must be <= repeat_interval ({timing_spec.group_interval} > {timing_spec.repeat_interval})"
            )

    if not ALERT_INHIBITION_POLICY_BASELINE:
        errors.append("ALERT_INHIBITION_POLICY_BASELINE must not be empty")
    for rule_id, rule in ALERT_INHIBITION_POLICY_BASELINE.items():
        if rule.rule_id != rule_id:
            errors.append(f"{rule_id}: rule_id field must match dictionary key")
        if not rule.source_matchers:
            errors.append(f"{rule_id}: source_matchers must not be empty")
        if not rule.target_matchers:
            errors.append(f"{rule_id}: target_matchers must not be empty")

        source_severity = rule.source_matchers.get("severity")
        target_severity = rule.target_matchers.get("severity")
        if source_severity is None or target_severity is None:
            errors.append(f"{rule_id}: source/target matchers must define severity")
        else:
            if source_severity == "page" and target_severity == "page":
                errors.append(f"{rule_id}: inhibition must not define page -> page suppression")
            if source_severity == target_severity:
                errors.append(f"{rule_id}: source and target severity should not be identical")

        if rule.source_matchers == rule.target_matchers:
            errors.append(f"{rule_id}: source and target matchers must not be identical")

        if not set(rule.equal_labels).issubset(set(ROUTING_REQUIRED_LABEL_KEYS)):
            errors.append(
                f"{rule_id}: equal_labels must be subset of routing labels {ROUTING_REQUIRED_LABEL_KEYS}"
            )

    if not ALERT_SILENCE_POLICY_BASELINE:
        errors.append("ALERT_SILENCE_POLICY_BASELINE must not be empty")

    policy_types: set[str] = set()
    for policy_id, policy in ALERT_SILENCE_POLICY_BASELINE.items():
        if policy.policy_id != policy_id:
            errors.append(f"{policy_id}: policy_id field must match dictionary key")

        policy_types.add(policy.policy_type)
        if policy.policy_type not in {"silence", "mute_timing"}:
            errors.append(f"{policy_id}: unknown policy_type: {policy.policy_type}")

        if not policy.requires_owner:
            errors.append(f"{policy_id}: requires_owner must be true")
        if not policy.requires_reason:
            errors.append(f"{policy_id}: requires_reason must be true")
        if not policy.requires_time_bound:
            errors.append(f"{policy_id}: requires_time_bound must be true")
        if not policy.suppresses_notifications_only:
            errors.append(f"{policy_id}: suppresses_notifications_only must be true")

        allowed = set(policy.allowed_severities)
        if not allowed:
            errors.append(f"{policy_id}: allowed_severities must not be empty")
        if not allowed.issubset(_ALLOWED_SEVERITIES):
            errors.append(f"{policy_id}: allowed_severities must be subset of {_ALLOWED_SEVERITIES}")

        if "page" in allowed and policy.max_duration_hours is None:
            errors.append(
                f"{policy_id}: page suppression requires explicit max_duration_hours"
            )
        if policy.policy_type == "mute_timing" and "page" in allowed:
            errors.append(f"{policy_id}: mute_timing must not include page severity suppression")

    if "silence" not in policy_types:
        errors.append("ALERT_SILENCE_POLICY_BASELINE must include a silence policy")
    if "mute_timing" not in policy_types:
        errors.append("ALERT_SILENCE_POLICY_BASELINE must include a mute_timing policy")

    return errors

from __future__ import annotations

from dataclasses import dataclass

from .reliability_alert_policy_mapping import SLO_ALERT_RULE_ALIAS_BASELINE

SERVICE_NAME = "flexphone-server"
DEFAULT_OWNER_TEAM = "core_platform"


@dataclass(frozen=True)
class AlertRoutingLabelSpec:
    service: str
    component: str
    severity: str
    alert_class: str
    routing_key: str
    runbook_ref: str
    owner_team: str


@dataclass(frozen=True)
class NotificationTargetSpec:
    target_id: str
    target_class: str
    channel: str
    description: str


@dataclass(frozen=True)
class EscalationPolicySpec:
    alert_alias: str
    severity: str
    notification_class: str
    primary_target: str
    escalation_target: str | None
    escalation_after_minutes: int | None


@dataclass(frozen=True)
class RunbookOwnershipSpec:
    alert_alias: str
    runbook_ref: str
    owner_team: str
    escalation_target: str | None


_COMPONENT_BY_SLI = {
    "auth_availability": "auth",
    "ws_session_establishment": "ws",
    "readiness_availability": "readiness",
}

ROUTING_REQUIRED_LABEL_KEYS = (
    "service",
    "component",
    "severity",
    "alert_class",
    "routing_key",
    "runbook_ref",
    "owner_team",
)

ALERT_NOTIFICATION_TARGET_BASELINE: dict[str, NotificationTargetSpec] = {
    "primary_oncall": NotificationTargetSpec(
        target_id="primary_oncall",
        target_class="pager",
        channel="pagerduty_primary",
        description="Primary on-call pager route for page-class alerts.",
    ),
    "secondary_oncall": NotificationTargetSpec(
        target_id="secondary_oncall",
        target_class="pager",
        channel="pagerduty_secondary",
        description="Escalation pager route for page-class alerts.",
    ),
    "ops_ticket_queue": NotificationTargetSpec(
        target_id="ops_ticket_queue",
        target_class="ticket",
        channel="ops_issue_tracker_queue",
        description="Non-paging operational ticket queue.",
    ),
    "dashboard_only": NotificationTargetSpec(
        target_id="dashboard_only",
        target_class="dashboard",
        channel="dashboard_only",
        description="Record-only route without operator notification.",
    ),
}


def _routing_key_for_severity(severity: str) -> str:
    if severity == "page":
        return "primary_oncall"
    if severity == "ticket":
        return "ops_ticket_queue"
    return "dashboard_only"


def _build_alert_routing_label_baseline() -> dict[str, AlertRoutingLabelSpec]:
    out: dict[str, AlertRoutingLabelSpec] = {}
    for alert_alias, alert_spec in sorted(SLO_ALERT_RULE_ALIAS_BASELINE.items()):
        component = _COMPONENT_BY_SLI[alert_spec.sli_key]
        out[alert_alias] = AlertRoutingLabelSpec(
            service=SERVICE_NAME,
            component=component,
            severity=alert_spec.severity,
            alert_class="slo_burn_rate",
            routing_key=_routing_key_for_severity(alert_spec.severity),
            runbook_ref=alert_spec.runbook_ref,
            owner_team=DEFAULT_OWNER_TEAM,
        )
    return out


def _build_alert_escalation_policy_baseline() -> dict[str, EscalationPolicySpec]:
    out: dict[str, EscalationPolicySpec] = {}
    for alert_alias, alert_spec in sorted(SLO_ALERT_RULE_ALIAS_BASELINE.items()):
        if alert_spec.severity == "page":
            out[alert_alias] = EscalationPolicySpec(
                alert_alias=alert_alias,
                severity=alert_spec.severity,
                notification_class="page",
                primary_target="primary_oncall",
                escalation_target="secondary_oncall",
                escalation_after_minutes=15,
            )
        elif alert_spec.severity == "ticket":
            out[alert_alias] = EscalationPolicySpec(
                alert_alias=alert_alias,
                severity=alert_spec.severity,
                notification_class="ticket",
                primary_target="ops_ticket_queue",
                escalation_target=None,
                escalation_after_minutes=None,
            )
        else:
            out[alert_alias] = EscalationPolicySpec(
                alert_alias=alert_alias,
                severity=alert_spec.severity,
                notification_class="info",
                primary_target="dashboard_only",
                escalation_target=None,
                escalation_after_minutes=None,
            )
    return out


def _build_runbook_ownership_baseline() -> dict[str, RunbookOwnershipSpec]:
    out: dict[str, RunbookOwnershipSpec] = {}
    for alert_alias, alert_spec in sorted(SLO_ALERT_RULE_ALIAS_BASELINE.items()):
        escalation_target = (
            "secondary_oncall" if alert_spec.severity == "page" else None
        )
        out[alert_alias] = RunbookOwnershipSpec(
            alert_alias=alert_alias,
            runbook_ref=alert_spec.runbook_ref,
            owner_team=DEFAULT_OWNER_TEAM,
            escalation_target=escalation_target,
        )
    return out


ALERT_ROUTING_LABEL_BASELINE = _build_alert_routing_label_baseline()
ALERT_ESCALATION_POLICY_BASELINE = _build_alert_escalation_policy_baseline()
ALERT_RUNBOOK_OWNERSHIP_BASELINE = _build_runbook_ownership_baseline()


def validate_reliability_alert_routing_baseline_contract() -> list[str]:
    errors: list[str] = []

    expected_aliases = set(SLO_ALERT_RULE_ALIAS_BASELINE.keys())

    if set(ALERT_ROUTING_LABEL_BASELINE.keys()) != expected_aliases:
        errors.append("ALERT_ROUTING_LABEL_BASELINE keys must match SLO_ALERT_RULE_ALIAS_BASELINE")
    if set(ALERT_ESCALATION_POLICY_BASELINE.keys()) != expected_aliases:
        errors.append("ALERT_ESCALATION_POLICY_BASELINE keys must match SLO_ALERT_RULE_ALIAS_BASELINE")
    if set(ALERT_RUNBOOK_OWNERSHIP_BASELINE.keys()) != expected_aliases:
        errors.append("ALERT_RUNBOOK_OWNERSHIP_BASELINE keys must match SLO_ALERT_RULE_ALIAS_BASELINE")

    for alert_alias, alert_spec in SLO_ALERT_RULE_ALIAS_BASELINE.items():
        routing_spec = ALERT_ROUTING_LABEL_BASELINE.get(alert_alias)
        if routing_spec is None:
            errors.append(f"{alert_alias}: missing routing label spec")
            continue

        routing_dict = routing_spec.__dict__
        if set(routing_dict.keys()) != set(ROUTING_REQUIRED_LABEL_KEYS):
            errors.append(f"{alert_alias}: routing labels must match required keys {ROUTING_REQUIRED_LABEL_KEYS}")

        if routing_spec.service != SERVICE_NAME:
            errors.append(f"{alert_alias}: service label must be {SERVICE_NAME}")

        expected_component = _COMPONENT_BY_SLI.get(alert_spec.sli_key)
        if routing_spec.component != expected_component:
            errors.append(
                f"{alert_alias}: component label mismatch, expected {expected_component}, got {routing_spec.component}"
            )

        if routing_spec.severity != alert_spec.severity:
            errors.append(
                f"{alert_alias}: severity label mismatch, expected {alert_spec.severity}, got {routing_spec.severity}"
            )

        if routing_spec.alert_class != "slo_burn_rate":
            errors.append(f"{alert_alias}: alert_class must be slo_burn_rate")

        if routing_spec.routing_key not in ALERT_NOTIFICATION_TARGET_BASELINE:
            errors.append(f"{alert_alias}: routing_key target is unknown: {routing_spec.routing_key}")

        if routing_spec.runbook_ref != alert_spec.runbook_ref:
            errors.append(
                f"{alert_alias}: runbook_ref mismatch, expected {alert_spec.runbook_ref}, got {routing_spec.runbook_ref}"
            )

        if not routing_spec.owner_team.strip():
            errors.append(f"{alert_alias}: owner_team must not be empty")

        escalation_spec = ALERT_ESCALATION_POLICY_BASELINE.get(alert_alias)
        if escalation_spec is None:
            errors.append(f"{alert_alias}: missing escalation policy spec")
            continue

        if escalation_spec.severity != alert_spec.severity:
            errors.append(
                f"{alert_alias}: escalation severity mismatch, expected {alert_spec.severity}, got {escalation_spec.severity}"
            )

        primary_target_spec = ALERT_NOTIFICATION_TARGET_BASELINE.get(escalation_spec.primary_target)
        if primary_target_spec is None:
            errors.append(f"{alert_alias}: unknown primary_target: {escalation_spec.primary_target}")
        else:
            if escalation_spec.severity == "page" and primary_target_spec.target_class != "pager":
                errors.append(f"{alert_alias}: page severity must route to pager primary target")
            if escalation_spec.severity == "ticket" and primary_target_spec.target_class == "pager":
                errors.append(f"{alert_alias}: ticket severity must not route to pager target")

        if escalation_spec.severity == "page":
            if escalation_spec.escalation_target is None:
                errors.append(f"{alert_alias}: page severity requires escalation_target")
            else:
                escalation_target_spec = ALERT_NOTIFICATION_TARGET_BASELINE.get(
                    escalation_spec.escalation_target
                )
                if escalation_target_spec is None:
                    errors.append(
                        f"{alert_alias}: escalation_target is unknown: {escalation_spec.escalation_target}"
                    )
                elif escalation_target_spec.target_class != "pager":
                    errors.append(f"{alert_alias}: page escalation_target must use pager target class")
            if escalation_spec.escalation_after_minutes is None:
                errors.append(f"{alert_alias}: page severity requires escalation_after_minutes")
        else:
            if escalation_spec.escalation_target is not None:
                errors.append(f"{alert_alias}: non-page severity must not have escalation_target")
            if escalation_spec.escalation_after_minutes is not None:
                errors.append(f"{alert_alias}: non-page severity must not have escalation_after_minutes")

        ownership_spec = ALERT_RUNBOOK_OWNERSHIP_BASELINE.get(alert_alias)
        if ownership_spec is None:
            errors.append(f"{alert_alias}: missing runbook ownership spec")
            continue

        if ownership_spec.runbook_ref != alert_spec.runbook_ref:
            errors.append(
                f"{alert_alias}: ownership runbook_ref mismatch, expected {alert_spec.runbook_ref}, got {ownership_spec.runbook_ref}"
            )

        if ownership_spec.owner_team != routing_spec.owner_team:
            errors.append(
                f"{alert_alias}: owner_team mismatch between routing and ownership specs"
            )

        if escalation_spec.severity == "page" and ownership_spec.escalation_target is None:
            errors.append(f"{alert_alias}: page severity ownership requires escalation_target")
        if escalation_spec.severity != "page" and ownership_spec.escalation_target is not None:
            errors.append(
                f"{alert_alias}: non-page severity ownership must not define escalation_target"
            )

    return errors

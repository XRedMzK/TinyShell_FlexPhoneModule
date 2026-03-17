from __future__ import annotations

from dataclasses import dataclass

from .reliability_alert_delivery_template_baseline import (
    ALERT_CONTACT_POINT_PAYLOAD_BASELINE,
    ALERT_DELIVERY_SCHEMA_BASELINE,
    ALERT_TEMPLATE_VARIABLE_BASELINE,
)
from .reliability_alert_routing_baseline import (
    ALERT_NOTIFICATION_TARGET_BASELINE,
    ALERT_ROUTING_LABEL_BASELINE,
)
from .reliability_alert_suppression_baseline import (
    ALERT_GROUPING_BASELINE,
    ALERT_GROUP_TIMING_BASELINE,
    ALERT_INHIBITION_POLICY_BASELINE,
    ALERT_SILENCE_POLICY_BASELINE,
)


@dataclass(frozen=True)
class AlertmanagerRouteExportSpec:
    alert_alias: str
    matchers: dict[str, str]
    receiver: str
    group_by: tuple[str, ...]
    group_wait: str
    group_interval: str
    repeat_interval: str


@dataclass(frozen=True)
class AlertmanagerReceiverExportSpec:
    receiver_id: str
    target_class: str
    contact_point_ref: str
    template_ref: str


@dataclass(frozen=True)
class AlertmanagerInhibitExportSpec:
    rule_id: str
    source_matchers: dict[str, str]
    target_matchers: dict[str, str]
    equal_labels: tuple[str, ...]


@dataclass(frozen=True)
class AlertmanagerTemplateExportSpec:
    template_id: str
    contact_point: str
    title_template: str
    body_template: str
    required_variables: tuple[str, ...]


@dataclass(frozen=True)
class GrafanaNotificationPolicyNodeExportSpec:
    policy_id: str
    parent_policy_id: str | None
    matchers: dict[str, str]
    contact_point_ref: str
    group_by: tuple[str, ...]
    group_wait: str
    group_interval: str
    repeat_interval: str
    continue_routing: bool


@dataclass(frozen=True)
class GrafanaContactPointExportSpec:
    contact_point_id: str
    target_class: str
    endpoint_ref: str
    template_ref: str


@dataclass(frozen=True)
class GrafanaMuteTimingExportSpec:
    timing_id: str
    timezone: str
    intervals: tuple[str, ...]
    allowed_severities: tuple[str, ...]


@dataclass(frozen=True)
class GrafanaTemplateExportSpec:
    template_id: str
    contact_point: str
    title_template: str
    body_template: str
    required_variables: tuple[str, ...]


_TARGET_TO_CONTACT_POINT = {
    "primary_oncall": "slack",
    "secondary_oncall": "slack",
    "ops_ticket_queue": "email",
    "dashboard_only": "webhook",
}


def _policy_node_id(alert_alias: str) -> str:
    return f"policy_{alert_alias.replace(':', '_')}"


def _template_id(contact_point: str) -> str:
    return f"template_{contact_point}"


STATIC_SUPPRESSION_EXPORT_BASELINE = {
    "includes": ("grouping", "inhibition", "mute_timing"),
    "runtime_managed": ("silence",),
}

RUNTIME_MANAGED_SILENCE_BASELINE = tuple(
    sorted(
        policy_id
        for policy_id, policy in ALERT_SILENCE_POLICY_BASELINE.items()
        if policy.policy_type == "silence"
    )
)


def _build_template_exports() -> tuple[
    dict[str, AlertmanagerTemplateExportSpec],
    dict[str, GrafanaTemplateExportSpec],
]:
    alertmanager_templates: dict[str, AlertmanagerTemplateExportSpec] = {}
    grafana_templates: dict[str, GrafanaTemplateExportSpec] = {}

    for contact_point, payload_spec in sorted(ALERT_CONTACT_POINT_PAYLOAD_BASELINE.items()):
        template_id = _template_id(contact_point)
        required_variables = tuple(
            dict.fromkeys(payload_spec.required_group_variables + payload_spec.required_alert_variables)
        )

        alertmanager_templates[template_id] = AlertmanagerTemplateExportSpec(
            template_id=template_id,
            contact_point=contact_point,
            title_template=payload_spec.title_template,
            body_template=payload_spec.body_template,
            required_variables=required_variables,
        )
        grafana_templates[template_id] = GrafanaTemplateExportSpec(
            template_id=template_id,
            contact_point=contact_point,
            title_template=payload_spec.title_template,
            body_template=payload_spec.body_template,
            required_variables=required_variables,
        )

    return alertmanager_templates, grafana_templates


ALERTMANAGER_TEMPLATE_EXPORT_BASELINE, GRAFANA_TEMPLATE_EXPORT_BASELINE = _build_template_exports()

ALERTMANAGER_RECEIVER_EXPORT_BASELINE: dict[str, AlertmanagerReceiverExportSpec] = {
    receiver_id: AlertmanagerReceiverExportSpec(
        receiver_id=receiver_id,
        target_class=target_spec.target_class,
        contact_point_ref=_TARGET_TO_CONTACT_POINT[receiver_id],
        template_ref=_template_id(_TARGET_TO_CONTACT_POINT[receiver_id]),
    )
    for receiver_id, target_spec in sorted(ALERT_NOTIFICATION_TARGET_BASELINE.items())
}


def _build_alertmanager_route_exports() -> dict[str, AlertmanagerRouteExportSpec]:
    out: dict[str, AlertmanagerRouteExportSpec] = {}
    for alert_alias, routing_spec in sorted(ALERT_ROUTING_LABEL_BASELINE.items()):
        grouping_spec = ALERT_GROUPING_BASELINE[alert_alias]
        timing_spec = ALERT_GROUP_TIMING_BASELINE[routing_spec.severity]
        out[alert_alias] = AlertmanagerRouteExportSpec(
            alert_alias=alert_alias,
            matchers={
                "alert_alias": alert_alias,
                "service": routing_spec.service,
                "component": routing_spec.component,
                "severity": routing_spec.severity,
                "alert_class": routing_spec.alert_class,
            },
            receiver=routing_spec.routing_key,
            group_by=grouping_spec.group_by,
            group_wait=timing_spec.group_wait,
            group_interval=timing_spec.group_interval,
            repeat_interval=timing_spec.repeat_interval,
        )
    return out


ALERTMANAGER_ROUTE_EXPORT_BASELINE = _build_alertmanager_route_exports()

ALERTMANAGER_INHIBIT_EXPORT_BASELINE: dict[str, AlertmanagerInhibitExportSpec] = {
    rule_id: AlertmanagerInhibitExportSpec(
        rule_id=rule.rule_id,
        source_matchers=rule.source_matchers,
        target_matchers=rule.target_matchers,
        equal_labels=rule.equal_labels,
    )
    for rule_id, rule in sorted(ALERT_INHIBITION_POLICY_BASELINE.items())
}


ALERTMANAGER_EXPORT_BASELINE = {
    "root_receiver": "dashboard_only",
    "routes": ALERTMANAGER_ROUTE_EXPORT_BASELINE,
    "receivers": ALERTMANAGER_RECEIVER_EXPORT_BASELINE,
    "inhibit_rules": ALERTMANAGER_INHIBIT_EXPORT_BASELINE,
    "templates": ALERTMANAGER_TEMPLATE_EXPORT_BASELINE,
}


def _build_grafana_policy_tree_exports() -> dict[str, GrafanaNotificationPolicyNodeExportSpec]:
    tree: dict[str, GrafanaNotificationPolicyNodeExportSpec] = {}
    root_timing = ALERT_GROUP_TIMING_BASELINE["info"]

    tree["root"] = GrafanaNotificationPolicyNodeExportSpec(
        policy_id="root",
        parent_policy_id=None,
        matchers={},
        contact_point_ref="dashboard_only",
        group_by=("service", "severity"),
        group_wait=root_timing.group_wait,
        group_interval=root_timing.group_interval,
        repeat_interval=root_timing.repeat_interval,
        continue_routing=False,
    )

    for alert_alias, routing_spec in sorted(ALERT_ROUTING_LABEL_BASELINE.items()):
        grouping_spec = ALERT_GROUPING_BASELINE[alert_alias]
        timing_spec = ALERT_GROUP_TIMING_BASELINE[routing_spec.severity]
        policy_id = _policy_node_id(alert_alias)
        tree[policy_id] = GrafanaNotificationPolicyNodeExportSpec(
            policy_id=policy_id,
            parent_policy_id="root",
            matchers={
                "alert_alias": alert_alias,
                "service": routing_spec.service,
                "component": routing_spec.component,
                "severity": routing_spec.severity,
                "alert_class": routing_spec.alert_class,
            },
            contact_point_ref=routing_spec.routing_key,
            group_by=grouping_spec.group_by,
            group_wait=timing_spec.group_wait,
            group_interval=timing_spec.group_interval,
            repeat_interval=timing_spec.repeat_interval,
            continue_routing=False,
        )

    return tree


GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE = _build_grafana_policy_tree_exports()

GRAFANA_CONTACT_POINT_EXPORT_BASELINE: dict[str, GrafanaContactPointExportSpec] = {
    contact_point_id: GrafanaContactPointExportSpec(
        contact_point_id=contact_point_id,
        target_class=target_spec.target_class,
        endpoint_ref=_TARGET_TO_CONTACT_POINT[contact_point_id],
        template_ref=_template_id(_TARGET_TO_CONTACT_POINT[contact_point_id]),
    )
    for contact_point_id, target_spec in sorted(ALERT_NOTIFICATION_TARGET_BASELINE.items())
}

GRAFANA_MUTE_TIMING_EXPORT_BASELINE: dict[str, GrafanaMuteTimingExportSpec] = {
    policy_id: GrafanaMuteTimingExportSpec(
        timing_id=policy_id,
        timezone="UTC",
        intervals=("Mon-Sun 00:00-06:00",),
        allowed_severities=policy.allowed_severities,
    )
    for policy_id, policy in sorted(ALERT_SILENCE_POLICY_BASELINE.items())
    if policy.policy_type == "mute_timing"
}

GRAFANA_EXPORT_BASELINE = {
    "policy_tree": GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE,
    "contact_points": GRAFANA_CONTACT_POINT_EXPORT_BASELINE,
    "mute_timings": GRAFANA_MUTE_TIMING_EXPORT_BASELINE,
    "templates": GRAFANA_TEMPLATE_EXPORT_BASELINE,
}


def validate_reliability_alert_policy_export_baseline_contract() -> list[str]:
    errors: list[str] = []

    expected_alert_aliases = set(ALERT_ROUTING_LABEL_BASELINE.keys())

    if set(ALERTMANAGER_ROUTE_EXPORT_BASELINE.keys()) != expected_alert_aliases:
        errors.append("ALERTMANAGER_ROUTE_EXPORT_BASELINE keys must match alert aliases")

    if set(ALERT_DELIVERY_SCHEMA_BASELINE.keys()) != expected_alert_aliases:
        errors.append("ALERT_DELIVERY_SCHEMA_BASELINE keys must match alert aliases")

    for alert_alias, route_spec in ALERTMANAGER_ROUTE_EXPORT_BASELINE.items():
        routing_spec = ALERT_ROUTING_LABEL_BASELINE[alert_alias]
        grouping_spec = ALERT_GROUPING_BASELINE[alert_alias]
        timing_spec = ALERT_GROUP_TIMING_BASELINE[routing_spec.severity]

        if route_spec.receiver != routing_spec.routing_key:
            errors.append(
                f"{alert_alias}: route receiver mismatch, expected {routing_spec.routing_key}, got {route_spec.receiver}"
            )

        if route_spec.group_by != grouping_spec.group_by:
            errors.append(f"{alert_alias}: route group_by must match ALERT_GROUPING_BASELINE")

        if route_spec.group_wait != timing_spec.group_wait:
            errors.append(f"{alert_alias}: route group_wait mismatch")
        if route_spec.group_interval != timing_spec.group_interval:
            errors.append(f"{alert_alias}: route group_interval mismatch")
        if route_spec.repeat_interval != timing_spec.repeat_interval:
            errors.append(f"{alert_alias}: route repeat_interval mismatch")

        for matcher_key, expected_value in {
            "alert_alias": alert_alias,
            "service": routing_spec.service,
            "component": routing_spec.component,
            "severity": routing_spec.severity,
            "alert_class": routing_spec.alert_class,
        }.items():
            if route_spec.matchers.get(matcher_key) != expected_value:
                errors.append(
                    f"{alert_alias}: route matcher '{matcher_key}' mismatch, "
                    f"expected {expected_value}, got {route_spec.matchers.get(matcher_key)}"
                )

    for receiver_id, receiver_spec in ALERTMANAGER_RECEIVER_EXPORT_BASELINE.items():
        if receiver_id not in ALERT_NOTIFICATION_TARGET_BASELINE:
            errors.append(f"{receiver_id}: unknown receiver in ALERTMANAGER_RECEIVER_EXPORT_BASELINE")
            continue

        if receiver_spec.contact_point_ref not in ALERT_CONTACT_POINT_PAYLOAD_BASELINE:
            errors.append(
                f"{receiver_id}: contact_point_ref missing in ALERT_CONTACT_POINT_PAYLOAD_BASELINE: "
                f"{receiver_spec.contact_point_ref}"
            )
        if receiver_spec.template_ref not in ALERTMANAGER_TEMPLATE_EXPORT_BASELINE:
            errors.append(
                f"{receiver_id}: template_ref missing in ALERTMANAGER_TEMPLATE_EXPORT_BASELINE: "
                f"{receiver_spec.template_ref}"
            )

    if set(ALERTMANAGER_INHIBIT_EXPORT_BASELINE.keys()) != set(ALERT_INHIBITION_POLICY_BASELINE.keys()):
        errors.append("ALERTMANAGER_INHIBIT_EXPORT_BASELINE must match ALERT_INHIBITION_POLICY_BASELINE")
    for rule_id, rule_spec in ALERTMANAGER_INHIBIT_EXPORT_BASELINE.items():
        source_severity = rule_spec.source_matchers.get("severity")
        target_severity = rule_spec.target_matchers.get("severity")
        if source_severity == "page" and target_severity == "page":
            errors.append(f"{rule_id}: export inhibition must not allow page -> page suppression")

    if "root" not in GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE:
        errors.append("GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE must include root node")

    alias_policy_nodes: dict[str, GrafanaNotificationPolicyNodeExportSpec] = {}
    for policy_id, node in GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE.items():
        if policy_id == "root":
            if node.parent_policy_id is not None:
                errors.append("Grafana root policy must not have parent_policy_id")
            continue

        if node.parent_policy_id is None:
            errors.append(f"{policy_id}: non-root policy must define parent_policy_id")
        elif node.parent_policy_id not in GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE:
            errors.append(f"{policy_id}: parent_policy_id does not exist: {node.parent_policy_id}")

        alert_alias = node.matchers.get("alert_alias")
        if not alert_alias:
            errors.append(f"{policy_id}: policy node must include alert_alias matcher")
            continue

        alias_policy_nodes[alert_alias] = node

    if set(alias_policy_nodes.keys()) != expected_alert_aliases:
        errors.append("Grafana policy tree must include node for each alert alias")

    for alert_alias, node in alias_policy_nodes.items():
        routing_spec = ALERT_ROUTING_LABEL_BASELINE[alert_alias]
        grouping_spec = ALERT_GROUPING_BASELINE[alert_alias]
        timing_spec = ALERT_GROUP_TIMING_BASELINE[routing_spec.severity]

        if node.contact_point_ref != routing_spec.routing_key:
            errors.append(
                f"{alert_alias}: grafana policy contact_point_ref mismatch, "
                f"expected {routing_spec.routing_key}, got {node.contact_point_ref}"
            )
        if node.group_by != grouping_spec.group_by:
            errors.append(f"{alert_alias}: grafana policy group_by must match ALERT_GROUPING_BASELINE")
        if node.group_wait != timing_spec.group_wait:
            errors.append(f"{alert_alias}: grafana policy group_wait mismatch")
        if node.group_interval != timing_spec.group_interval:
            errors.append(f"{alert_alias}: grafana policy group_interval mismatch")
        if node.repeat_interval != timing_spec.repeat_interval:
            errors.append(f"{alert_alias}: grafana policy repeat_interval mismatch")

        for matcher_key, expected_value in {
            "alert_alias": alert_alias,
            "service": routing_spec.service,
            "component": routing_spec.component,
            "severity": routing_spec.severity,
            "alert_class": routing_spec.alert_class,
        }.items():
            if node.matchers.get(matcher_key) != expected_value:
                errors.append(
                    f"{alert_alias}: grafana matcher '{matcher_key}' mismatch, expected {expected_value}, got {node.matchers.get(matcher_key)}"
                )

    if set(GRAFANA_CONTACT_POINT_EXPORT_BASELINE.keys()) != set(ALERT_NOTIFICATION_TARGET_BASELINE.keys()):
        errors.append("GRAFANA_CONTACT_POINT_EXPORT_BASELINE keys must match ALERT_NOTIFICATION_TARGET_BASELINE")
    for contact_point_id, spec in GRAFANA_CONTACT_POINT_EXPORT_BASELINE.items():
        if spec.endpoint_ref not in ALERT_CONTACT_POINT_PAYLOAD_BASELINE:
            errors.append(
                f"{contact_point_id}: endpoint_ref missing in ALERT_CONTACT_POINT_PAYLOAD_BASELINE: {spec.endpoint_ref}"
            )
        if spec.template_ref not in GRAFANA_TEMPLATE_EXPORT_BASELINE:
            errors.append(
                f"{contact_point_id}: template_ref missing in GRAFANA_TEMPLATE_EXPORT_BASELINE: {spec.template_ref}"
            )

    expected_mute_timing_ids = {
        policy_id
        for policy_id, policy in ALERT_SILENCE_POLICY_BASELINE.items()
        if policy.policy_type == "mute_timing"
    }
    if set(GRAFANA_MUTE_TIMING_EXPORT_BASELINE.keys()) != expected_mute_timing_ids:
        errors.append("GRAFANA_MUTE_TIMING_EXPORT_BASELINE keys must match mute_timing policies")

    expected_runtime_silence_ids = {
        policy_id
        for policy_id, policy in ALERT_SILENCE_POLICY_BASELINE.items()
        if policy.policy_type == "silence"
    }
    if set(RUNTIME_MANAGED_SILENCE_BASELINE) != expected_runtime_silence_ids:
        errors.append("RUNTIME_MANAGED_SILENCE_BASELINE must match silence policy ids")

    if STATIC_SUPPRESSION_EXPORT_BASELINE.get("runtime_managed") != ("silence",):
        errors.append("STATIC_SUPPRESSION_EXPORT_BASELINE.runtime_managed must be ('silence',)")

    if set(ALERTMANAGER_TEMPLATE_EXPORT_BASELINE.keys()) != set(GRAFANA_TEMPLATE_EXPORT_BASELINE.keys()):
        errors.append("Alertmanager/Grafana template export keys must match")

    for template_id, template_spec in ALERTMANAGER_TEMPLATE_EXPORT_BASELINE.items():
        for variable in template_spec.required_variables:
            if variable not in ALERT_TEMPLATE_VARIABLE_BASELINE:
                errors.append(
                    f"{template_id}: required variable is not defined in ALERT_TEMPLATE_VARIABLE_BASELINE: {variable}"
                )

    for template_id, template_spec in GRAFANA_TEMPLATE_EXPORT_BASELINE.items():
        for variable in template_spec.required_variables:
            if variable not in ALERT_TEMPLATE_VARIABLE_BASELINE:
                errors.append(
                    f"{template_id}: required variable is not defined in ALERT_TEMPLATE_VARIABLE_BASELINE: {variable}"
                )

    return errors

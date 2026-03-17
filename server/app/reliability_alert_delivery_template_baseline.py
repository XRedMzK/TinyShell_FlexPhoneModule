from __future__ import annotations

from dataclasses import dataclass

from .reliability_alert_policy_mapping import SLO_ALERT_RULE_ALIAS_BASELINE
from .reliability_alert_suppression_baseline import ALERT_GROUPING_BASELINE


@dataclass(frozen=True)
class AlertDeliverySchemaSpec:
    alert_alias: str
    severity: str
    required_labels: tuple[str, ...]
    required_annotations: tuple[str, ...]
    required_group_fields: tuple[str, ...]
    required_alert_fields: tuple[str, ...]
    runbook_link_required: bool


@dataclass(frozen=True)
class RunbookLinkFormatSpec:
    mode: str
    ref_prefix: str
    url_template: str
    required_for_severity: tuple[str, ...]


@dataclass(frozen=True)
class ContactPointPayloadSpec:
    contact_point: str
    required_group_variables: tuple[str, ...]
    required_alert_variables: tuple[str, ...]
    title_template: str
    body_template: str


GROUP_PAYLOAD_FIELDS = (
    "receiver",
    "status",
    "group_labels",
    "common_labels",
    "common_annotations",
    "external_url",
)

ALERT_PAYLOAD_FIELDS = (
    "status",
    "labels",
    "annotations",
    "starts_at",
    "ends_at",
    "generator_url",
    "fingerprint",
)

REQUIRED_ALERT_LABELS = (
    "alertname",
    "severity",
    "service",
    "component",
    "alert_class",
    "owner_team",
)

REQUIRED_ALERT_ANNOTATIONS = (
    "summary",
    "description",
    "runbook_ref",
    "runbook_url",
)

ALERT_TEMPLATE_VARIABLE_BASELINE = {
    # Group-level variables (Prometheus Data object).
    "group.receiver": "Data.Receiver",
    "group.status": "Data.Status",
    "group.group_labels": "Data.GroupLabels",
    "group.common_labels": "Data.CommonLabels",
    "group.common_annotations": "Data.CommonAnnotations",
    "group.external_url": "Data.ExternalURL",
    # Per-alert variables (Prometheus Alert object).
    "alert.status": "Alert.Status",
    "alert.labels": "Alert.Labels",
    "alert.annotations": "Alert.Annotations",
    "alert.starts_at": "Alert.StartsAt",
    "alert.ends_at": "Alert.EndsAt",
    "alert.generator_url": "Alert.GeneratorURL",
    "alert.fingerprint": "Alert.Fingerprint",
    # Canonical convenience aliases for contact-point templates.
    "alert.summary": "Alert.Annotations.summary",
    "alert.description": "Alert.Annotations.description",
    "alert.runbook_url": "Alert.Annotations.runbook_url",
}

ALERT_RUNBOOK_LINK_FORMAT_BASELINE = RunbookLinkFormatSpec(
    mode="prefer_annotation_url_fallback_ref",
    ref_prefix="docs/runbooks/slo/",
    url_template="https://runbooks.flexphone.local/{runbook_ref}",
    required_for_severity=("page", "ticket"),
)

ALERT_CONTACT_POINT_PAYLOAD_BASELINE: dict[str, ContactPointPayloadSpec] = {
    "slack": ContactPointPayloadSpec(
        contact_point="slack",
        required_group_variables=("group.status", "group.receiver", "group.group_labels"),
        required_alert_variables=(
            "alert.summary",
            "alert.description",
            "alert.runbook_url",
            "alert.status",
        ),
        title_template='[{{ .Status | toUpper }}] {{ .CommonLabels.severity }} {{ .GroupLabels.alertname }}',
        body_template='{{ range .Alerts }}{{ .Annotations.summary }} | runbook={{ .Annotations.runbook_url }}{{ end }}',
    ),
    "email": ContactPointPayloadSpec(
        contact_point="email",
        required_group_variables=("group.status", "group.receiver"),
        required_alert_variables=(
            "alert.summary",
            "alert.description",
            "alert.runbook_url",
        ),
        title_template='[{{ .Status | toUpper }}] {{ .CommonLabels.service }} {{ .GroupLabels.alertname }}',
        body_template='{{ range .Alerts }}summary={{ .Annotations.summary }} desc={{ .Annotations.description }}{{ end }}',
    ),
    "webhook": ContactPointPayloadSpec(
        contact_point="webhook",
        required_group_variables=(
            "group.status",
            "group.receiver",
            "group.group_labels",
            "group.common_labels",
        ),
        required_alert_variables=(
            "alert.status",
            "alert.labels",
            "alert.annotations",
            "alert.fingerprint",
            "alert.runbook_url",
        ),
        title_template='{{ .Status }} {{ .GroupLabels.alertname }}',
        body_template='alerts={{ len .Alerts }}',
    ),
}


def _build_alert_delivery_schema_baseline() -> dict[str, AlertDeliverySchemaSpec]:
    out: dict[str, AlertDeliverySchemaSpec] = {}
    for alert_alias, alert_spec in sorted(SLO_ALERT_RULE_ALIAS_BASELINE.items()):
        runbook_link_required = alert_spec.severity in ALERT_RUNBOOK_LINK_FORMAT_BASELINE.required_for_severity
        out[alert_alias] = AlertDeliverySchemaSpec(
            alert_alias=alert_alias,
            severity=alert_spec.severity,
            required_labels=REQUIRED_ALERT_LABELS,
            required_annotations=REQUIRED_ALERT_ANNOTATIONS,
            required_group_fields=GROUP_PAYLOAD_FIELDS,
            required_alert_fields=ALERT_PAYLOAD_FIELDS,
            runbook_link_required=runbook_link_required,
        )
    return out


ALERT_DELIVERY_SCHEMA_BASELINE = _build_alert_delivery_schema_baseline()


def validate_reliability_alert_delivery_template_baseline_contract() -> list[str]:
    errors: list[str] = []

    expected_alert_aliases = set(SLO_ALERT_RULE_ALIAS_BASELINE.keys())
    if set(ALERT_DELIVERY_SCHEMA_BASELINE.keys()) != expected_alert_aliases:
        errors.append("ALERT_DELIVERY_SCHEMA_BASELINE keys must match SLO_ALERT_RULE_ALIAS_BASELINE")

    if set(ALERT_GROUPING_BASELINE.keys()) != expected_alert_aliases:
        errors.append("ALERT_GROUPING_BASELINE keys must match SLO_ALERT_RULE_ALIAS_BASELINE for grouped rendering")

    required_variable_keys = {
        "group.receiver",
        "group.status",
        "group.group_labels",
        "group.common_labels",
        "group.common_annotations",
        "group.external_url",
        "alert.status",
        "alert.labels",
        "alert.annotations",
        "alert.starts_at",
        "alert.ends_at",
        "alert.generator_url",
        "alert.fingerprint",
        "alert.summary",
        "alert.description",
        "alert.runbook_url",
    }
    missing_variables = required_variable_keys - set(ALERT_TEMPLATE_VARIABLE_BASELINE.keys())
    for variable_name in sorted(missing_variables):
        errors.append(f"Missing required template variable mapping: {variable_name}")

    if ALERT_RUNBOOK_LINK_FORMAT_BASELINE.mode != "prefer_annotation_url_fallback_ref":
        errors.append(
            "ALERT_RUNBOOK_LINK_FORMAT_BASELINE.mode must be prefer_annotation_url_fallback_ref"
        )
    if "{runbook_ref}" not in ALERT_RUNBOOK_LINK_FORMAT_BASELINE.url_template:
        errors.append("ALERT_RUNBOOK_LINK_FORMAT_BASELINE.url_template must include {runbook_ref}")
    if not ALERT_RUNBOOK_LINK_FORMAT_BASELINE.ref_prefix.startswith("docs/runbooks/slo/"):
        errors.append("ALERT_RUNBOOK_LINK_FORMAT_BASELINE.ref_prefix must start with docs/runbooks/slo/")

    if not ALERT_CONTACT_POINT_PAYLOAD_BASELINE:
        errors.append("ALERT_CONTACT_POINT_PAYLOAD_BASELINE must not be empty")

    for alias, schema in ALERT_DELIVERY_SCHEMA_BASELINE.items():
        if schema.alert_alias != alias:
            errors.append(f"{alias}: alert_alias field must match dictionary key")

        rule_spec = SLO_ALERT_RULE_ALIAS_BASELINE.get(alias)
        if rule_spec is None:
            errors.append(f"{alias}: missing rule spec in SLO_ALERT_RULE_ALIAS_BASELINE")
            continue

        if schema.severity != rule_spec.severity:
            errors.append(
                f"{alias}: severity mismatch, expected {rule_spec.severity}, got {schema.severity}"
            )

        if tuple(schema.required_labels) != REQUIRED_ALERT_LABELS:
            errors.append(f"{alias}: required_labels must match REQUIRED_ALERT_LABELS")
        if tuple(schema.required_annotations) != REQUIRED_ALERT_ANNOTATIONS:
            errors.append(f"{alias}: required_annotations must match REQUIRED_ALERT_ANNOTATIONS")
        if tuple(schema.required_group_fields) != GROUP_PAYLOAD_FIELDS:
            errors.append(f"{alias}: required_group_fields must match GROUP_PAYLOAD_FIELDS")
        if tuple(schema.required_alert_fields) != ALERT_PAYLOAD_FIELDS:
            errors.append(f"{alias}: required_alert_fields must match ALERT_PAYLOAD_FIELDS")

        expected_runbook_required = (
            rule_spec.severity in ALERT_RUNBOOK_LINK_FORMAT_BASELINE.required_for_severity
        )
        if schema.runbook_link_required != expected_runbook_required:
            errors.append(
                f"{alias}: runbook_link_required mismatch for severity {rule_spec.severity}"
            )

        if schema.runbook_link_required and not rule_spec.runbook_ref.startswith(
            ALERT_RUNBOOK_LINK_FORMAT_BASELINE.ref_prefix
        ):
            errors.append(
                f"{alias}: runbook_ref must start with {ALERT_RUNBOOK_LINK_FORMAT_BASELINE.ref_prefix}"
            )

    for contact_point, payload_spec in ALERT_CONTACT_POINT_PAYLOAD_BASELINE.items():
        if payload_spec.contact_point != contact_point:
            errors.append(f"{contact_point}: contact_point field must match dictionary key")

        for variable_name in payload_spec.required_group_variables:
            if variable_name not in ALERT_TEMPLATE_VARIABLE_BASELINE:
                errors.append(
                    f"{contact_point}: unknown required_group_variable: {variable_name}"
                )
            elif not variable_name.startswith("group."):
                errors.append(
                    f"{contact_point}: required_group_variables must use group.* keys: {variable_name}"
                )

        for variable_name in payload_spec.required_alert_variables:
            if variable_name not in ALERT_TEMPLATE_VARIABLE_BASELINE:
                errors.append(
                    f"{contact_point}: unknown required_alert_variable: {variable_name}"
                )
            elif not variable_name.startswith("alert."):
                errors.append(
                    f"{contact_point}: required_alert_variables must use alert.* keys: {variable_name}"
                )

        if not payload_spec.title_template.strip():
            errors.append(f"{contact_point}: title_template must not be empty")
        if not payload_spec.body_template.strip():
            errors.append(f"{contact_point}: body_template must not be empty")

    return errors

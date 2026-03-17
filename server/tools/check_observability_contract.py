from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
DOC_18_1_PATH = ROOT.parent / "docs" / "step18-observability-hardening-baseline.md"
DOC_18_3_PATH = ROOT.parent / "docs" / "step18-signal-correlation-triage-baseline.md"
DOC_18_4_PATH = ROOT.parent / "docs" / "step18-dashboard-alert-mapping-baseline.md"
DOC_19_1_PATH = ROOT.parent / "docs" / "step19-reliability-slo-alerting-baseline.md"
DOC_19_2_PATH = ROOT.parent / "docs" / "step19-slo-query-alert-policy-hardening-baseline.md"
DOC_19_3_PATH = ROOT.parent / "docs" / "step19-alert-routing-escalation-baseline.md"
DOC_19_4_PATH = ROOT.parent / "docs" / "step19-alert-suppression-grouping-baseline.md"
DOC_19_5_PATH = ROOT.parent / "docs" / "step19-alert-delivery-template-baseline.md"
DOC_19_6_PATH = ROOT.parent / "docs" / "step19-alertmanager-grafana-policy-export-baseline.md"
ENV_EXAMPLE = ROOT / ".env.example"

REASON_RE = re.compile(r"^[a-z][a-z0-9_]*$")
EVENT_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+$")
COUNTER_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_/{@}-]+)+$")

REQUIRED_ENV_KEYS = (
    "FLEXPHONE_OTEL_EXPORTER",
    "FLEXPHONE_OTEL_SERVICE_NAME",
    "FLEXPHONE_OTEL_OTLP_ENDPOINT",
)

REQUIRED_DOC_18_1_PHRASES = (
    "## Signals Scope",
    "## Invariants",
    "### Resource Fields",
    "### Correlation Fields",
    "### Naming Surface",
    "## Build-Level Contract Check",
)

REQUIRED_DOC_18_3_PHRASES = (
    "## Correlation Contract",
    "### Always Required",
    "### Required When Active Span Exists",
    "### Required For Reject/Error/Degraded Events",
    "## Dashboard/Triage Mapping Baseline",
    "## Build-Level Validation",
)

REQUIRED_DOC_18_4_PHRASES = (
    "## Dashboard Query Baseline",
    "## Alert Mapping Baseline",
    "## Recording Rule Naming Baseline",
    "## Build-Level Validation",
)

REQUIRED_DOC_19_1_PHRASES = (
    "## SLI/SLO Scope",
    "## Reliability vs Security Boundary",
    "## Symptom-Based Alerting Invariants",
    "## Burn-Rate Policy Baseline",
    "## Baseline Mapping Registry",
    "## Build-Level Validation",
)

REQUIRED_DOC_19_2_PHRASES = (
    "## Recording Rule Alias Baseline",
    "## Alert Rule Alias Baseline",
    "## Severity/Action Mapping",
    "## Runbook Linkage",
    "## Invariants",
    "## Build-Level Validation",
)

REQUIRED_DOC_19_3_PHRASES = (
    "## Routing Label Contract",
    "## Notification Target Classes",
    "## Escalation Policy Baseline",
    "## Runbook Ownership Baseline",
    "## Invariants",
    "## Build-Level Validation",
)

REQUIRED_DOC_19_4_PHRASES = (
    "## Grouping Baseline",
    "## Group Timing Controls",
    "## Inhibition Policy Baseline",
    "## Silence / Mute Policy Baseline",
    "## Invariants",
    "## Build-Level Validation",
)

REQUIRED_DOC_19_5_PHRASES = (
    "## Annotation & Label Schema Baseline",
    "## Contact-Point Template Variable Contract",
    "## Grouped Notification Rendering Rules",
    "## Runbook Link Formatting Baseline",
    "## Contact-Point Payload Baseline",
    "## Build-Level Validation",
)

REQUIRED_DOC_19_6_PHRASES = (
    "## Alertmanager Export Surface",
    "## Grafana Export Surface",
    "## Policy Tree Completeness",
    "## Static vs Runtime-Managed Suppression",
    "## Template Export Compatibility",
    "## Build-Level Validation",
)

REQUIRED_LOG_KEYS = {
    "ts",
    "level",
    "service",
    "env",
    "event",
    "message",
    "request_id",
    "trace_id",
    "span_id",
    "route",
    "method",
    "component",
    "reason_code",
    "reason_class",
}

REQUIRED_SENSITIVE_KEYS = {
    "access_token",
    "authorization",
    "challenge",
    "password",
    "private_key",
    "secret",
    "signature",
    "token",
}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _load_ast(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _check_env_surface(errors: list[str]) -> None:
    if not ENV_EXAMPLE.exists():
        _fail(errors, f"Missing env example file: {ENV_EXAMPLE}")
        return

    env_text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for key in REQUIRED_ENV_KEYS:
        if key not in env_text:
            _fail(errors, f"Missing required env key in .env.example: {key}")


def _check_doc(path: Path, required_phrases: tuple[str, ...], *, label: str, errors: list[str]) -> None:
    if not path.exists():
        _fail(errors, f"Missing {label}: {path}")
        return

    doc_text = path.read_text(encoding="utf-8")
    for phrase in required_phrases:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in {label}: {phrase}")


def _check_tracing_resource(errors: list[str]) -> None:
    path = APP_DIR / "tracing.py"
    text = path.read_text(encoding="utf-8")

    # Contract baseline requires service.name as resource field.
    if 'Resource.create({"service.name": settings.otel_service_name})' not in text:
        _fail(errors, "Tracing resource must include service.name from settings.otel_service_name")


def _extract_set_constant(module: ast.AST, name: str) -> set[str]:
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = node.value
                    if isinstance(value, ast.Set):
                        out: set[str] = set()
                        for element in value.elts:
                            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                                out.add(element.value)
                        return out
    return set()


def _extract_payload_keys(module: ast.AST) -> set[str]:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "log_event":
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Assign):
                if any(isinstance(t, ast.Name) and t.id == "payload" for t in inner.targets):
                    if isinstance(inner.value, ast.Dict):
                        keys: set[str] = set()
                        for key in inner.value.keys:
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                keys.add(key.value)
                        return keys
            if isinstance(inner, ast.AnnAssign):
                if isinstance(inner.target, ast.Name) and inner.target.id == "payload":
                    if isinstance(inner.value, ast.Dict):
                        keys: set[str] = set()
                        for key in inner.value.keys:
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                keys.add(key.value)
                        return keys
    return set()


def _check_operational_logging_contract(errors: list[str]) -> None:
    path = APP_DIR / "operational_logging.py"
    module = _load_ast(path)

    sensitive_keys = _extract_set_constant(module, "_SENSITIVE_KEYS")
    missing_sensitive = REQUIRED_SENSITIVE_KEYS - sensitive_keys
    for key in sorted(missing_sensitive):
        _fail(errors, f"Missing sensitive key in operational logging redaction set: {key}")

    payload_keys = _extract_payload_keys(module)
    missing_payload_keys = REQUIRED_LOG_KEYS - payload_keys
    for key in sorted(missing_payload_keys):
        _fail(errors, f"Missing required payload key in log_event payload: {key}")


def _call_attr_name(node: ast.AST) -> tuple[str, str] | None:
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id, func.attr
    return None


def _check_main_naming_surface(errors: list[str]) -> None:
    path = APP_DIR / "main.py"
    module = _load_ast(path)

    for node in ast.walk(module):
        call_name = _call_attr_name(node)
        if call_name == ("observability", "incr"):
            if not node.args:
                _fail(errors, "observability.incr call without arguments")
                continue
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                if not COUNTER_RE.fullmatch(first_arg.value):
                    _fail(errors, f"Counter name does not match canonical pattern: {first_arg.value}")
            elif isinstance(first_arg, ast.JoinedStr):
                # Allow dynamic segments for path/reason based counters, but ensure canonical prefix.
                static_parts = "".join(
                    value.value
                    for value in first_arg.values
                    if isinstance(value, ast.Constant) and isinstance(value.value, str)
                )
                if not static_parts.startswith(("http.requests.", "ws.connect.rejected.")):
                    _fail(
                        errors,
                        "Dynamic observability.incr format must use approved prefixes: "
                        f"{ast.get_source_segment(path.read_text(encoding='utf-8'), first_arg)}",
                    )
            else:
                _fail(errors, "observability.incr first argument must be str or f-string")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "log_event":
            event_kw = None
            reason_kw = None
            for keyword in node.keywords:
                if keyword.arg == "event":
                    event_kw = keyword.value
                if keyword.arg == "reason_code":
                    reason_kw = keyword.value

            if isinstance(event_kw, ast.Constant) and isinstance(event_kw.value, str):
                if not EVENT_RE.fullmatch(event_kw.value):
                    _fail(errors, f"log_event event name does not match canonical pattern: {event_kw.value}")

            if isinstance(reason_kw, ast.Constant) and isinstance(reason_kw.value, str):
                if not REASON_RE.fullmatch(reason_kw.value):
                    _fail(errors, f"log_event reason_code does not match canonical pattern: {reason_kw.value}")


def _check_triage_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.observability_contract import REASON_CLASSES
        from app.observability_triage import (
            CORRELATION_FIELDS_ALWAYS_REQUIRED,
            CORRELATION_FIELDS_FOR_CLASSIFIED_EVENTS,
            CORRELATION_FIELDS_REQUIRE_ACTIVE_SPAN,
            TRIAGE_DASHBOARD_BY_REASON_CLASS,
            triage_classes_are_consistent,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import observability triage contract modules: {exc}")
        return

    if not triage_classes_are_consistent():
        _fail(errors, "Triage classes are inconsistent with observability reason taxonomy")

    if set(TRIAGE_DASHBOARD_BY_REASON_CLASS.keys()) != REASON_CLASSES:
        _fail(errors, "Triage dashboard mapping keys must match REASON_CLASSES")

    if tuple(CORRELATION_FIELDS_ALWAYS_REQUIRED) != ("request_id",):
        _fail(errors, "CORRELATION_FIELDS_ALWAYS_REQUIRED must be exactly ('request_id',)")

    if set(CORRELATION_FIELDS_REQUIRE_ACTIVE_SPAN) != {"trace_id", "span_id"}:
        _fail(errors, "CORRELATION_FIELDS_REQUIRE_ACTIVE_SPAN must contain trace_id and span_id")

    if set(CORRELATION_FIELDS_FOR_CLASSIFIED_EVENTS) != {"reason_code", "reason_class"}:
        _fail(errors, "CORRELATION_FIELDS_FOR_CLASSIFIED_EVENTS must contain reason_code and reason_class")


def _check_dashboard_alert_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.observability_dashboard_mapping import (
            ALERT_RULE_BASELINE,
            DASHBOARD_QUERY_BASELINE,
            PROM_COUNTER_ALIAS_BASELINE,
            validate_dashboard_alert_mapping_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import observability dashboard mapping modules: {exc}")
        return

    if not DASHBOARD_QUERY_BASELINE:
        _fail(errors, "DASHBOARD_QUERY_BASELINE must not be empty")
    if not ALERT_RULE_BASELINE:
        _fail(errors, "ALERT_RULE_BASELINE must not be empty")
    if not PROM_COUNTER_ALIAS_BASELINE:
        _fail(errors, "PROM_COUNTER_ALIAS_BASELINE must not be empty")

    errors.extend(validate_dashboard_alert_mapping_contract())


def _check_reliability_slo_baseline_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.reliability_alerting_baseline import (
            BURN_RATE_ALERT_BASELINE,
            RELIABILITY_SLI_KEYS,
            SLI_BASELINE,
            SLO_BASELINE,
            SLO_QUERY_MAPPING,
            validate_reliability_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import reliability baseline modules: {exc}")
        return

    if not RELIABILITY_SLI_KEYS:
        _fail(errors, "RELIABILITY_SLI_KEYS must not be empty")
    if not SLI_BASELINE or not SLO_BASELINE or not SLO_QUERY_MAPPING or not BURN_RATE_ALERT_BASELINE:
        _fail(errors, "Reliability baseline mappings must not be empty")

    errors.extend(validate_reliability_baseline_contract())


def _check_reliability_alert_policy_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.reliability_alert_policy_mapping import (
            SLO_ALERT_QUERY_MAPPING,
            SLO_ALERT_RULE_ALIAS_BASELINE,
            SLO_ALERT_SEVERITY_ACTION_BASELINE,
            SLO_RECORDING_RULE_ALIAS_BASELINE,
            validate_reliability_alert_policy_mapping_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import reliability alert policy mapping modules: {exc}")
        return

    if not SLO_RECORDING_RULE_ALIAS_BASELINE:
        _fail(errors, "SLO_RECORDING_RULE_ALIAS_BASELINE must not be empty")
    if not SLO_ALERT_SEVERITY_ACTION_BASELINE:
        _fail(errors, "SLO_ALERT_SEVERITY_ACTION_BASELINE must not be empty")
    if not SLO_ALERT_RULE_ALIAS_BASELINE:
        _fail(errors, "SLO_ALERT_RULE_ALIAS_BASELINE must not be empty")
    if not SLO_ALERT_QUERY_MAPPING:
        _fail(errors, "SLO_ALERT_QUERY_MAPPING must not be empty")

    errors.extend(validate_reliability_alert_policy_mapping_contract())


def _check_reliability_alert_routing_baseline_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.reliability_alert_routing_baseline import (
            ALERT_ESCALATION_POLICY_BASELINE,
            ALERT_NOTIFICATION_TARGET_BASELINE,
            ALERT_ROUTING_LABEL_BASELINE,
            ALERT_RUNBOOK_OWNERSHIP_BASELINE,
            validate_reliability_alert_routing_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import reliability alert routing baseline modules: {exc}")
        return

    if not ALERT_NOTIFICATION_TARGET_BASELINE:
        _fail(errors, "ALERT_NOTIFICATION_TARGET_BASELINE must not be empty")
    if not ALERT_ROUTING_LABEL_BASELINE:
        _fail(errors, "ALERT_ROUTING_LABEL_BASELINE must not be empty")
    if not ALERT_ESCALATION_POLICY_BASELINE:
        _fail(errors, "ALERT_ESCALATION_POLICY_BASELINE must not be empty")
    if not ALERT_RUNBOOK_OWNERSHIP_BASELINE:
        _fail(errors, "ALERT_RUNBOOK_OWNERSHIP_BASELINE must not be empty")

    errors.extend(validate_reliability_alert_routing_baseline_contract())


def _check_reliability_alert_suppression_baseline_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.reliability_alert_suppression_baseline import (
            ALERT_GROUPING_BASELINE,
            ALERT_GROUP_TIMING_BASELINE,
            ALERT_INHIBITION_POLICY_BASELINE,
            ALERT_SILENCE_POLICY_BASELINE,
            validate_reliability_alert_suppression_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import reliability alert suppression baseline modules: {exc}")
        return

    if not ALERT_GROUPING_BASELINE:
        _fail(errors, "ALERT_GROUPING_BASELINE must not be empty")
    if not ALERT_GROUP_TIMING_BASELINE:
        _fail(errors, "ALERT_GROUP_TIMING_BASELINE must not be empty")
    if not ALERT_INHIBITION_POLICY_BASELINE:
        _fail(errors, "ALERT_INHIBITION_POLICY_BASELINE must not be empty")
    if not ALERT_SILENCE_POLICY_BASELINE:
        _fail(errors, "ALERT_SILENCE_POLICY_BASELINE must not be empty")

    errors.extend(validate_reliability_alert_suppression_baseline_contract())


def _check_reliability_alert_delivery_template_baseline_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.reliability_alert_delivery_template_baseline import (
            ALERT_CONTACT_POINT_PAYLOAD_BASELINE,
            ALERT_DELIVERY_SCHEMA_BASELINE,
            ALERT_RUNBOOK_LINK_FORMAT_BASELINE,
            ALERT_TEMPLATE_VARIABLE_BASELINE,
            validate_reliability_alert_delivery_template_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import reliability alert delivery template baseline modules: {exc}")
        return

    if not ALERT_DELIVERY_SCHEMA_BASELINE:
        _fail(errors, "ALERT_DELIVERY_SCHEMA_BASELINE must not be empty")
    if not ALERT_TEMPLATE_VARIABLE_BASELINE:
        _fail(errors, "ALERT_TEMPLATE_VARIABLE_BASELINE must not be empty")
    if not ALERT_CONTACT_POINT_PAYLOAD_BASELINE:
        _fail(errors, "ALERT_CONTACT_POINT_PAYLOAD_BASELINE must not be empty")
    if not ALERT_RUNBOOK_LINK_FORMAT_BASELINE.mode:
        _fail(errors, "ALERT_RUNBOOK_LINK_FORMAT_BASELINE.mode must not be empty")

    errors.extend(validate_reliability_alert_delivery_template_baseline_contract())


def _check_reliability_alert_policy_export_baseline_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from app.reliability_alert_policy_export_baseline import (
            ALERTMANAGER_EXPORT_BASELINE,
            ALERTMANAGER_INHIBIT_EXPORT_BASELINE,
            ALERTMANAGER_RECEIVER_EXPORT_BASELINE,
            ALERTMANAGER_ROUTE_EXPORT_BASELINE,
            ALERTMANAGER_TEMPLATE_EXPORT_BASELINE,
            GRAFANA_CONTACT_POINT_EXPORT_BASELINE,
            GRAFANA_EXPORT_BASELINE,
            GRAFANA_MUTE_TIMING_EXPORT_BASELINE,
            GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE,
            GRAFANA_TEMPLATE_EXPORT_BASELINE,
            RUNTIME_MANAGED_SILENCE_BASELINE,
            STATIC_SUPPRESSION_EXPORT_BASELINE,
            validate_reliability_alert_policy_export_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import reliability alert policy export baseline modules: {exc}")
        return

    if not ALERTMANAGER_EXPORT_BASELINE:
        _fail(errors, "ALERTMANAGER_EXPORT_BASELINE must not be empty")
    if not ALERTMANAGER_ROUTE_EXPORT_BASELINE:
        _fail(errors, "ALERTMANAGER_ROUTE_EXPORT_BASELINE must not be empty")
    if not ALERTMANAGER_RECEIVER_EXPORT_BASELINE:
        _fail(errors, "ALERTMANAGER_RECEIVER_EXPORT_BASELINE must not be empty")
    if not ALERTMANAGER_INHIBIT_EXPORT_BASELINE:
        _fail(errors, "ALERTMANAGER_INHIBIT_EXPORT_BASELINE must not be empty")
    if not ALERTMANAGER_TEMPLATE_EXPORT_BASELINE:
        _fail(errors, "ALERTMANAGER_TEMPLATE_EXPORT_BASELINE must not be empty")

    if not GRAFANA_EXPORT_BASELINE:
        _fail(errors, "GRAFANA_EXPORT_BASELINE must not be empty")
    if not GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE:
        _fail(errors, "GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE must not be empty")
    if not GRAFANA_CONTACT_POINT_EXPORT_BASELINE:
        _fail(errors, "GRAFANA_CONTACT_POINT_EXPORT_BASELINE must not be empty")
    if not GRAFANA_MUTE_TIMING_EXPORT_BASELINE:
        _fail(errors, "GRAFANA_MUTE_TIMING_EXPORT_BASELINE must not be empty")
    if not GRAFANA_TEMPLATE_EXPORT_BASELINE:
        _fail(errors, "GRAFANA_TEMPLATE_EXPORT_BASELINE must not be empty")

    if not STATIC_SUPPRESSION_EXPORT_BASELINE:
        _fail(errors, "STATIC_SUPPRESSION_EXPORT_BASELINE must not be empty")
    if not RUNTIME_MANAGED_SILENCE_BASELINE:
        _fail(errors, "RUNTIME_MANAGED_SILENCE_BASELINE must not be empty")

    errors.extend(validate_reliability_alert_policy_export_baseline_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(
        DOC_18_1_PATH,
        REQUIRED_DOC_18_1_PHRASES,
        label="Step 18.1 observability baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_18_3_PATH,
        REQUIRED_DOC_18_3_PHRASES,
        label="Step 18.3 correlation/triage baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_18_4_PATH,
        REQUIRED_DOC_18_4_PHRASES,
        label="Step 18.4 dashboard/alert mapping baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_19_1_PATH,
        REQUIRED_DOC_19_1_PHRASES,
        label="Step 19.1 reliability/SLO baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_19_2_PATH,
        REQUIRED_DOC_19_2_PHRASES,
        label="Step 19.2 SLO query/alert policy baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_19_3_PATH,
        REQUIRED_DOC_19_3_PHRASES,
        label="Step 19.3 alert routing/escalation baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_19_4_PATH,
        REQUIRED_DOC_19_4_PHRASES,
        label="Step 19.4 alert suppression/grouping baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_19_5_PATH,
        REQUIRED_DOC_19_5_PHRASES,
        label="Step 19.5 alert delivery template baseline doc",
        errors=errors,
    )
    _check_doc(
        DOC_19_6_PATH,
        REQUIRED_DOC_19_6_PHRASES,
        label="Step 19.6 alertmanager/grafana policy export baseline doc",
        errors=errors,
    )
    _check_env_surface(errors)
    _check_tracing_resource(errors)
    _check_operational_logging_contract(errors)
    _check_main_naming_surface(errors)
    _check_triage_contract(errors)
    _check_dashboard_alert_mapping_contract(errors)
    _check_reliability_slo_baseline_contract(errors)
    _check_reliability_alert_policy_mapping_contract(errors)
    _check_reliability_alert_routing_baseline_contract(errors)
    _check_reliability_alert_suppression_baseline_contract(errors)
    _check_reliability_alert_delivery_template_baseline_contract(errors)
    _check_reliability_alert_policy_export_baseline_contract(errors)

    if errors:
        print("observability-contract-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("observability-contract-check: OK")
    print(
        f"- checked docs: {DOC_18_1_PATH}, {DOC_18_3_PATH}, {DOC_18_4_PATH}, "
        f"{DOC_19_1_PATH}, {DOC_19_2_PATH}, {DOC_19_3_PATH}, {DOC_19_4_PATH}, {DOC_19_5_PATH}, {DOC_19_6_PATH}"
    )
    print(f"- checked env surface: {ENV_EXAMPLE}")
    print(f"- checked app files: {APP_DIR / 'main.py'}, {APP_DIR / 'tracing.py'}, {APP_DIR / 'operational_logging.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

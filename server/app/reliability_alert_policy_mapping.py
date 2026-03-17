from __future__ import annotations

from dataclasses import dataclass
import re

from .reliability_alerting_baseline import BURN_RATE_ALERT_BASELINE, RELIABILITY_SLI_KEYS


@dataclass(frozen=True)
class RecordingRuleAliasSpec:
    sli_key: str
    window: str
    alias: str
    expression_template: str


@dataclass(frozen=True)
class AlertRuleAliasSpec:
    alert_alias: str
    sli_key: str
    policy_id: str
    severity: str
    action: str
    burn_rate_threshold: float
    long_window_alias: str
    short_window_alias: str
    query_template: str
    runbook_ref: str
    summary: str


@dataclass(frozen=True)
class SeverityActionSpec:
    policy_id: str
    severity: str
    action: str


_SLI_METRIC_ALIAS = {
    "auth_availability": "auth_verify",
    "ws_session_establishment": "ws_session_establish",
    "readiness_availability": "readiness",
}

_WINDOW_ALIAS_SUFFIX = {
    "5m": "rate5m",
    "30m": "rate30m",
    "1h": "rate1h",
    "6h": "rate6h",
    "3d": "rate3d",
}

_WINDOW_ORDER = {"5m": 1, "30m": 2, "1h": 3, "6h": 4, "3d": 5}

_REQUIRED_WINDOWS = tuple(
    sorted(
        {policy.long_window for policy in BURN_RATE_ALERT_BASELINE.values()}
        | {policy.short_window for policy in BURN_RATE_ALERT_BASELINE.values()},
        key=lambda value: _WINDOW_ORDER[value],
    )
)

_RECORDING_ALIAS_RE = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")
_ALERT_ALIAS_RE = re.compile(r"^slo:[a-z][a-z0-9_]*:burn_[a-z][a-z0-9_]*$")


def _build_burn_alias(sli_key: str, window: str) -> str:
    metric_alias = _SLI_METRIC_ALIAS[sli_key]
    suffix = _WINDOW_ALIAS_SUFFIX[window]
    return f"service:{metric_alias}_error_budget_burn:ratio_{suffix}"


def _build_recording_alias_baseline() -> dict[str, dict[str, RecordingRuleAliasSpec]]:
    out: dict[str, dict[str, RecordingRuleAliasSpec]] = {}
    for sli_key in sorted(RELIABILITY_SLI_KEYS):
        window_mapping: dict[str, RecordingRuleAliasSpec] = {}
        for window in _REQUIRED_WINDOWS:
            alias = _build_burn_alias(sli_key, window)
            window_mapping[window] = RecordingRuleAliasSpec(
                sli_key=sli_key,
                window=window,
                alias=alias,
                expression_template=(
                    f"({sli_key}.bad_events[{window}] / clamp_min({sli_key}.total_events[{window}], 1)) "
                    f"/ (1 - {sli_key}.slo_target)"
                ),
            )
        out[sli_key] = window_mapping
    return out


def _build_severity_action_baseline() -> dict[str, SeverityActionSpec]:
    return {
        policy_id: SeverityActionSpec(
            policy_id=policy_id,
            severity=policy.severity,
            action=policy.action,
        )
        for policy_id, policy in BURN_RATE_ALERT_BASELINE.items()
    }


def _build_alert_alias_baseline(
    recording_aliases: dict[str, dict[str, RecordingRuleAliasSpec]],
) -> tuple[dict[str, AlertRuleAliasSpec], dict[str, str]]:
    rule_mapping: dict[str, AlertRuleAliasSpec] = {}
    query_mapping: dict[str, str] = {}

    for sli_key in sorted(RELIABILITY_SLI_KEYS):
        for policy_id in sorted(BURN_RATE_ALERT_BASELINE.keys()):
            policy = BURN_RATE_ALERT_BASELINE[policy_id]
            long_alias = recording_aliases[sli_key][policy.long_window].alias
            short_alias = recording_aliases[sli_key][policy.short_window].alias
            threshold = policy.burn_rate_threshold
            alert_alias = f"slo:{sli_key}:burn_{policy_id}"
            query = f"({long_alias} > {threshold}) and ({short_alias} > {threshold})"

            rule_mapping[alert_alias] = AlertRuleAliasSpec(
                alert_alias=alert_alias,
                sli_key=sli_key,
                policy_id=policy_id,
                severity=policy.severity,
                action=policy.action,
                burn_rate_threshold=threshold,
                long_window_alias=long_alias,
                short_window_alias=short_alias,
                query_template=query,
                runbook_ref=f"docs/runbooks/slo/{sli_key}.md",
                summary=(
                    f"{sli_key} burn-rate policy '{policy_id}' breached "
                    f"({policy.long_window}/{policy.short_window})."
                ),
            )
            query_mapping[alert_alias] = query

    return rule_mapping, query_mapping


SLO_RECORDING_RULE_ALIAS_BASELINE = _build_recording_alias_baseline()
SLO_ALERT_SEVERITY_ACTION_BASELINE = _build_severity_action_baseline()
SLO_ALERT_RULE_ALIAS_BASELINE, SLO_ALERT_QUERY_MAPPING = _build_alert_alias_baseline(
    SLO_RECORDING_RULE_ALIAS_BASELINE
)


def validate_reliability_alert_policy_mapping_contract() -> list[str]:
    errors: list[str] = []

    if set(SLO_RECORDING_RULE_ALIAS_BASELINE.keys()) != RELIABILITY_SLI_KEYS:
        errors.append("SLO_RECORDING_RULE_ALIAS_BASELINE keys must match RELIABILITY_SLI_KEYS")

    if set(SLO_ALERT_SEVERITY_ACTION_BASELINE.keys()) != set(BURN_RATE_ALERT_BASELINE.keys()):
        errors.append("SLO_ALERT_SEVERITY_ACTION_BASELINE keys must match BURN_RATE_ALERT_BASELINE")

    all_recording_aliases: set[str] = set()

    for sli_key, window_specs in SLO_RECORDING_RULE_ALIAS_BASELINE.items():
        if set(window_specs.keys()) != set(_REQUIRED_WINDOWS):
            errors.append(
                f"{sli_key}: recording windows must match {_REQUIRED_WINDOWS}, got {tuple(window_specs.keys())}"
            )

        for window, spec in window_specs.items():
            if spec.sli_key != sli_key:
                errors.append(f"{sli_key}/{window}: sli_key mismatch in recording alias spec")
            if spec.window != window:
                errors.append(f"{sli_key}/{window}: window mismatch in recording alias spec")
            if not _RECORDING_ALIAS_RE.fullmatch(spec.alias):
                errors.append(f"{sli_key}/{window}: invalid recording alias format: {spec.alias}")
            if spec.alias in all_recording_aliases:
                errors.append(f"{sli_key}/{window}: duplicate recording alias detected: {spec.alias}")
            all_recording_aliases.add(spec.alias)
            if "slo_target" not in spec.expression_template:
                errors.append(
                    f"{sli_key}/{window}: expression_template must include slo_target normalization"
                )

    expected_alert_count = len(RELIABILITY_SLI_KEYS) * len(BURN_RATE_ALERT_BASELINE)
    if len(SLO_ALERT_RULE_ALIAS_BASELINE) != expected_alert_count:
        errors.append(
            "SLO_ALERT_RULE_ALIAS_BASELINE must include each sli_key x policy_id combination"
        )

    if set(SLO_ALERT_QUERY_MAPPING.keys()) != set(SLO_ALERT_RULE_ALIAS_BASELINE.keys()):
        errors.append("SLO_ALERT_QUERY_MAPPING keys must match SLO_ALERT_RULE_ALIAS_BASELINE keys")

    for alert_alias, spec in SLO_ALERT_RULE_ALIAS_BASELINE.items():
        if spec.alert_alias != alert_alias:
            errors.append(f"{alert_alias}: alert_alias field must match dictionary key")
        if not _ALERT_ALIAS_RE.fullmatch(alert_alias):
            errors.append(f"{alert_alias}: invalid alert alias format")

        if spec.sli_key not in RELIABILITY_SLI_KEYS:
            errors.append(f"{alert_alias}: unknown sli_key: {spec.sli_key}")
            continue

        policy = BURN_RATE_ALERT_BASELINE.get(spec.policy_id)
        if policy is None:
            errors.append(f"{alert_alias}: unknown policy_id: {spec.policy_id}")
            continue

        expected_severity_action = SLO_ALERT_SEVERITY_ACTION_BASELINE.get(spec.policy_id)
        if expected_severity_action is None:
            errors.append(f"{alert_alias}: missing severity/action mapping for policy_id {spec.policy_id}")
        else:
            if spec.severity != expected_severity_action.severity:
                errors.append(
                    f"{alert_alias}: severity mismatch, expected {expected_severity_action.severity}, got {spec.severity}"
                )
            if spec.action != expected_severity_action.action:
                errors.append(
                    f"{alert_alias}: action mismatch, expected {expected_severity_action.action}, got {spec.action}"
                )

        if round(spec.burn_rate_threshold, 6) != round(policy.burn_rate_threshold, 6):
            errors.append(
                f"{alert_alias}: burn_rate_threshold mismatch, expected {policy.burn_rate_threshold}, got {spec.burn_rate_threshold}"
            )

        expected_long_alias = SLO_RECORDING_RULE_ALIAS_BASELINE[spec.sli_key][policy.long_window].alias
        expected_short_alias = SLO_RECORDING_RULE_ALIAS_BASELINE[spec.sli_key][policy.short_window].alias
        if spec.long_window_alias != expected_long_alias:
            errors.append(
                f"{alert_alias}: long_window_alias mismatch, expected {expected_long_alias}, got {spec.long_window_alias}"
            )
        if spec.short_window_alias != expected_short_alias:
            errors.append(
                f"{alert_alias}: short_window_alias mismatch, expected {expected_short_alias}, got {spec.short_window_alias}"
            )

        if not spec.runbook_ref.startswith("docs/runbooks/slo/"):
            errors.append(f"{alert_alias}: runbook_ref must start with docs/runbooks/slo/")
        if not spec.summary.strip():
            errors.append(f"{alert_alias}: summary must not be empty")

        query_alias_value = SLO_ALERT_QUERY_MAPPING.get(alert_alias)
        if query_alias_value != spec.query_template:
            errors.append(
                f"{alert_alias}: SLO_ALERT_QUERY_MAPPING entry must equal rule query_template"
            )

        if str(policy.burn_rate_threshold) not in spec.query_template:
            errors.append(f"{alert_alias}: query_template must include burn-rate threshold value")
        if spec.long_window_alias not in spec.query_template or spec.short_window_alias not in spec.query_template:
            errors.append(
                f"{alert_alias}: query_template must reference both long_window_alias and short_window_alias"
            )

    return errors

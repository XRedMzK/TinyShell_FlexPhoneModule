from __future__ import annotations

from dataclasses import dataclass

from .observability_contract import REASON_CLASS_BY_CODE, REASON_CLASSES

ROLLING_WINDOW_DAYS = 30

RELIABILITY_SLI_KEYS = {
    "auth_availability",
    "ws_session_establishment",
    "readiness_availability",
}

SECURITY_REASON_CODES = tuple(
    sorted(
        reason_code
        for reason_code, reason_class in REASON_CLASS_BY_CODE.items()
        if reason_class == "security"
    )
)


@dataclass(frozen=True)
class SLIBaseline:
    name: str
    scope: str
    user_symptom: str
    good_event_definition: str
    bad_event_definition: str
    excluded_reason_codes: tuple[str, ...]
    included_reason_classes: tuple[str, ...]


@dataclass(frozen=True)
class SLOBaseline:
    sli_name: str
    target: float
    window_days: int
    error_budget: float


@dataclass(frozen=True)
class BurnRatePolicy:
    policy_id: str
    burn_rate_threshold: float
    long_window: str
    short_window: str
    severity: str
    action: str


SLI_BASELINE: dict[str, SLIBaseline] = {
    "auth_availability": SLIBaseline(
        name="auth_availability",
        scope="auth",
        user_symptom="User cannot complete verify/login path due to runtime/dependency failures.",
        good_event_definition="auth.verify.succeeded",
        bad_event_definition="auth.verify.failed where reason_class in {operational,dependency}",
        excluded_reason_codes=SECURITY_REASON_CODES,
        included_reason_classes=("operational", "dependency"),
    ),
    "ws_session_establishment": SLIBaseline(
        name="ws_session_establishment",
        scope="ws",
        user_symptom="User cannot establish signaling websocket session due to runtime/dependency failures.",
        good_event_definition="ws.connect.accepted",
        bad_event_definition="ws.connect.rejected where reason_class in {operational,dependency}",
        excluded_reason_codes=SECURITY_REASON_CODES,
        included_reason_classes=("operational", "dependency"),
    ),
    "readiness_availability": SLIBaseline(
        name="readiness_availability",
        scope="readiness",
        user_symptom="Service instance cannot serve traffic due to readiness degradation.",
        good_event_definition="runtime.ready.ok",
        bad_event_definition="runtime.ready.degraded",
        excluded_reason_codes=(),
        included_reason_classes=("dependency",),
    ),
}

SLO_BASELINE: dict[str, SLOBaseline] = {
    "auth_availability": SLOBaseline(
        sli_name="auth_availability",
        target=0.999,
        window_days=ROLLING_WINDOW_DAYS,
        error_budget=0.001,
    ),
    "ws_session_establishment": SLOBaseline(
        sli_name="ws_session_establishment",
        target=0.999,
        window_days=ROLLING_WINDOW_DAYS,
        error_budget=0.001,
    ),
    "readiness_availability": SLOBaseline(
        sli_name="readiness_availability",
        target=0.995,
        window_days=ROLLING_WINDOW_DAYS,
        error_budget=0.005,
    ),
}

BURN_RATE_ALERT_BASELINE: dict[str, BurnRatePolicy] = {
    "fast_page": BurnRatePolicy(
        policy_id="fast_page",
        burn_rate_threshold=14.4,
        long_window="1h",
        short_window="5m",
        severity="page",
        action="page_on_call",
    ),
    "slow_page": BurnRatePolicy(
        policy_id="slow_page",
        burn_rate_threshold=6.0,
        long_window="6h",
        short_window="30m",
        severity="page",
        action="page_on_call",
    ),
    "budget_ticket": BurnRatePolicy(
        policy_id="budget_ticket",
        burn_rate_threshold=1.0,
        long_window="3d",
        short_window="6h",
        severity="ticket",
        action="open_ticket",
    ),
}

# Query aliases are intentionally provider-agnostic and map to canonical SLI math.
SLO_QUERY_MAPPING: dict[str, dict[str, str]] = {
    "auth_availability": {
        "good_events": "sum(rate(auth.verify.succeeded[window]))",
        "bad_events": "sum(rate(auth.verify.failed{reason_class=~\"operational|dependency\"}[window]))",
        "error_rate": "bad_events / clamp_min(good_events + bad_events, 1)",
        "burn_rate": "error_rate / (1 - 0.999)",
    },
    "ws_session_establishment": {
        "good_events": "sum(rate(ws.connect.accepted[window]))",
        "bad_events": "sum(rate(ws.connect.rejected{reason_class=~\"operational|dependency\"}[window]))",
        "error_rate": "bad_events / clamp_min(good_events + bad_events, 1)",
        "burn_rate": "error_rate / (1 - 0.999)",
    },
    "readiness_availability": {
        "good_events": "sum(rate(runtime.ready.ok[window]))",
        "bad_events": "sum(rate(runtime.ready.degraded[window]))",
        "error_rate": "bad_events / clamp_min(good_events + bad_events, 1)",
        "burn_rate": "error_rate / (1 - 0.995)",
    },
}

# Invariants for Step 19.1
SYMPTOM_BASED_ALERTING_INVARIANT = True
NON_FATAL_OBSERVABILITY_DEPENDENCIES_INVARIANT = True


def validate_reliability_baseline_contract() -> list[str]:
    errors: list[str] = []

    if set(SLI_BASELINE.keys()) != RELIABILITY_SLI_KEYS:
        errors.append("SLI_BASELINE keys must match RELIABILITY_SLI_KEYS")

    if set(SLO_BASELINE.keys()) != RELIABILITY_SLI_KEYS:
        errors.append("SLO_BASELINE keys must match RELIABILITY_SLI_KEYS")

    if set(SLO_QUERY_MAPPING.keys()) != RELIABILITY_SLI_KEYS:
        errors.append("SLO_QUERY_MAPPING keys must match RELIABILITY_SLI_KEYS")

    if not SYMPTOM_BASED_ALERTING_INVARIANT:
        errors.append("SYMPTOM_BASED_ALERTING_INVARIANT must be true")
    if not NON_FATAL_OBSERVABILITY_DEPENDENCIES_INVARIANT:
        errors.append("NON_FATAL_OBSERVABILITY_DEPENDENCIES_INVARIANT must be true")

    for sli_key, sli in SLI_BASELINE.items():
        if not sli.user_symptom.strip():
            errors.append(f"{sli_key}: user_symptom must not be empty")

        if set(sli.included_reason_classes) - REASON_CLASSES:
            errors.append(f"{sli_key}: included_reason_classes must be subset of REASON_CLASSES")

        for reason_code in sli.excluded_reason_codes:
            reason_class = REASON_CLASS_BY_CODE.get(reason_code)
            if reason_class is None:
                errors.append(f"{sli_key}: excluded reason_code is unknown: {reason_code}")
                continue
            if reason_class != "security":
                errors.append(
                    f"{sli_key}: excluded reason_code must be security-classified: {reason_code} -> {reason_class}"
                )

        query_map = SLO_QUERY_MAPPING.get(sli_key, {})
        required_query_parts = {"good_events", "bad_events", "error_rate", "burn_rate"}
        if set(query_map.keys()) != required_query_parts:
            errors.append(f"{sli_key}: SLO_QUERY_MAPPING must contain {sorted(required_query_parts)}")

    for slo_key, slo in SLO_BASELINE.items():
        if slo.window_days != ROLLING_WINDOW_DAYS:
            errors.append(f"{slo_key}: window_days must be {ROLLING_WINDOW_DAYS}")
        if not (0 < slo.target < 1):
            errors.append(f"{slo_key}: target must be in (0, 1)")
        expected_budget = round(1 - slo.target, 6)
        if round(slo.error_budget, 6) != expected_budget:
            errors.append(
                f"{slo_key}: error_budget must equal (1-target), expected {expected_budget}, got {slo.error_budget}"
            )

    required_burn_policy = {
        "fast_page": (14.4, "1h", "5m", "page"),
        "slow_page": (6.0, "6h", "30m", "page"),
        "budget_ticket": (1.0, "3d", "6h", "ticket"),
    }
    if set(BURN_RATE_ALERT_BASELINE.keys()) != set(required_burn_policy.keys()):
        errors.append("BURN_RATE_ALERT_BASELINE must contain fast_page, slow_page, budget_ticket")
    else:
        for policy_id, (threshold, long_window, short_window, severity) in required_burn_policy.items():
            policy = BURN_RATE_ALERT_BASELINE[policy_id]
            if policy.burn_rate_threshold != threshold:
                errors.append(
                    f"{policy_id}: burn_rate_threshold expected {threshold}, got {policy.burn_rate_threshold}"
                )
            if policy.long_window != long_window or policy.short_window != short_window:
                errors.append(
                    f"{policy_id}: windows expected ({long_window}, {short_window}), "
                    f"got ({policy.long_window}, {policy.short_window})"
                )
            if policy.severity != severity:
                errors.append(f"{policy_id}: severity expected {severity}, got {policy.severity}")

    return errors

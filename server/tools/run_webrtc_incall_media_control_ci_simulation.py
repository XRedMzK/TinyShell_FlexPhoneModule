from __future__ import annotations

import os
from typing import Any

from run_webrtc_incall_media_control_sandbox_smoke import (
    INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS,
    InCallMediaControlSmokeError,
    run_webrtc_incall_media_control_sandbox_smoke,
)

from app.webrtc_incall_media_control_ci_gate_baseline import (
    CI_INCALL_MEDIA_CONTROL_REQUIRED_ASSERTIONS,
    CI_INCALL_MEDIA_CONTROL_SCENARIO_IDS,
)
from app.webrtc_incall_quality_observability_baseline import (
    LIMITED_AVAILABILITY_NON_GATING_METRICS,
    QUALITY_STATS_SURFACE_BASELINE,
)


VALID_SCENARIOS = {"all", *CI_INCALL_MEDIA_CONTROL_SCENARIO_IDS}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _assert_eq(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        _fail(errors, f"{label}: expected {expected!r}, got {actual!r}")


def _validate_smoke_scenario(errors: list[str], scenario_id: str, payload: dict[str, Any]) -> None:
    if payload.get("status") != "PASS":
        _fail(errors, f"{scenario_id}: status must be PASS")
        return

    assertions = payload.get("expected_contract_assertions")
    if not isinstance(assertions, dict):
        _fail(errors, f"{scenario_id}: expected_contract_assertions must be object")
        return

    required_assertions = CI_INCALL_MEDIA_CONTROL_REQUIRED_ASSERTIONS[scenario_id]["required_assertions"]
    for assertion_key in required_assertions:
        if assertions.get(assertion_key) is not True:
            _fail(errors, f"{scenario_id}: required assertion {assertion_key!r} must be true")


def _validate_ci_only_scenario_g(errors: list[str], proof: dict[str, Any]) -> None:
    required_types = proof.get("required_stat_types")
    _assert_eq(
        errors,
        "G_required_optional_stats_gate_semantics.required_stat_types",
        tuple(required_types) if isinstance(required_types, (tuple, list)) else required_types,
        QUALITY_STATS_SURFACE_BASELINE["required_stat_types"],
    )

    non_gating_missing_metrics = proof.get("non_gating_missing_metrics")
    if not isinstance(non_gating_missing_metrics, list):
        _fail(errors, "G_required_optional_stats_gate_semantics.non_gating_missing_metrics must be list")
        return

    expected_non_gating = sorted(LIMITED_AVAILABILITY_NON_GATING_METRICS)
    if sorted(non_gating_missing_metrics) != expected_non_gating:
        _fail(
            errors,
            "G_required_optional_stats_gate_semantics non-gating metrics must match 25.5 limited-availability set",
        )


def _validate_contract(target_scenario: str, proof: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if proof.get("overall_status") != "PASS":
        _fail(errors, "overall_status must be PASS")

    payload_scenarios = proof.get("scenarios")
    if not isinstance(payload_scenarios, list):
        _fail(errors, "proof.scenarios must be list")
        return errors

    scenario_map: dict[str, dict[str, Any]] = {}
    for entry in payload_scenarios:
        if not isinstance(entry, dict):
            _fail(errors, "proof.scenarios entries must be objects")
            continue
        scenario_id = entry.get("scenario_id")
        if not isinstance(scenario_id, str):
            _fail(errors, "proof.scenarios entry must define scenario_id string")
            continue
        scenario_map[scenario_id] = entry

    expected_smoke_ids = set(INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS)
    if set(scenario_map.keys()) != expected_smoke_ids:
        _fail(errors, f"proof scenario IDs must match smoke IDs: {sorted(expected_smoke_ids)}")

    if target_scenario == "all":
        _assert_eq(errors, "scenarios_total", proof.get("scenarios_total"), len(INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS))
        _assert_eq(errors, "scenarios_passed", proof.get("scenarios_passed"), len(INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS))
        target_smoke_ids = list(INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS)
        check_ci_only_g = True
    elif target_scenario == "G_required_optional_stats_gate_semantics":
        target_smoke_ids = []
        check_ci_only_g = True
    else:
        target_smoke_ids = [target_scenario]
        check_ci_only_g = False

    for scenario_id in target_smoke_ids:
        payload = scenario_map.get(scenario_id)
        if payload is None:
            _fail(errors, f"{scenario_id}: missing in proof payload")
            continue
        _validate_smoke_scenario(errors, scenario_id, payload)

    if check_ci_only_g:
        _validate_ci_only_scenario_g(errors, proof)

    return errors


def run_ci_simulation() -> int:
    target_scenario = os.getenv("FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO", "all").strip()
    if target_scenario not in VALID_SCENARIOS:
        print(
            "WebRTC in-call media-control CI simulation: FAILED - "
            f"unsupported FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO={target_scenario!r}; "
            f"expected one of {sorted(VALID_SCENARIOS)}"
        )
        return 1

    print(f"WebRTC in-call media-control CI simulation scenario={target_scenario}")
    proof_obj = run_webrtc_incall_media_control_sandbox_smoke(return_proof=True)
    if not isinstance(proof_obj, dict):
        print("WebRTC in-call media-control CI simulation: FAILED - runner did not return proof payload")
        return 1

    errors = _validate_contract(target_scenario, proof_obj)
    if errors:
        print("WebRTC in-call media-control CI simulation: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print(f"WebRTC in-call media-control CI simulation scenario={target_scenario}: OK")
    return 0


def main() -> int:
    try:
        return run_ci_simulation()
    except InCallMediaControlSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"WebRTC in-call media-control CI simulation: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"WebRTC in-call media-control CI simulation: FAILED (unexpected) - {exc!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

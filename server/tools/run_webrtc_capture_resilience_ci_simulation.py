from __future__ import annotations

import os
from typing import Any

from run_webrtc_capture_resilience_sandbox_smoke import (
    CAPTURE_RESILIENCE_SMOKE_SCENARIO_IDS,
    CAPTURE_RESILIENCE_SMOKE_SUCCESS_MARKER,
    CaptureResilienceSmokeError,
    run_webrtc_capture_resilience_sandbox_smoke,
)

from app.webrtc_capture_resilience_ci_gate_baseline import (
    CI_CAPTURE_RESILIENCE_REQUIRED_ASSERTIONS,
    CI_CAPTURE_RESILIENCE_SCENARIO_IDS,
)


VALID_SCENARIOS = {"all", *CI_CAPTURE_RESILIENCE_SCENARIO_IDS}
CI_SUCCESS_MARKER = "WebRTC capture resilience CI simulation: OK"


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _validate_scenario(errors: list[str], scenario_id: str, payload: dict[str, Any]) -> None:
    if payload.get("status") != "PASS":
        _fail(errors, f"{scenario_id}: status must be PASS")
        return

    surfaces = payload.get("authoritative_surfaces")
    actions = payload.get("deterministic_actions")
    forbidden = payload.get("forbidden_interpretations_checked")

    if not isinstance(surfaces, list):
        _fail(errors, f"{scenario_id}: authoritative_surfaces must be list")
        return
    if not isinstance(actions, list):
        _fail(errors, f"{scenario_id}: deterministic_actions must be list")
        return
    if not isinstance(forbidden, list):
        _fail(errors, f"{scenario_id}: forbidden_interpretations_checked must be list")
        return

    required = CI_CAPTURE_RESILIENCE_REQUIRED_ASSERTIONS[scenario_id]
    for marker in required["required_authoritative_surfaces"]:
        if marker not in surfaces:
            _fail(errors, f"{scenario_id}: missing authoritative surface marker {marker!r}")
    for marker in required["required_forbidden_checks"]:
        if marker not in forbidden:
            _fail(errors, f"{scenario_id}: missing forbidden-check marker {marker!r}")

    if not actions:
        _fail(errors, f"{scenario_id}: deterministic_actions must be non-empty")


def _validate_contract(target_scenario: str, proof: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if proof.get("overall_status") != "PASS":
        _fail(errors, "overall_status must be PASS")

    if proof.get("advisory_devicechange_only") is not True:
        _fail(errors, "advisory_devicechange_only must be true")

    if proof.get("authoritative_reconcile_surface") != "fresh_enumerate_devices_snapshot":
        _fail(errors, "authoritative_reconcile_surface must be fresh_enumerate_devices_snapshot")

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

    expected_ids = set(CAPTURE_RESILIENCE_SMOKE_SCENARIO_IDS)
    if set(scenario_map.keys()) != expected_ids:
        _fail(errors, f"proof scenario IDs must match smoke IDs: {sorted(expected_ids)}")

    if target_scenario == "all":
        expected_total = len(CAPTURE_RESILIENCE_SMOKE_SCENARIO_IDS)
        if proof.get("scenarios_total") != expected_total:
            _fail(errors, f"scenarios_total must be {expected_total}")
        if proof.get("scenarios_passed") != expected_total:
            _fail(errors, f"scenarios_passed must be {expected_total}")
        targets = list(CAPTURE_RESILIENCE_SMOKE_SCENARIO_IDS)
    else:
        targets = [target_scenario]

    for scenario_id in targets:
        payload = scenario_map.get(scenario_id)
        if payload is None:
            _fail(errors, f"{scenario_id}: missing in proof payload")
            continue
        _validate_scenario(errors, scenario_id, payload)

    return errors


def run_ci_simulation() -> int:
    target_scenario = os.getenv("FLEXPHONE_WEBRTC_CAPTURE_CI_SCENARIO", "all").strip()
    if target_scenario not in VALID_SCENARIOS:
        print(
            "WebRTC capture resilience CI simulation: FAILED - "
            f"unsupported FLEXPHONE_WEBRTC_CAPTURE_CI_SCENARIO={target_scenario!r}; "
            f"expected one of {sorted(VALID_SCENARIOS)}"
        )
        return 1

    print(f"WebRTC capture resilience CI simulation scenario={target_scenario}")
    proof_obj = run_webrtc_capture_resilience_sandbox_smoke(return_proof=True)
    if not isinstance(proof_obj, dict):
        print("WebRTC capture resilience CI simulation: FAILED - runner did not return proof payload")
        return 1

    errors = _validate_contract(target_scenario, proof_obj)
    if errors:
        print("WebRTC capture resilience CI simulation: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print(f"dependent smoke marker: {CAPTURE_RESILIENCE_SMOKE_SUCCESS_MARKER}")
    print(f"WebRTC capture resilience CI simulation scenario={target_scenario}: OK")
    print(CI_SUCCESS_MARKER)
    return 0


def main() -> int:
    try:
        return run_ci_simulation()
    except CaptureResilienceSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"WebRTC capture resilience CI simulation: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"WebRTC capture resilience CI simulation: FAILED (unexpected) - {exc!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

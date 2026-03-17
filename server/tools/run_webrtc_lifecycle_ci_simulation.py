from __future__ import annotations

import os
from typing import Any

from run_webrtc_lifecycle_sandbox_smoke import (
    WebRTCLifecycleSmokeError,
    run_webrtc_lifecycle_sandbox_smoke,
)


VALID_SCENARIOS = {
    "all",
    "A_happy_path_lifecycle",
    "B_glare_collision_roles",
    "C_transient_disconnect_recovery",
    "D_failed_ice_restart_recovery",
    "E_late_signaling_ignored",
    "F_close_during_pending_recovery",
}

EXPECTED_ASSERTIONS: dict[str, dict[str, Any]] = {
    "A_happy_path_lifecycle": {
        "end_state": "session_closed",
        "deterministic_action": "normal_lifecycle_progression",
    },
    "B_glare_collision_roles": {
        "end_state": {"polite": "session_negotiating", "impolite": "session_connected"},
        "role_actions": {"polite": "rollback_then_apply_remote_offer", "impolite": "ignore_incoming_offer"},
    },
    "C_transient_disconnect_recovery": {
        "end_state": "session_connected",
        "deterministic_action": "observe_then_reconnect_wait",
    },
    "D_failed_ice_restart_recovery": {
        "end_state": "session_connected",
        "deterministic_action": "start_ice_restart_negotiation",
    },
    "E_late_signaling_ignored": {
        "end_state": "session_connected",
        "deterministic_action": "ignore_and_log_late_answer",
    },
    "F_close_during_pending_recovery": {
        "end_state": "session_closed",
        "deterministic_action": "reject_signal_terminal",
    },
}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _assert_eq(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        _fail(errors, f"{label}: expected {expected!r}, got {actual!r}")


def _validate_scenario_payload(errors: list[str], scenario: dict[str, Any]) -> None:
    scenario_id = scenario.get("scenario_id")
    if scenario_id not in EXPECTED_ASSERTIONS:
        _fail(errors, f"Unexpected scenario_id in proof: {scenario_id!r}")
        return

    if scenario.get("status") != "PASS":
        _fail(errors, f"{scenario_id}: status must be PASS")

    expected = EXPECTED_ASSERTIONS[scenario_id]
    for key, expected_value in expected.items():
        _assert_eq(errors, f"{scenario_id}.{key}", scenario.get(key), expected_value)


def _validate_contract(target_scenario: str, proof: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if proof.get("overall_status") != "PASS":
        _fail(errors, "overall_status must be PASS")

    scenarios_payload = proof.get("scenarios")
    if not isinstance(scenarios_payload, list):
        _fail(errors, "proof.scenarios must be list")
        return errors

    scenario_map: dict[str, dict[str, Any]] = {}
    for entry in scenarios_payload:
        if not isinstance(entry, dict):
            _fail(errors, "proof.scenarios entries must be objects")
            continue
        scenario_id = entry.get("scenario_id")
        if not isinstance(scenario_id, str):
            _fail(errors, "proof.scenarios entry must define scenario_id string")
            continue
        scenario_map[scenario_id] = entry

    missing = sorted(set(EXPECTED_ASSERTIONS.keys()) - set(scenario_map.keys()))
    if missing:
        _fail(errors, f"proof missing scenario results: {missing}")

    if target_scenario == "all":
        expected_total = len(EXPECTED_ASSERTIONS)
        _assert_eq(errors, "scenarios_total", proof.get("scenarios_total"), expected_total)
        _assert_eq(errors, "scenarios_passed", proof.get("scenarios_passed"), expected_total)
        scenarios_to_validate = list(EXPECTED_ASSERTIONS.keys())
    else:
        scenarios_to_validate = [target_scenario]

    for scenario_id in scenarios_to_validate:
        payload = scenario_map.get(scenario_id)
        if payload is None:
            _fail(errors, f"{scenario_id}: missing in proof payload")
            continue
        _validate_scenario_payload(errors, payload)

    return errors


def run_ci_simulation() -> int:
    target_scenario = os.getenv("FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO", "all").strip()
    if target_scenario not in VALID_SCENARIOS:
        print(
            "WebRTC lifecycle CI simulation: FAILED - "
            f"unsupported FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO={target_scenario!r}; "
            f"expected one of {sorted(VALID_SCENARIOS)}"
        )
        return 1

    print(f"WebRTC lifecycle CI simulation scenario={target_scenario}")
    proof_obj = run_webrtc_lifecycle_sandbox_smoke(return_proof=True)
    if not isinstance(proof_obj, dict):
        print("WebRTC lifecycle CI simulation: FAILED - runner did not return proof payload")
        return 1

    errors = _validate_contract(target_scenario, proof_obj)
    if errors:
        print("WebRTC lifecycle CI simulation: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print(f"WebRTC lifecycle CI simulation scenario={target_scenario}: OK")
    return 0


def main() -> int:
    try:
        return run_ci_simulation()
    except WebRTCLifecycleSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"WebRTC lifecycle CI simulation: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"WebRTC lifecycle CI simulation: FAILED (unexpected) - {exc!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

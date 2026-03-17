from __future__ import annotations


CI_LIFECYCLE_SCENARIO_IDS = (
    "A_happy_path_lifecycle",
    "B_glare_collision_roles",
    "C_transient_disconnect_recovery",
    "D_failed_ice_restart_recovery",
    "E_late_signaling_ignored",
    "F_close_during_pending_recovery",
)

CI_LIFECYCLE_REQUIRED_ASSERTIONS = {
    "A_happy_path_lifecycle": {
        "expected_end_state": "session_closed",
        "expected_action": "normal_lifecycle_progression",
    },
    "B_glare_collision_roles": {
        "expected_end_state_polite": "session_negotiating",
        "expected_end_state_impolite": "session_connected",
        "expected_polite_action": "rollback_then_apply_remote_offer",
        "expected_impolite_action": "ignore_incoming_offer",
    },
    "C_transient_disconnect_recovery": {
        "expected_end_state": "session_connected",
        "expected_action": "observe_then_reconnect_wait",
    },
    "D_failed_ice_restart_recovery": {
        "expected_end_state": "session_connected",
        "expected_action": "start_ice_restart_negotiation",
    },
    "E_late_signaling_ignored": {
        "expected_end_state": "session_connected",
        "expected_action": "ignore_and_log_late_answer",
    },
    "F_close_during_pending_recovery": {
        "expected_end_state": "session_closed",
        "expected_action": "reject_signal_terminal",
    },
}

CI_LIFECYCLE_FAIL_CONDITIONS = (
    "scenario_missing_or_unexpected",
    "scenario_status_not_pass",
    "forbidden_terminal_state_mismatch",
    "glare_role_action_mismatch",
    "failed_restart_contract_breach",
    "late_or_stale_signal_ownership_breach",
    "proof_payload_incomplete_or_nondeterministic",
)

CI_LIFECYCLE_INVARIANTS = {
    "ci_gate_reuses_24_5_scenario_matrix": True,
    "contract_breach_returns_nonzero_exit": True,
    "no_forbidden_state_transitions": True,
    "closed_session_stays_terminal": True,
    "production_runtime_path_unchanged": True,
}

WORKFLOW_BASELINE = {
    "workflow_path": ".github/workflows/webrtc-lifecycle-ci.yml",
    "job_name": "webrtc-lifecycle-gate",
    "matrix_scenarios": CI_LIFECYCLE_SCENARIO_IDS,
    "runner_script": "server/tools/run_webrtc_lifecycle_ci_simulation.py",
}


def validate_webrtc_lifecycle_ci_gate_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_session_lifecycle_hardening_baseline import (
        STAGE24_SUBSTEP_DRAFT,
        STAGE24_VERIFICATION_TYPES,
    )
    from app.webrtc_peer_session_state_inventory import TERMINAL_STATES
    from app.webrtc_negotiation_glare_resolution_contract import (
        DETERMINISTIC_SIGNALING_CASE_ACTIONS,
    )
    from app.webrtc_reconnect_ice_restart_pending_recovery_contract import (
        DETERMINISTIC_RECOVERY_CASE_ACTIONS,
    )

    if STAGE24_SUBSTEP_DRAFT.get("24.5") != "lifecycle_sandbox_smoke_baseline":
        errors.append("Step 24.1 substep draft must keep 24.5 lifecycle sandbox smoke milestone")
    if STAGE24_SUBSTEP_DRAFT.get("24.6") != "lifecycle_ci_gate_baseline":
        errors.append("Step 24.1 substep draft must keep 24.6 lifecycle CI gate milestone")
    if STAGE24_VERIFICATION_TYPES.get("24.6") != "build check":
        errors.append("Step 24 verification map must define 24.6 as build check")

    if set(CI_LIFECYCLE_REQUIRED_ASSERTIONS.keys()) != set(CI_LIFECYCLE_SCENARIO_IDS):
        errors.append("CI_LIFECYCLE_REQUIRED_ASSERTIONS must cover all scenario IDs")

    for scenario_id in CI_LIFECYCLE_SCENARIO_IDS:
        if not scenario_id.startswith(("A_", "B_", "C_", "D_", "E_", "F_")):
            errors.append(f"{scenario_id}: unexpected scenario id prefix")

    if "session_closed" not in TERMINAL_STATES:
        errors.append("Step 24.2 terminal states must include session_closed")
    if "session_failed" not in TERMINAL_STATES:
        errors.append("Step 24.2 terminal states must include session_failed")

    if (
        DETERMINISTIC_SIGNALING_CASE_ACTIONS["glare_offer_collision"]["polite"]
        != CI_LIFECYCLE_REQUIRED_ASSERTIONS["B_glare_collision_roles"]["expected_polite_action"]
    ):
        errors.append("Step 24.3 polite glare action mismatch vs 24.6 expected assertion")
    if (
        DETERMINISTIC_SIGNALING_CASE_ACTIONS["glare_offer_collision"]["impolite"]
        != CI_LIFECYCLE_REQUIRED_ASSERTIONS["B_glare_collision_roles"]["expected_impolite_action"]
    ):
        errors.append("Step 24.3 impolite glare action mismatch vs 24.6 expected assertion")

    if (
        DETERMINISTIC_RECOVERY_CASE_ACTIONS["failed_ice_state"]
        != CI_LIFECYCLE_REQUIRED_ASSERTIONS["D_failed_ice_restart_recovery"]["expected_action"]
    ):
        errors.append("Step 24.4 failed_ice_state action mismatch vs 24.6 expected assertion")
    if (
        DETERMINISTIC_RECOVERY_CASE_ACTIONS["signal_received_for_closed_session"]
        != CI_LIFECYCLE_REQUIRED_ASSERTIONS["F_close_during_pending_recovery"]["expected_action"]
    ):
        errors.append("Step 24.4 closed-session signal action mismatch vs 24.6 expected assertion")

    required_invariants = {
        "ci_gate_reuses_24_5_scenario_matrix": True,
        "contract_breach_returns_nonzero_exit": True,
        "no_forbidden_state_transitions": True,
        "closed_session_stays_terminal": True,
        "production_runtime_path_unchanged": True,
    }
    if CI_LIFECYCLE_INVARIANTS != required_invariants:
        errors.append("CI_LIFECYCLE_INVARIANTS must match canonical invariant set")

    required_workflow_baseline = {
        "workflow_path": ".github/workflows/webrtc-lifecycle-ci.yml",
        "job_name": "webrtc-lifecycle-gate",
        "matrix_scenarios": CI_LIFECYCLE_SCENARIO_IDS,
        "runner_script": "server/tools/run_webrtc_lifecycle_ci_simulation.py",
    }
    if WORKFLOW_BASELINE != required_workflow_baseline:
        errors.append("WORKFLOW_BASELINE must match lifecycle CI workflow baseline")

    if len(CI_LIFECYCLE_FAIL_CONDITIONS) < 6:
        errors.append("CI_LIFECYCLE_FAIL_CONDITIONS must include full baseline failure classes")

    return errors

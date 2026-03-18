from __future__ import annotations


CI_CAPTURE_RESILIENCE_SCENARIO_IDS = (
    "A_permission_drift_device_capture",
    "B_hardware_device_drift",
    "C_direct_local_stop",
    "D_temporary_display_interruption",
    "E_permanent_display_loss",
    "F_fallback_refresh_without_devicechange",
    "G_device_reacquire_after_terminal",
    "H_display_reacquire_after_terminal",
)

CI_CAPTURE_RESILIENCE_REQUIRED_ASSERTIONS = {
    "A_permission_drift_device_capture": {
        "required_authoritative_surfaces": (
            "MediaStreamTrack.readyState",
            "MediaDevices.enumerateDevices_snapshot",
        ),
        "required_forbidden_checks": (
            "permission_drift_is_not_user_mute",
            "terminal_capture_not_treated_as_temporary_mute",
        ),
    },
    "B_hardware_device_drift": {
        "required_authoritative_surfaces": (
            "MediaDevices.enumerateDevices_snapshot",
        ),
        "required_forbidden_checks": (
            "no_truth_assumption_from_missing_devicechange_event",
            "snapshot_absence_not_absolute_os_hardware_absence",
        ),
    },
    "C_direct_local_stop": {
        "required_authoritative_surfaces": (
            "MediaStreamTrack.readyState",
        ),
        "required_forbidden_checks": (
            "no_wait_for_ended_event_after_direct_stop",
        ),
    },
    "D_temporary_display_interruption": {
        "required_authoritative_surfaces": (
            "MediaStreamTrack.mute_unmute_events",
            "MediaStreamTrack.readyState",
        ),
        "required_forbidden_checks": (
            "temporary_display_mute_not_treated_as_terminal_end",
            "no_inventory_reselection_for_temporary_display_interrupt",
        ),
    },
    "E_permanent_display_loss": {
        "required_authoritative_surfaces": (
            "MediaStreamTrack.readyState",
            "MediaStreamTrack.ended_event_path",
        ),
        "required_forbidden_checks": (
            "no_recovery_via_enumerateDevices_or_devicechange",
            "no_automatic_display_source_switch_without_user_mediation",
        ),
    },
    "F_fallback_refresh_without_devicechange": {
        "required_authoritative_surfaces": (
            "MediaDevices.enumerateDevices_snapshot",
        ),
        "required_forbidden_checks": (
            "devicechange_not_required_for_correctness",
        ),
    },
    "G_device_reacquire_after_terminal": {
        "required_authoritative_surfaces": (
            "MediaStreamTrack.readyState",
            "fresh_getUserMedia_result",
        ),
        "required_forbidden_checks": (
            "ended_track_not_revived_in_place",
        ),
    },
    "H_display_reacquire_after_terminal": {
        "required_authoritative_surfaces": (
            "MediaStreamTrack.readyState",
            "fresh_getDisplayMedia_result",
        ),
        "required_forbidden_checks": (
            "no_display_reacquire_via_inventory_refresh",
            "no_persistent_display_granted_assumption",
        ),
    },
}

CI_CAPTURE_RESILIENCE_FAIL_CONDITIONS = (
    "scenario_missing_or_unexpected",
    "scenario_status_not_pass",
    "required_assertion_marker_missing",
    "devicechange_treated_as_authoritative_truth",
    "authoritative_reconcile_surface_mismatch",
    "direct_stop_terminal_boundary_breach",
    "display_source_non_enumerable_boundary_breach",
    "proof_payload_incomplete_or_nondeterministic",
)

CI_CAPTURE_RESILIENCE_INVARIANTS = {
    "ci_validates_contract_transitions_not_real_hardware_quirks": True,
    "ci_requires_no_physical_capture_devices": True,
    "ci_requires_no_permission_prompt_or_display_picker": True,
    "ci_requires_no_real_devicechange_delivery": True,
    "ci_contract_breach_returns_nonzero_exit": True,
    "production_runtime_path_unchanged": True,
}

WORKFLOW_BASELINE = {
    "workflow_path": ".github/workflows/webrtc-capture-resilience-ci.yml",
    "job_name": "webrtc-capture-resilience-gate",
    "runner_script": "server/tools/run_webrtc_capture_resilience_ci_simulation.py",
}


def validate_webrtc_capture_resilience_ci_gate_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_capture_source_device_permission_resilience_baseline import (
        STAGE26_SUBSTEP_DRAFT,
        STAGE26_VERIFICATION_TYPES,
    )
    from app.webrtc_device_change_reconciliation_baseline import (
        AUTHORITATIVE_RECONCILIATION_SURFACE,
        DEVICECHANGE_ADVISORY_TRIGGER_CONTRACT,
    )
    from app.webrtc_media_device_inventory_permission_gated_visibility_contract_baseline import (
        MEDIA_DEVICE_INVENTORY_AUTHORITY_SURFACE,
    )
    from app.webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline import (
        DISPLAY_SOURCE_MODEL_CONTRACT,
        DISPLAY_SOURCE_RESELECTION_CONTRACT,
    )
    from app.webrtc_track_source_termination_semantics_baseline import (
        DIRECT_STOP_PATH_CONTRACT,
    )
    from tools.run_webrtc_capture_resilience_sandbox_smoke import (
        CAPTURE_RESILIENCE_SMOKE_SCENARIO_IDS,
    )

    if STAGE26_SUBSTEP_DRAFT.get("26.6") != "capture_resilience_sandbox_smoke_baseline":
        errors.append("Stage 26 draft must keep 26.6 sandbox smoke milestone")
    if STAGE26_SUBSTEP_DRAFT.get("26.7") != "capture_resilience_ci_gate_baseline":
        errors.append("Stage 26 draft must keep 26.7 CI gate milestone")
    if STAGE26_VERIFICATION_TYPES.get("26.7") != "build check":
        errors.append("Stage 26 verification map must define 26.7 as build check")

    if tuple(CAPTURE_RESILIENCE_SMOKE_SCENARIO_IDS) != CI_CAPTURE_RESILIENCE_SCENARIO_IDS:
        errors.append("CI_CAPTURE_RESILIENCE_SCENARIO_IDS must match 26.6 smoke scenario IDs")

    if set(CI_CAPTURE_RESILIENCE_REQUIRED_ASSERTIONS.keys()) != set(CI_CAPTURE_RESILIENCE_SCENARIO_IDS):
        errors.append("CI_CAPTURE_RESILIENCE_REQUIRED_ASSERTIONS must cover all CI scenarios")

    if DEVICECHANGE_ADVISORY_TRIGGER_CONTRACT.get("devicechange_required_for_correctness") is not False:
        errors.append("26.5 must keep devicechange non-required for correctness")

    if AUTHORITATIVE_RECONCILIATION_SURFACE.get("reconciliation_source") != "fresh_enumerate_devices_snapshot":
        errors.append("26.5 authoritative reconciliation source mismatch vs 26.7 expectations")

    if MEDIA_DEVICE_INVENTORY_AUTHORITY_SURFACE.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("26.2 inventory authority must remain enumerateDevices")

    if DISPLAY_SOURCE_MODEL_CONTRACT.get("display_sources_enumerable_via_enumerateDevices") is not False:
        errors.append("26.4 must keep display source model non-enumerable")

    if DISPLAY_SOURCE_RESELECTION_CONTRACT.get("source_change_without_user_interaction_allowed") is not False:
        errors.append("26.4 must keep source change without user interaction disabled")

    if DIRECT_STOP_PATH_CONTRACT.get("ended_event_required") is not False:
        errors.append("26.3 direct stop path must keep ended_event_required=false")

    required_invariants = {
        "ci_validates_contract_transitions_not_real_hardware_quirks": True,
        "ci_requires_no_physical_capture_devices": True,
        "ci_requires_no_permission_prompt_or_display_picker": True,
        "ci_requires_no_real_devicechange_delivery": True,
        "ci_contract_breach_returns_nonzero_exit": True,
        "production_runtime_path_unchanged": True,
    }
    if CI_CAPTURE_RESILIENCE_INVARIANTS != required_invariants:
        errors.append("CI_CAPTURE_RESILIENCE_INVARIANTS must match canonical invariant set")

    if len(CI_CAPTURE_RESILIENCE_FAIL_CONDITIONS) < 7:
        errors.append("CI_CAPTURE_RESILIENCE_FAIL_CONDITIONS must include full failure-class baseline")

    required_workflow = {
        "workflow_path": ".github/workflows/webrtc-capture-resilience-ci.yml",
        "job_name": "webrtc-capture-resilience-gate",
        "runner_script": "server/tools/run_webrtc_capture_resilience_ci_simulation.py",
    }
    if WORKFLOW_BASELINE != required_workflow:
        errors.append("WORKFLOW_BASELINE must match capture resilience CI workflow baseline")

    return errors

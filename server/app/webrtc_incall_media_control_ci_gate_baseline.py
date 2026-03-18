from __future__ import annotations


CI_INCALL_MEDIA_CONTROL_SCENARIO_IDS = (
    "A_user_mute_unmute",
    "B_source_switch_replace_track",
    "C_transceiver_direction_desired_vs_effective",
    "D_sender_parameters_boundary",
    "E_quality_observability_getstats",
    "F_late_controls_after_close",
    "G_required_optional_stats_gate_semantics",
)

CI_INCALL_MEDIA_CONTROL_REQUIRED_ASSERTIONS = {
    "A_user_mute_unmute": {
        "required_assertions": (
            "user_mute_uses_track_enabled",
            "user_mute_not_equal_source_mute",
        ),
    },
    "B_source_switch_replace_track": {
        "required_assertions": (
            "replace_track_authoritative",
            "invalid_kind_rejected",
            "late_abort_non_mutating",
        ),
    },
    "C_transceiver_direction_desired_vs_effective": {
        "required_assertions": (
            "direction_currentDirection_distinct",
            "negotiation_commit_required_for_effective_change",
        ),
    },
    "D_sender_parameters_boundary": {
        "required_assertions": (
            "supported_update_applied",
            "unsupported_and_out_of_envelope_rejected",
            "terminal_session_rejects_mutation",
        ),
    },
    "E_quality_observability_getstats": {
        "required_assertions": (
            "required_stat_types_present",
            "required_metrics_present",
            "limited_metrics_non_gating",
        ),
    },
    "F_late_controls_after_close": {
        "required_assertions": (
            "closed_session_rejects_media_mutation",
            "state_integrity_preserved",
        ),
    },
    "G_required_optional_stats_gate_semantics": {
        "required_assertions": (
            "required_stat_types_match_25_5",
            "optional_non_gating_metrics_do_not_fail_gate",
        ),
    },
}

CI_INCALL_MEDIA_CONTROL_FAIL_CONDITIONS = (
    "scenario_missing_or_unexpected",
    "scenario_status_not_pass",
    "required_assertion_missing_or_false",
    "replace_track_boundary_breach",
    "direction_desired_effective_boundary_breach",
    "sender_parameter_boundary_breach",
    "required_vs_optional_stats_gate_breach",
    "proof_payload_incomplete_or_nondeterministic",
)

CI_INCALL_MEDIA_CONTROL_INVARIANTS = {
    "ci_gate_reuses_25_6_sandbox_smoke_scenarios": True,
    "contract_breach_returns_nonzero_exit": True,
    "required_stats_types_remain_gating": True,
    "limited_availability_metrics_remain_non_gating": True,
    "no_external_network_or_device_dependency": True,
    "production_runtime_path_unchanged": True,
}

WORKFLOW_BASELINE = {
    "workflow_path": ".github/workflows/webrtc-incall-media-control-ci.yml",
    "job_name": "webrtc-incall-media-control-gate",
    "runner_script": "server/tools/run_webrtc_incall_media_control_ci_simulation.py",
}


def validate_webrtc_incall_media_control_ci_gate_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_incall_media_control_quality_observability_baseline import (
        STAGE25_SUBSTEP_DRAFT,
        STAGE25_VERIFICATION_TYPES,
    )
    from app.webrtc_incall_quality_observability_baseline import (
        LIMITED_AVAILABILITY_NON_GATING_METRICS,
        QUALITY_STATS_SURFACE_BASELINE,
    )
    from app.webrtc_mute_unmute_source_switch_transceiver_direction_contract import (
        DETERMINISTIC_OPERATION_CASE_ACTIONS,
    )
    from app.webrtc_sender_parameters_bitrate_codec_boundary_contract import (
        DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS,
    )
    from tools.run_webrtc_incall_media_control_sandbox_smoke import (
        INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS,
    )

    if STAGE25_SUBSTEP_DRAFT.get("25.6") != "incall_media_control_sandbox_smoke_baseline":
        errors.append("Step 25.1 substep draft must keep 25.6 sandbox smoke milestone")
    if STAGE25_SUBSTEP_DRAFT.get("25.7") != "incall_media_control_ci_gate_baseline":
        errors.append("Step 25.1 substep draft must keep 25.7 CI gate milestone")
    if STAGE25_VERIFICATION_TYPES.get("25.7") != "build check":
        errors.append("Step 25 verification map must define 25.7 as build check")

    required_scenario_ids = {
        *INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS,
        "G_required_optional_stats_gate_semantics",
    }
    if set(CI_INCALL_MEDIA_CONTROL_SCENARIO_IDS) != required_scenario_ids:
        errors.append("CI_INCALL_MEDIA_CONTROL_SCENARIO_IDS must cover 25.6 A-F plus CI-only G scenario")

    if set(CI_INCALL_MEDIA_CONTROL_REQUIRED_ASSERTIONS.keys()) != set(CI_INCALL_MEDIA_CONTROL_SCENARIO_IDS):
        errors.append("CI_INCALL_MEDIA_CONTROL_REQUIRED_ASSERTIONS must cover all CI scenarios")

    if DETERMINISTIC_OPERATION_CASE_ACTIONS.get("source_switch_invalid_kind") != "reject_switch_and_keep_previous_track":
        errors.append("Step 25.3 source_switch_invalid_kind action mismatch vs 25.7 expectations")
    if DETERMINISTIC_OPERATION_CASE_ACTIONS.get("source_switch_late_abort") != "ignore_abort_and_log_without_state_corruption":
        errors.append("Step 25.3 source_switch_late_abort action mismatch vs 25.7 expectations")

    if (
        DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS.get("sender_parameter_update_out_of_envelope")
        != "reject_and_require_renegotiation"
    ):
        errors.append("Step 25.4 out_of_envelope sender action mismatch vs 25.7 expectations")
    if (
        DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS.get("sender_parameter_update_terminal_session")
        != "reject_terminal_session_mutation"
    ):
        errors.append("Step 25.4 terminal sender action mismatch vs 25.7 expectations")

    if QUALITY_STATS_SURFACE_BASELINE.get("required_stat_types") != (
        "candidate-pair",
        "outbound-rtp",
        "inbound-rtp",
    ):
        errors.append("Step 25.5 required_stat_types mismatch vs 25.7 expected gate semantics")

    if len(LIMITED_AVAILABILITY_NON_GATING_METRICS) < 2:
        errors.append("Step 25.5 must define limited non-gating metrics for CI optional handling")

    required_invariants = {
        "ci_gate_reuses_25_6_sandbox_smoke_scenarios": True,
        "contract_breach_returns_nonzero_exit": True,
        "required_stats_types_remain_gating": True,
        "limited_availability_metrics_remain_non_gating": True,
        "no_external_network_or_device_dependency": True,
        "production_runtime_path_unchanged": True,
    }
    if CI_INCALL_MEDIA_CONTROL_INVARIANTS != required_invariants:
        errors.append("CI_INCALL_MEDIA_CONTROL_INVARIANTS must match canonical invariant set")

    if len(CI_INCALL_MEDIA_CONTROL_FAIL_CONDITIONS) < 7:
        errors.append("CI_INCALL_MEDIA_CONTROL_FAIL_CONDITIONS must include full baseline failure classes")

    required_workflow_baseline = {
        "workflow_path": ".github/workflows/webrtc-incall-media-control-ci.yml",
        "job_name": "webrtc-incall-media-control-gate",
        "runner_script": "server/tools/run_webrtc_incall_media_control_ci_simulation.py",
    }
    if WORKFLOW_BASELINE != required_workflow_baseline:
        errors.append("WORKFLOW_BASELINE must match in-call media-control CI workflow baseline")

    return errors

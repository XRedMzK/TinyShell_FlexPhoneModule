from __future__ import annotations


OUTPUT_ROUTE_STATE_SCHEMA_27_4 = {
    "effective_sink_id": "str_empty_string_means_default",
    "preferred_sink_id": "str_empty_string_means_default_or_no_override",
    "rebind_status": (
        "bound",
        "fallback_default",
        "pending_rebind",
        "rebind_required_user_activation",
        "permission_blocked",
        "unsupported",
    ),
    "last_route_error_class": (
        None,
        "not_found",
        "abort",
        "not_allowed",
        "invalid_state",
        "unsupported",
    ),
}

STALE_SINK_DETECTION_RULES_27_4 = {
    "stale_sink_condition": "preferred_non_default_missing_in_audiooutput_snapshot",
    "stale_sink_requires_default_fallback_attempt": True,
    "devicechange_required_for_stale_detection": False,
    "authoritative_detection_surface": "fresh_enumerate_devices_snapshot",
}

FALLBACK_TO_DEFAULT_RULES_27_4 = {
    "fallback_call": "HTMLMediaElement.setSinkId_empty_string",
    "fallback_success_effective_sink_is_default": True,
    "fallback_preserves_preferred_sink": True,
    "fallback_sets_pending_rebind_status": True,
    "fallback_erases_preference": False,
}

APPLY_FAILURE_CLASSIFICATION_RULES_27_4 = {
    "NotFoundError": "stale_sink_missing",
    "AbortError": "sink_switch_failed",
    "NotAllowedError": "permission_blocked_not_sink_loss",
}

REBIND_MODE_RULES_27_4 = {
    "passive_rebind": {
        "trigger": "preferred_sink_visible_again_in_snapshot",
        "requires_user_activation": False,
        "action": "setSinkId_preferred_sink",
        "success_status": "bound",
    },
    "interactive_rebind": {
        "trigger": "explicit_user_restore_action",
        "requires_user_activation": True,
        "selection_action": "selectAudioOutput_with_preferred_hint",
        "apply_action": "setSinkId_selected_or_rotated_id",
        "may_rotate_preferred_sink_id": True,
        "allowed_in_background_reconcile": False,
    },
}

DETERMINISTIC_TRANSITION_RULES_27_4 = {
    "bound_plus_apply_not_found": "attempt_default_fallback_then_pending_rebind",
    "bound_plus_apply_abort": "attempt_default_fallback_then_pending_rebind",
    "bound_plus_stale_detected": "attempt_default_fallback_then_pending_rebind",
    "pending_rebind_plus_passive_candidate_visible": "attempt_passive_rebind",
    "pending_rebind_plus_user_restore_action": "interactive_rebind_flow",
    "permission_blocked_branch_not_merged_with_sink_loss": True,
}

OUTPUT_DEVICE_LOSS_REBIND_CONTRACT_INVARIANTS_27_4 = {
    "stale_or_apply_failure_notfound_abort_converges_to_fallback_branch": True,
    "successful_fallback_sets_effective_default_and_preserves_preference": True,
    "interactive_rebind_requires_explicit_user_activation": True,
    "no_background_selectaudiooutput_invocation": True,
    "devicechange_advisory_not_correctness_primitive": True,
    "production_runtime_change_allowed_in_27_4": False,
}

STAGE27_CLOSURE_CRITERIA_27_4 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "stale_detection_fallback_rebind_rules_defined",
    "preferred_vs_effective_state_split_explicit",
    "dependency_alignment_with_27_1_27_2_27_3_checker_enforced",
    "checker_and_compileall_pass",
)


def validate_webrtc_output_device_loss_fallback_rebinding_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_audio_output_remote_playout_route_resilience_baseline import (
        OUTPUT_RECONCILIATION_MODEL,
        OUTPUT_ROUTE_FALLBACK_RULES,
        STAGE27_SUBSTEP_DRAFT,
        STAGE27_VERIFICATION_TYPES,
    )
    from app.webrtc_output_device_inventory_permission_policy_visibility_contract_baseline import (
        OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE,
        OUTPUT_VISIBILITY_PATHS,
    )
    from app.webrtc_sink_selection_apply_semantics_error_class_contract_baseline import (
        APPLY_ERROR_CLASS_MATRIX,
        PERSISTED_SINK_REVALIDATION_RULES,
        SINK_SELECTION_APPLY_PHASE_MODEL,
    )

    required_state_schema = {
        "effective_sink_id": "str_empty_string_means_default",
        "preferred_sink_id": "str_empty_string_means_default_or_no_override",
        "rebind_status": (
            "bound",
            "fallback_default",
            "pending_rebind",
            "rebind_required_user_activation",
            "permission_blocked",
            "unsupported",
        ),
        "last_route_error_class": (
            None,
            "not_found",
            "abort",
            "not_allowed",
            "invalid_state",
            "unsupported",
        ),
    }
    if OUTPUT_ROUTE_STATE_SCHEMA_27_4 != required_state_schema:
        errors.append("OUTPUT_ROUTE_STATE_SCHEMA_27_4 must match canonical state schema")

    required_stale_rules = {
        "stale_sink_condition": "preferred_non_default_missing_in_audiooutput_snapshot",
        "stale_sink_requires_default_fallback_attempt": True,
        "devicechange_required_for_stale_detection": False,
        "authoritative_detection_surface": "fresh_enumerate_devices_snapshot",
    }
    if STALE_SINK_DETECTION_RULES_27_4 != required_stale_rules:
        errors.append("STALE_SINK_DETECTION_RULES_27_4 must match canonical stale detection rules")

    required_fallback_rules = {
        "fallback_call": "HTMLMediaElement.setSinkId_empty_string",
        "fallback_success_effective_sink_is_default": True,
        "fallback_preserves_preferred_sink": True,
        "fallback_sets_pending_rebind_status": True,
        "fallback_erases_preference": False,
    }
    if FALLBACK_TO_DEFAULT_RULES_27_4 != required_fallback_rules:
        errors.append("FALLBACK_TO_DEFAULT_RULES_27_4 must match canonical fallback rules")

    required_apply_failure_classification = {
        "NotFoundError": "stale_sink_missing",
        "AbortError": "sink_switch_failed",
        "NotAllowedError": "permission_blocked_not_sink_loss",
    }
    if APPLY_FAILURE_CLASSIFICATION_RULES_27_4 != required_apply_failure_classification:
        errors.append(
            "APPLY_FAILURE_CLASSIFICATION_RULES_27_4 must match canonical apply failure classification"
        )

    required_rebind_modes = {
        "passive_rebind": {
            "trigger": "preferred_sink_visible_again_in_snapshot",
            "requires_user_activation": False,
            "action": "setSinkId_preferred_sink",
            "success_status": "bound",
        },
        "interactive_rebind": {
            "trigger": "explicit_user_restore_action",
            "requires_user_activation": True,
            "selection_action": "selectAudioOutput_with_preferred_hint",
            "apply_action": "setSinkId_selected_or_rotated_id",
            "may_rotate_preferred_sink_id": True,
            "allowed_in_background_reconcile": False,
        },
    }
    if REBIND_MODE_RULES_27_4 != required_rebind_modes:
        errors.append("REBIND_MODE_RULES_27_4 must match canonical passive/interactive modes")

    required_transition_rules = {
        "bound_plus_apply_not_found": "attempt_default_fallback_then_pending_rebind",
        "bound_plus_apply_abort": "attempt_default_fallback_then_pending_rebind",
        "bound_plus_stale_detected": "attempt_default_fallback_then_pending_rebind",
        "pending_rebind_plus_passive_candidate_visible": "attempt_passive_rebind",
        "pending_rebind_plus_user_restore_action": "interactive_rebind_flow",
        "permission_blocked_branch_not_merged_with_sink_loss": True,
    }
    if DETERMINISTIC_TRANSITION_RULES_27_4 != required_transition_rules:
        errors.append("DETERMINISTIC_TRANSITION_RULES_27_4 must match canonical transition rules")

    required_invariants = {
        "stale_or_apply_failure_notfound_abort_converges_to_fallback_branch": True,
        "successful_fallback_sets_effective_default_and_preserves_preference": True,
        "interactive_rebind_requires_explicit_user_activation": True,
        "no_background_selectaudiooutput_invocation": True,
        "devicechange_advisory_not_correctness_primitive": True,
        "production_runtime_change_allowed_in_27_4": False,
    }
    if OUTPUT_DEVICE_LOSS_REBIND_CONTRACT_INVARIANTS_27_4 != required_invariants:
        errors.append(
            "OUTPUT_DEVICE_LOSS_REBIND_CONTRACT_INVARIANTS_27_4 must match canonical invariant set"
        )

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "stale_detection_fallback_rebind_rules_defined",
        "preferred_vs_effective_state_split_explicit",
        "dependency_alignment_with_27_1_27_2_27_3_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE27_CLOSURE_CRITERIA_27_4 != required_closure:
        errors.append("STAGE27_CLOSURE_CRITERIA_27_4 must match closure criteria")

    if STAGE27_SUBSTEP_DRAFT.get("27.4") != "output_device_loss_fallback_rebinding_contract":
        errors.append("Stage 27 draft must define 27.4 output-device-loss contract milestone")

    if STAGE27_VERIFICATION_TYPES.get("27.4") != "build check":
        errors.append("Stage 27 verification map must keep 27.4 as build check")

    if OUTPUT_RECONCILIATION_MODEL.get("devicechange_required_for_correctness") is not False:
        errors.append("27.1 reconcile model must keep devicechange non-required for correctness")

    if OUTPUT_ROUTE_FALLBACK_RULES.get("sink_apply_abort_error") != "deterministic_rollback_or_fallback":
        errors.append("27.1 fallback rules must keep deterministic abort handling")

    if OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("27.2 inventory authority must keep enumerateDevices authoritative")

    if OUTPUT_VISIBILITY_PATHS.get("explicit_grant_path") != "MediaDevices.selectAudioOutput":
        errors.append("27.2 visibility paths must keep selectAudioOutput explicit grant path")

    if SINK_SELECTION_APPLY_PHASE_MODEL.get("selection_phase") != "MediaDevices.selectAudioOutput":
        errors.append("27.3 phase model must keep selectAudioOutput as selection phase")

    if SINK_SELECTION_APPLY_PHASE_MODEL.get("apply_phase") != "HTMLMediaElement.setSinkId":
        errors.append("27.3 phase model must keep setSinkId as apply phase")

    required_apply_error_matrix_27_3 = {
        "NotAllowedError": "apply_blocked_by_policy_or_permission",
        "NotFoundError": "sink_id_missing_or_stale",
        "AbortError": "sink_switch_failed_at_apply_stage",
    }
    if APPLY_ERROR_CLASS_MATRIX != required_apply_error_matrix_27_3:
        errors.append("27.3 apply error matrix must keep canonical class mapping")

    if PERSISTED_SINK_REVALIDATION_RULES.get("revalidate_via_selectaudiooutput_before_reuse") is not True:
        errors.append("27.3 revalidation rules must keep selectAudioOutput revalidation requirement")

    return errors

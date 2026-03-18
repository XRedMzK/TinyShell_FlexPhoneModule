from __future__ import annotations


SINK_SELECTION_APPLY_PHASE_MODEL = {
    "selection_phase": "MediaDevices.selectAudioOutput",
    "apply_phase": "HTMLMediaElement.setSinkId",
    "selection_and_apply_are_distinct_operations": True,
}

SELECTION_PATH_PRECONDITIONS = {
    "secure_context_required": True,
    "transient_user_activation_required": True,
    "selection_is_authoritative_non_default_grant_path": True,
    "selection_returns_sink_metadata_for_apply_path": True,
}

APPLY_PATH_PRECONDITIONS = {
    "secure_context_required": True,
    "target_surface": "HTMLMediaElement",
    "requires_already_usable_sink_id": True,
    "apply_is_not_permission_grant_path": True,
}

PERSISTED_SINK_REVALIDATION_RULES = {
    "persisted_sink_ids_permanently_trusted": False,
    "revalidate_via_selectaudiooutput_before_reuse": True,
    "id_rotation_or_revoke_considered_expected": True,
}

SELECTION_ERROR_CLASS_MATRIX = {
    "InvalidStateError": "missing_transient_user_activation",
    "NotAllowedError": "selection_blocked_or_cancelled",
    "NotFoundError": "no_available_output_devices",
}

APPLY_ERROR_CLASS_MATRIX = {
    "NotAllowedError": "apply_blocked_by_policy_or_permission",
    "NotFoundError": "sink_id_missing_or_stale",
    "AbortError": "sink_switch_failed_at_apply_stage",
}

DETERMINISTIC_HANDLING_RULES_27_3 = {
    "never_use_setsinkid_as_selection_substitute": True,
    "selection_notallowed_requires_fresh_user_action": True,
    "apply_notallowed_no_blind_retry_loop": True,
    "notfound_requires_fresh_visibility_or_reselection": True,
    "aborterror_is_apply_failure_not_selection_failure": True,
    "failure_classes_non_overlapping": True,
}

SINK_SELECTION_APPLY_CONTRACT_INVARIANTS = {
    "selection_apply_split_authoritative": True,
    "transient_activation_applies_to_selection_only": True,
    "apply_path_never_implicit_permission_grant": True,
    "persisted_ids_require_revalidation": True,
    "phase_specific_error_matrix_deterministic": True,
    "production_runtime_change_allowed_in_27_3": False,
}

STAGE27_CLOSURE_CRITERIA_27_3 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "selection_apply_split_preconditions_and_error_matrix_defined",
    "persisted_id_revalidation_rule_explicit",
    "dependency_alignment_with_27_1_27_2_checker_enforced",
    "checker_and_compileall_pass",
)


def validate_webrtc_sink_selection_apply_semantics_error_class_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_audio_output_remote_playout_route_resilience_baseline import (
        OUTPUT_SELECTION_SURFACES,
        OUTPUT_PERMISSION_POLICY_MODEL,
        STAGE27_SUBSTEP_DRAFT,
        STAGE27_VERIFICATION_TYPES,
    )
    from app.webrtc_output_device_inventory_permission_policy_visibility_contract_baseline import (
        OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE,
        OUTPUT_VISIBILITY_PATHS,
    )

    required_phase_model = {
        "selection_phase": "MediaDevices.selectAudioOutput",
        "apply_phase": "HTMLMediaElement.setSinkId",
        "selection_and_apply_are_distinct_operations": True,
    }
    if SINK_SELECTION_APPLY_PHASE_MODEL != required_phase_model:
        errors.append("SINK_SELECTION_APPLY_PHASE_MODEL must match canonical two-phase model")

    required_selection_preconditions = {
        "secure_context_required": True,
        "transient_user_activation_required": True,
        "selection_is_authoritative_non_default_grant_path": True,
        "selection_returns_sink_metadata_for_apply_path": True,
    }
    if SELECTION_PATH_PRECONDITIONS != required_selection_preconditions:
        errors.append("SELECTION_PATH_PRECONDITIONS must match canonical selection preconditions")

    required_apply_preconditions = {
        "secure_context_required": True,
        "target_surface": "HTMLMediaElement",
        "requires_already_usable_sink_id": True,
        "apply_is_not_permission_grant_path": True,
    }
    if APPLY_PATH_PRECONDITIONS != required_apply_preconditions:
        errors.append("APPLY_PATH_PRECONDITIONS must match canonical apply preconditions")

    required_revalidation_rules = {
        "persisted_sink_ids_permanently_trusted": False,
        "revalidate_via_selectaudiooutput_before_reuse": True,
        "id_rotation_or_revoke_considered_expected": True,
    }
    if PERSISTED_SINK_REVALIDATION_RULES != required_revalidation_rules:
        errors.append("PERSISTED_SINK_REVALIDATION_RULES must match canonical revalidation rules")

    required_selection_errors = {
        "InvalidStateError": "missing_transient_user_activation",
        "NotAllowedError": "selection_blocked_or_cancelled",
        "NotFoundError": "no_available_output_devices",
    }
    if SELECTION_ERROR_CLASS_MATRIX != required_selection_errors:
        errors.append("SELECTION_ERROR_CLASS_MATRIX must match canonical selection error classes")

    required_apply_errors = {
        "NotAllowedError": "apply_blocked_by_policy_or_permission",
        "NotFoundError": "sink_id_missing_or_stale",
        "AbortError": "sink_switch_failed_at_apply_stage",
    }
    if APPLY_ERROR_CLASS_MATRIX != required_apply_errors:
        errors.append("APPLY_ERROR_CLASS_MATRIX must match canonical apply error classes")

    required_handling_rules = {
        "never_use_setsinkid_as_selection_substitute": True,
        "selection_notallowed_requires_fresh_user_action": True,
        "apply_notallowed_no_blind_retry_loop": True,
        "notfound_requires_fresh_visibility_or_reselection": True,
        "aborterror_is_apply_failure_not_selection_failure": True,
        "failure_classes_non_overlapping": True,
    }
    if DETERMINISTIC_HANDLING_RULES_27_3 != required_handling_rules:
        errors.append("DETERMINISTIC_HANDLING_RULES_27_3 must match canonical handling rules")

    required_invariants = {
        "selection_apply_split_authoritative": True,
        "transient_activation_applies_to_selection_only": True,
        "apply_path_never_implicit_permission_grant": True,
        "persisted_ids_require_revalidation": True,
        "phase_specific_error_matrix_deterministic": True,
        "production_runtime_change_allowed_in_27_3": False,
    }
    if SINK_SELECTION_APPLY_CONTRACT_INVARIANTS != required_invariants:
        errors.append("SINK_SELECTION_APPLY_CONTRACT_INVARIANTS must match canonical invariants")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "selection_apply_split_preconditions_and_error_matrix_defined",
        "persisted_id_revalidation_rule_explicit",
        "dependency_alignment_with_27_1_27_2_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE27_CLOSURE_CRITERIA_27_3 != required_closure:
        errors.append("STAGE27_CLOSURE_CRITERIA_27_3 must match closure criteria")

    if STAGE27_SUBSTEP_DRAFT.get("27.3") != "sink_selection_apply_semantics_and_error_class_contract":
        errors.append("Stage 27 draft must define 27.3 sink-selection/apply contract milestone")

    if STAGE27_VERIFICATION_TYPES.get("27.3") != "build check":
        errors.append("Stage 27 verification map must keep 27.3 as build check")

    if OUTPUT_SELECTION_SURFACES.get("selection_api") != "MediaDevices.selectAudioOutput":
        errors.append("27.1 output surfaces must keep selectAudioOutput as authoritative selection API")

    if OUTPUT_SELECTION_SURFACES.get("apply_api_media_element") != "HTMLMediaElement.setSinkId":
        errors.append("27.1 output surfaces must keep setSinkId as authoritative apply API")

    if OUTPUT_PERMISSION_POLICY_MODEL.get("select_audio_output_requires_transient_user_activation") is not True:
        errors.append("27.1 permission model must keep transient user activation requirement")

    if OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("27.2 inventory model must keep enumerateDevices as authoritative inventory API")

    if OUTPUT_VISIBILITY_PATHS.get("explicit_grant_path") != "MediaDevices.selectAudioOutput":
        errors.append("27.2 visibility paths must keep selectAudioOutput explicit grant path")

    return errors

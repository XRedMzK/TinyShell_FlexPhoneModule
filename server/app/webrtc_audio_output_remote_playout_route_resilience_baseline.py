from __future__ import annotations


STAGE27_NAME = "Audio Output / Remote Playout Route Resilience Baseline"

STAGE27_SCOPE = (
    "remote_audio_playout_routing_scope",
    "authoritative_output_selection_surfaces",
    "optional_web_audio_owner_path",
    "output_inventory_permission_policy_visibility_model",
    "advisory_devicechange_authoritative_snapshot_reconcile",
    "deterministic_output_route_fallback_rules",
    "explicit_boundary_excluding_capture_and_transport_quality_contracts",
    "stage27_closure_and_verification_plan",
)

OUTPUT_SELECTION_SURFACES = {
    "selection_api": "MediaDevices.selectAudioOutput",
    "apply_api_media_element": "HTMLMediaElement.setSinkId",
    "optional_apply_api_web_audio": "AudioContext.setSinkId",
    "optional_web_audio_allowed_only_with_explicit_owner": True,
    "authoritative_apply_requires_explicit_owner_path": True,
}

OUTPUT_INVENTORY_VISIBILITY_MODEL = {
    "inventory_api": "MediaDevices.enumerateDevices",
    "authoritative_output_kind": "audiooutput",
    "inventory_snapshot_semantics": "permission_policy_visibility_shaped",
    "inventory_represents_os_hardware_truth": False,
    "default_output_handling_explicit": True,
    "non_default_output_permission_gated": True,
}

OUTPUT_PERMISSION_POLICY_MODEL = {
    "select_audio_output_requires_transient_user_activation": True,
    "speaker_selection_permissions_policy_may_block": True,
    "non_default_sink_requires_permission_or_prior_grant": True,
    "policy_or_permission_denial_has_deterministic_failure_class": True,
    "permission_helper_apis_non_authoritative": True,
}

OUTPUT_RECONCILIATION_MODEL = {
    "devicechange_role": "advisory_refresh_trigger",
    "devicechange_required_for_correctness": False,
    "authoritative_reconcile_source": "fresh_enumerate_devices_snapshot",
    "route_validation_key": "sinkId",
    "enumeration_eligibility_required": True,
}

OUTPUT_ROUTE_FALLBACK_RULES = {
    "missing_selected_sink": "fallback_default_or_require_user_reselection",
    "policy_or_permission_blocked_sink": "fail_closed_to_allowed_route_with_reselection_path",
    "sink_apply_abort_error": "deterministic_rollback_or_fallback",
    "unsupported_setsinkid_or_selectaudiooutput": "deterministic_degraded_mode",
    "fallback_never_inferred_from_capture_contracts": True,
}

STAGE27_SCOPE_BOUNDARY = {
    "output_route_resilience_in_scope": True,
    "capture_acquisition_in_scope": False,
    "screen_capture_source_selection_in_scope": False,
    "rtp_transport_quality_contracts_in_scope": False,
    "signaling_durability_contracts_in_scope": False,
}

STAGE27_INVARIANTS = {
    "output_owner_path_explicit_and_separate_from_capture": True,
    "authoritative_output_apply_surface_explicit": True,
    "authoritative_output_reconcile_source_is_fresh_snapshot": True,
    "devicechange_advisory_non_required_for_correctness": True,
    "speaker_selection_policy_constraints_explicit": True,
    "fallback_outcomes_deterministic_fail_closed": True,
    "production_runtime_change_allowed_in_27_1": False,
}

STAGE27_CLOSURE_CRITERIA_27_1 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "scope_surfaces_policy_reconcile_fallbacks_defined",
    "stage27_draft_and_verification_map_defined",
    "checker_and_compileall_pass",
)

STAGE27_VERIFICATION_TYPES = {
    "27.1": "build check",
    "27.2": "build check",
    "27.3": "build check",
    "27.4": "build check",
    "27.5": "build check",
    "27.6": "manual runtime check",
    "27.7": "build check",
}

STAGE27_SUBSTEP_DRAFT = {
    "27.1": "audio_output_remote_playout_route_resilience_baseline_definition",
    "27.2": "output_device_inventory_permission_policy_visibility_contract",
    "27.3": "sink_selection_apply_semantics_and_error_class_contract",
    "27.4": "output_device_loss_fallback_rebinding_contract",
    "27.5": "output_devicechange_reconciliation_contract",
    "27.6": "output_route_resilience_sandbox_smoke_baseline",
    "27.7": "output_route_resilience_ci_gate_baseline",
}


def validate_webrtc_audio_output_remote_playout_route_resilience_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_capture_resilience_ci_gate_baseline import (
        CI_CAPTURE_RESILIENCE_INVARIANTS,
    )
    from app.webrtc_capture_source_device_permission_resilience_baseline import (
        CAPTURE_SCOPE_BOUNDARY,
        STAGE26_SUBSTEP_DRAFT,
        STAGE26_VERIFICATION_TYPES,
    )

    if STAGE27_NAME != "Audio Output / Remote Playout Route Resilience Baseline":
        errors.append("STAGE27_NAME must match canonical stage name")

    required_scope = (
        "remote_audio_playout_routing_scope",
        "authoritative_output_selection_surfaces",
        "optional_web_audio_owner_path",
        "output_inventory_permission_policy_visibility_model",
        "advisory_devicechange_authoritative_snapshot_reconcile",
        "deterministic_output_route_fallback_rules",
        "explicit_boundary_excluding_capture_and_transport_quality_contracts",
        "stage27_closure_and_verification_plan",
    )
    if STAGE27_SCOPE != required_scope:
        errors.append("STAGE27_SCOPE must match canonical stage scope")

    required_selection_surfaces = {
        "selection_api": "MediaDevices.selectAudioOutput",
        "apply_api_media_element": "HTMLMediaElement.setSinkId",
        "optional_apply_api_web_audio": "AudioContext.setSinkId",
        "optional_web_audio_allowed_only_with_explicit_owner": True,
        "authoritative_apply_requires_explicit_owner_path": True,
    }
    if OUTPUT_SELECTION_SURFACES != required_selection_surfaces:
        errors.append("OUTPUT_SELECTION_SURFACES must match canonical output selection surfaces")

    required_inventory_model = {
        "inventory_api": "MediaDevices.enumerateDevices",
        "authoritative_output_kind": "audiooutput",
        "inventory_snapshot_semantics": "permission_policy_visibility_shaped",
        "inventory_represents_os_hardware_truth": False,
        "default_output_handling_explicit": True,
        "non_default_output_permission_gated": True,
    }
    if OUTPUT_INVENTORY_VISIBILITY_MODEL != required_inventory_model:
        errors.append("OUTPUT_INVENTORY_VISIBILITY_MODEL must match canonical inventory model")

    required_permission_policy_model = {
        "select_audio_output_requires_transient_user_activation": True,
        "speaker_selection_permissions_policy_may_block": True,
        "non_default_sink_requires_permission_or_prior_grant": True,
        "policy_or_permission_denial_has_deterministic_failure_class": True,
        "permission_helper_apis_non_authoritative": True,
    }
    if OUTPUT_PERMISSION_POLICY_MODEL != required_permission_policy_model:
        errors.append("OUTPUT_PERMISSION_POLICY_MODEL must match canonical permission/policy model")

    required_reconcile_model = {
        "devicechange_role": "advisory_refresh_trigger",
        "devicechange_required_for_correctness": False,
        "authoritative_reconcile_source": "fresh_enumerate_devices_snapshot",
        "route_validation_key": "sinkId",
        "enumeration_eligibility_required": True,
    }
    if OUTPUT_RECONCILIATION_MODEL != required_reconcile_model:
        errors.append("OUTPUT_RECONCILIATION_MODEL must match canonical reconciliation model")

    required_fallback_rules = {
        "missing_selected_sink": "fallback_default_or_require_user_reselection",
        "policy_or_permission_blocked_sink": "fail_closed_to_allowed_route_with_reselection_path",
        "sink_apply_abort_error": "deterministic_rollback_or_fallback",
        "unsupported_setsinkid_or_selectaudiooutput": "deterministic_degraded_mode",
        "fallback_never_inferred_from_capture_contracts": True,
    }
    if OUTPUT_ROUTE_FALLBACK_RULES != required_fallback_rules:
        errors.append("OUTPUT_ROUTE_FALLBACK_RULES must match canonical fallback rule set")

    required_scope_boundary = {
        "output_route_resilience_in_scope": True,
        "capture_acquisition_in_scope": False,
        "screen_capture_source_selection_in_scope": False,
        "rtp_transport_quality_contracts_in_scope": False,
        "signaling_durability_contracts_in_scope": False,
    }
    if STAGE27_SCOPE_BOUNDARY != required_scope_boundary:
        errors.append("STAGE27_SCOPE_BOUNDARY must match canonical boundary map")

    required_invariants = {
        "output_owner_path_explicit_and_separate_from_capture": True,
        "authoritative_output_apply_surface_explicit": True,
        "authoritative_output_reconcile_source_is_fresh_snapshot": True,
        "devicechange_advisory_non_required_for_correctness": True,
        "speaker_selection_policy_constraints_explicit": True,
        "fallback_outcomes_deterministic_fail_closed": True,
        "production_runtime_change_allowed_in_27_1": False,
    }
    if STAGE27_INVARIANTS != required_invariants:
        errors.append("STAGE27_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "scope_surfaces_policy_reconcile_fallbacks_defined",
        "stage27_draft_and_verification_map_defined",
        "checker_and_compileall_pass",
    )
    if STAGE27_CLOSURE_CRITERIA_27_1 != required_closure:
        errors.append("STAGE27_CLOSURE_CRITERIA_27_1 must match closure criteria")

    required_verification_types = {
        "27.1": "build check",
        "27.2": "build check",
        "27.3": "build check",
        "27.4": "build check",
        "27.5": "build check",
        "27.6": "manual runtime check",
        "27.7": "build check",
    }
    if STAGE27_VERIFICATION_TYPES != required_verification_types:
        errors.append("STAGE27_VERIFICATION_TYPES must match verification map")

    required_substeps = {
        "27.1": "audio_output_remote_playout_route_resilience_baseline_definition",
        "27.2": "output_device_inventory_permission_policy_visibility_contract",
        "27.3": "sink_selection_apply_semantics_and_error_class_contract",
        "27.4": "output_device_loss_fallback_rebinding_contract",
        "27.5": "output_devicechange_reconciliation_contract",
        "27.6": "output_route_resilience_sandbox_smoke_baseline",
        "27.7": "output_route_resilience_ci_gate_baseline",
    }
    if STAGE27_SUBSTEP_DRAFT != required_substeps:
        errors.append("STAGE27_SUBSTEP_DRAFT must match stage draft")

    if STAGE26_SUBSTEP_DRAFT.get("26.7") != "capture_resilience_ci_gate_baseline":
        errors.append("Stage 26 dependency must keep 26.7 CI gate milestone")

    if STAGE26_VERIFICATION_TYPES.get("26.7") != "build check":
        errors.append("Stage 26 dependency must keep 26.7 verification type as build check")

    if CAPTURE_SCOPE_BOUNDARY.get("output_sink_routing_in_scope") is not False:
        errors.append("Stage 26 capture scope boundary must keep output sink routing out of scope")

    if CI_CAPTURE_RESILIENCE_INVARIANTS.get("production_runtime_path_unchanged") is not True:
        errors.append("Stage 26 CI invariants must keep production_runtime_path_unchanged=true")

    return errors

from __future__ import annotations


OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE = {
    "inventory_api": "MediaDevices.enumerateDevices",
    "authoritative_output_kind": "audiooutput",
    "secure_context_required": True,
    "fully_active_document_required": True,
    "visible_document_required": True,
    "inventory_snapshot_semantics": "permission_policy_visibility_shaped",
    "inventory_represents_os_hardware_truth": False,
}

OUTPUT_DEVICE_VISIBILITY_SCOPE = {
    "default_sink_requires_additional_permission": False,
    "non_default_sink_requires_permission": True,
    "speaker_selection_policy_gates_output_visibility": True,
    "stage27_output_inventory_authoritative": True,
    "capture_slot_authority_in_stage27": False,
}

OUTPUT_PERMISSION_POLICY_VISIBILITY_MODEL = {
    "policy_blocked_outputs_excluded_from_snapshot": True,
    "select_audio_output_explicit_grant_enables_non_default_visibility": True,
    "implicit_visibility_via_getusermedia_same_groupid_allowed": True,
    "permission_helper_apis_non_authoritative": True,
    "missing_non_default_without_permission_not_hardware_absence": True,
}

OUTPUT_VISIBILITY_PATHS = {
    "explicit_grant_path": "MediaDevices.selectAudioOutput",
    "implicit_grant_path": "getUserMedia_same_groupId_affinity",
    "authoritative_visibility_confirmation": "fresh_enumerate_devices_snapshot",
    "devicechange_authoritative_for_visibility": False,
}

OUTPUT_IDENTITY_AND_METADATA_RULES = {
    "primary_identity_key_fields": (
        "kind",
        "deviceId",
    ),
    "groupid_association_metadata_only": True,
    "label_ux_metadata_only": True,
    "label_never_used_as_identity_key": True,
    "audiooutput_inventory_scope_only": True,
}

OUTPUT_INVENTORY_VISIBILITY_CONTRACT_INVARIANTS = {
    "enumerate_devices_is_authoritative_output_inventory_surface": True,
    "inventory_is_permission_policy_snapshot_not_hardware_truth": True,
    "default_sink_semantics_no_additional_permission": True,
    "non_default_sink_semantics_permission_gated": True,
    "explicit_or_implicit_grant_required_for_non_default_visibility": True,
    "speaker_selection_policy_constraints_explicit": True,
    "identity_uses_kind_plus_deviceid": True,
    "groupid_association_only": True,
    "label_not_identity": True,
    "production_runtime_change_allowed_in_27_2": False,
}

STAGE27_CLOSURE_CRITERIA_27_2 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "authoritative_inventory_visibility_identity_policy_rules_defined",
    "default_vs_non_default_visibility_semantics_explicit",
    "dependency_alignment_with_27_1_checker_enforced",
    "checker_and_compileall_pass",
)


def validate_webrtc_output_device_inventory_permission_policy_visibility_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_audio_output_remote_playout_route_resilience_baseline import (
        OUTPUT_INVENTORY_VISIBILITY_MODEL,
        OUTPUT_SELECTION_SURFACES,
        STAGE27_SCOPE_BOUNDARY,
        STAGE27_SUBSTEP_DRAFT,
        STAGE27_VERIFICATION_TYPES,
    )

    required_authority_surface = {
        "inventory_api": "MediaDevices.enumerateDevices",
        "authoritative_output_kind": "audiooutput",
        "secure_context_required": True,
        "fully_active_document_required": True,
        "visible_document_required": True,
        "inventory_snapshot_semantics": "permission_policy_visibility_shaped",
        "inventory_represents_os_hardware_truth": False,
    }
    if OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE != required_authority_surface:
        errors.append("OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE must match canonical authority surface")

    required_visibility_scope = {
        "default_sink_requires_additional_permission": False,
        "non_default_sink_requires_permission": True,
        "speaker_selection_policy_gates_output_visibility": True,
        "stage27_output_inventory_authoritative": True,
        "capture_slot_authority_in_stage27": False,
    }
    if OUTPUT_DEVICE_VISIBILITY_SCOPE != required_visibility_scope:
        errors.append("OUTPUT_DEVICE_VISIBILITY_SCOPE must match canonical visibility scope")

    required_policy_model = {
        "policy_blocked_outputs_excluded_from_snapshot": True,
        "select_audio_output_explicit_grant_enables_non_default_visibility": True,
        "implicit_visibility_via_getusermedia_same_groupid_allowed": True,
        "permission_helper_apis_non_authoritative": True,
        "missing_non_default_without_permission_not_hardware_absence": True,
    }
    if OUTPUT_PERMISSION_POLICY_VISIBILITY_MODEL != required_policy_model:
        errors.append(
            "OUTPUT_PERMISSION_POLICY_VISIBILITY_MODEL must match canonical permission/policy model"
        )

    required_visibility_paths = {
        "explicit_grant_path": "MediaDevices.selectAudioOutput",
        "implicit_grant_path": "getUserMedia_same_groupId_affinity",
        "authoritative_visibility_confirmation": "fresh_enumerate_devices_snapshot",
        "devicechange_authoritative_for_visibility": False,
    }
    if OUTPUT_VISIBILITY_PATHS != required_visibility_paths:
        errors.append("OUTPUT_VISIBILITY_PATHS must match canonical visibility paths")

    required_identity_rules = {
        "primary_identity_key_fields": ("kind", "deviceId"),
        "groupid_association_metadata_only": True,
        "label_ux_metadata_only": True,
        "label_never_used_as_identity_key": True,
        "audiooutput_inventory_scope_only": True,
    }
    if OUTPUT_IDENTITY_AND_METADATA_RULES != required_identity_rules:
        errors.append("OUTPUT_IDENTITY_AND_METADATA_RULES must match canonical identity rules")

    required_invariants = {
        "enumerate_devices_is_authoritative_output_inventory_surface": True,
        "inventory_is_permission_policy_snapshot_not_hardware_truth": True,
        "default_sink_semantics_no_additional_permission": True,
        "non_default_sink_semantics_permission_gated": True,
        "explicit_or_implicit_grant_required_for_non_default_visibility": True,
        "speaker_selection_policy_constraints_explicit": True,
        "identity_uses_kind_plus_deviceid": True,
        "groupid_association_only": True,
        "label_not_identity": True,
        "production_runtime_change_allowed_in_27_2": False,
    }
    if OUTPUT_INVENTORY_VISIBILITY_CONTRACT_INVARIANTS != required_invariants:
        errors.append(
            "OUTPUT_INVENTORY_VISIBILITY_CONTRACT_INVARIANTS must match canonical invariant set"
        )

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "authoritative_inventory_visibility_identity_policy_rules_defined",
        "default_vs_non_default_visibility_semantics_explicit",
        "dependency_alignment_with_27_1_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE27_CLOSURE_CRITERIA_27_2 != required_closure:
        errors.append("STAGE27_CLOSURE_CRITERIA_27_2 must match closure criteria")

    if STAGE27_SUBSTEP_DRAFT.get("27.2") != "output_device_inventory_permission_policy_visibility_contract":
        errors.append("Stage 27 draft must define 27.2 inventory visibility milestone")

    if STAGE27_VERIFICATION_TYPES.get("27.2") != "build check":
        errors.append("Stage 27 verification map must keep 27.2 as build check")

    if STAGE27_SCOPE_BOUNDARY.get("output_route_resilience_in_scope") is not True:
        errors.append("27.1 scope boundary must keep output route resilience in scope")

    if STAGE27_SCOPE_BOUNDARY.get("capture_acquisition_in_scope") is not False:
        errors.append("27.1 scope boundary must keep capture acquisition out of scope")

    if OUTPUT_SELECTION_SURFACES.get("selection_api") != "MediaDevices.selectAudioOutput":
        errors.append("27.1 output selection surfaces must keep selectAudioOutput authoritative")

    if OUTPUT_SELECTION_SURFACES.get("apply_api_media_element") != "HTMLMediaElement.setSinkId":
        errors.append("27.1 output selection surfaces must keep setSinkId authoritative")

    if OUTPUT_INVENTORY_VISIBILITY_MODEL.get("authoritative_output_kind") != "audiooutput":
        errors.append("27.1 inventory model must keep audiooutput as authoritative kind")

    if OUTPUT_INVENTORY_VISIBILITY_MODEL.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("27.1 inventory model must keep enumerateDevices as inventory API")

    return errors

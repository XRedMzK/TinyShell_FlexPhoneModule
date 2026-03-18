from __future__ import annotations


MEDIA_DEVICE_INVENTORY_AUTHORITY_SURFACE = {
    "inventory_api": "MediaDevices.enumerateDevices",
    "secure_context_required": True,
    "fully_active_document_required": True,
    "visible_document_required": True,
    "inventory_snapshot_semantics": "permission_policy_visibility_gated",
    "inventory_represents_os_hardware_truth": False,
}

CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE = {
    "authoritative_capture_kinds": (
        "audioinput",
        "videoinput",
    ),
    "observed_non_authoritative_kinds": (
        "audiooutput",
    ),
    "stage26_output_sink_routing_in_scope": False,
    "default_devices_ordered_first": True,
    "display_sources_enumerable_via_enumerate_devices": False,
    "devicechange_covers_display_source_changes": False,
}

INVENTORY_VISIBILITY_STATE_MODEL = {
    "redacted": {
        "pre_capture_or_no_relevant_grant": True,
        "max_entries_per_capture_kind": 1,
        "deviceid_label_groupid_may_be_empty": True,
        "full_inventory_assumed": False,
    },
    "expanded_partial": {
        "partial_exposure_after_grant_or_active_capture": True,
        "non_default_devices_may_be_visible": True,
    },
    "expanded_full_unknown": {
        "broad_exposure_available": True,
        "active_capture_not_guaranteed": True,
    },
    "expanded_full_live": {
        "active_local_capture_present": True,
        "expanded_relevant_kind_visibility": True,
    },
}

INVENTORY_IDENTITY_AND_METADATA_RULES = {
    "primary_identity_key_fields": (
        "kind",
        "deviceId",
    ),
    "groupid_is_association_metadata_only": True,
    "label_is_ux_metadata_only": True,
    "label_never_used_as_identity_key": True,
    "missing_non_default_entries_in_redacted_not_hardware_absence": True,
    "deviceid_is_origin_scoped": True,
    "deviceid_resets_with_browser_privacy_lifecycle": True,
}

PERMISSION_POLICY_AND_VISIBILITY_GATING_RULES = {
    "policy_blocked_devices_excluded_from_snapshot": True,
    "non_default_capture_devices_require_relevant_grant_for_visibility": True,
    "permissions_api_not_required_for_inventory_correctness": True,
    "speaker_selection_policy_is_observed_only": True,
}

DISPLAY_CAPTURE_INVENTORY_EXCLUSION = {
    "display_sources_in_enumerate_devices_inventory": False,
    "display_source_changes_derived_from_devicechange": False,
    "display_source_inventory_contract_step": "26.4_and_26.5",
}

PERMISSIONS_QUERY_HINT_BOUNDARY = {
    "permissions_query_authoritative": False,
    "unsupported_permission_name_non_fatal": True,
    "query_typeerror_tolerated": True,
}

INVENTORY_VISIBILITY_CONTRACT_INVARIANTS = {
    "enumerate_devices_is_authoritative_inventory_surface": True,
    "inventory_is_visibility_snapshot_not_hardware_truth": True,
    "pre_capture_inventory_can_be_redacted": True,
    "post_capture_visibility_can_expand": True,
    "visibility_can_contract_after_revoke_or_reset": True,
    "label_never_identity_or_reconcile_key": True,
    "groupid_association_only": True,
    "audiooutput_non_authoritative_for_capture_slots": True,
    "display_source_inventory_out_of_scope_for_26_2": True,
    "production_runtime_change_allowed_in_26_2": False,
}

STAGE26_CLOSURE_CRITERIA_26_2 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "authoritative_surface_visibility_model_identity_policy_boundaries_defined",
    "redacted_vs_expanded_inventory_rules_explicit",
    "display_inventory_exclusion_explicit",
    "checker_and_compileall_pass",
)


def validate_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_capture_source_device_permission_resilience_baseline import (
        CAPTURE_RECONCILIATION_SURFACES,
        CAPTURE_SCOPE_BOUNDARY,
        STAGE26_SUBSTEP_DRAFT,
        STAGE26_VERIFICATION_TYPES,
    )

    required_authority_surface = {
        "inventory_api": "MediaDevices.enumerateDevices",
        "secure_context_required": True,
        "fully_active_document_required": True,
        "visible_document_required": True,
        "inventory_snapshot_semantics": "permission_policy_visibility_gated",
        "inventory_represents_os_hardware_truth": False,
    }
    if MEDIA_DEVICE_INVENTORY_AUTHORITY_SURFACE != required_authority_surface:
        errors.append("MEDIA_DEVICE_INVENTORY_AUTHORITY_SURFACE must match canonical authority contract")

    required_scope = {
        "authoritative_capture_kinds": ("audioinput", "videoinput"),
        "observed_non_authoritative_kinds": ("audiooutput",),
        "stage26_output_sink_routing_in_scope": False,
        "default_devices_ordered_first": True,
        "display_sources_enumerable_via_enumerate_devices": False,
        "devicechange_covers_display_source_changes": False,
    }
    if CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE != required_scope:
        errors.append("CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE must match canonical inventory scope")

    required_state_model_keys = {
        "redacted",
        "expanded_partial",
        "expanded_full_unknown",
        "expanded_full_live",
    }
    if set(INVENTORY_VISIBILITY_STATE_MODEL.keys()) != required_state_model_keys:
        errors.append("INVENTORY_VISIBILITY_STATE_MODEL must define canonical visibility states")

    redacted = INVENTORY_VISIBILITY_STATE_MODEL.get("redacted", {})
    if redacted.get("max_entries_per_capture_kind") != 1:
        errors.append("redacted.max_entries_per_capture_kind must be 1")
    if redacted.get("deviceid_label_groupid_may_be_empty") is not True:
        errors.append("redacted.deviceid_label_groupid_may_be_empty must be true")
    if redacted.get("full_inventory_assumed") is not False:
        errors.append("redacted.full_inventory_assumed must be false")

    if INVENTORY_VISIBILITY_STATE_MODEL.get("expanded_full_live", {}).get("active_local_capture_present") is not True:
        errors.append("expanded_full_live.active_local_capture_present must be true")

    required_identity_rules = {
        "primary_identity_key_fields": ("kind", "deviceId"),
        "groupid_is_association_metadata_only": True,
        "label_is_ux_metadata_only": True,
        "label_never_used_as_identity_key": True,
        "missing_non_default_entries_in_redacted_not_hardware_absence": True,
        "deviceid_is_origin_scoped": True,
        "deviceid_resets_with_browser_privacy_lifecycle": True,
    }
    if INVENTORY_IDENTITY_AND_METADATA_RULES != required_identity_rules:
        errors.append("INVENTORY_IDENTITY_AND_METADATA_RULES must match canonical identity rules")

    required_policy_rules = {
        "policy_blocked_devices_excluded_from_snapshot": True,
        "non_default_capture_devices_require_relevant_grant_for_visibility": True,
        "permissions_api_not_required_for_inventory_correctness": True,
        "speaker_selection_policy_is_observed_only": True,
    }
    if PERMISSION_POLICY_AND_VISIBILITY_GATING_RULES != required_policy_rules:
        errors.append(
            "PERMISSION_POLICY_AND_VISIBILITY_GATING_RULES must match canonical policy-gating rules"
        )

    required_display_exclusion = {
        "display_sources_in_enumerate_devices_inventory": False,
        "display_source_changes_derived_from_devicechange": False,
        "display_source_inventory_contract_step": "26.4_and_26.5",
    }
    if DISPLAY_CAPTURE_INVENTORY_EXCLUSION != required_display_exclusion:
        errors.append("DISPLAY_CAPTURE_INVENTORY_EXCLUSION must match canonical exclusion contract")

    required_permissions_hint_boundary = {
        "permissions_query_authoritative": False,
        "unsupported_permission_name_non_fatal": True,
        "query_typeerror_tolerated": True,
    }
    if PERMISSIONS_QUERY_HINT_BOUNDARY != required_permissions_hint_boundary:
        errors.append("PERMISSIONS_QUERY_HINT_BOUNDARY must match canonical hint boundary")

    required_invariants = {
        "enumerate_devices_is_authoritative_inventory_surface": True,
        "inventory_is_visibility_snapshot_not_hardware_truth": True,
        "pre_capture_inventory_can_be_redacted": True,
        "post_capture_visibility_can_expand": True,
        "visibility_can_contract_after_revoke_or_reset": True,
        "label_never_identity_or_reconcile_key": True,
        "groupid_association_only": True,
        "audiooutput_non_authoritative_for_capture_slots": True,
        "display_source_inventory_out_of_scope_for_26_2": True,
        "production_runtime_change_allowed_in_26_2": False,
    }
    if INVENTORY_VISIBILITY_CONTRACT_INVARIANTS != required_invariants:
        errors.append("INVENTORY_VISIBILITY_CONTRACT_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "authoritative_surface_visibility_model_identity_policy_boundaries_defined",
        "redacted_vs_expanded_inventory_rules_explicit",
        "display_inventory_exclusion_explicit",
        "checker_and_compileall_pass",
    )
    if STAGE26_CLOSURE_CRITERIA_26_2 != required_closure:
        errors.append("STAGE26_CLOSURE_CRITERIA_26_2 must match closure criteria")

    if STAGE26_SUBSTEP_DRAFT.get("26.2") != "media_device_inventory_permission_gated_visibility_contract":
        errors.append("Stage 26 draft must define 26.2 inventory visibility contract milestone")

    if STAGE26_VERIFICATION_TYPES.get("26.2") != "build check":
        errors.append("Stage 26 verification map must keep 26.2 as build check")

    if CAPTURE_SCOPE_BOUNDARY.get("output_sink_routing_in_scope") is not False:
        errors.append("26.1 scope boundary must keep output sink routing out of scope")

    if CAPTURE_RECONCILIATION_SURFACES.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("26.1 reconciliation surfaces must keep enumerateDevices as inventory API")

    if CAPTURE_RECONCILIATION_SURFACES.get("display_sources_enumerable_via_enumerateDevices") is not False:
        errors.append("26.1 reconciliation surfaces must keep display sources non-enumerable")

    if CAPTURE_RECONCILIATION_SURFACES.get("devicechange_covers_display_source_changes") is not False:
        errors.append("26.1 reconciliation surfaces must keep devicechange non-authoritative for display sources")

    return errors

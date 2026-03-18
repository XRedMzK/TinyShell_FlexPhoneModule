from __future__ import annotations


DEVICECHANGE_ADVISORY_TRIGGER_CONTRACT = {
    "devicechange_role": "advisory_refresh_trigger",
    "devicechange_required_for_correctness": False,
    "devicechange_delivery_may_be_delayed_or_coalesced": True,
    "devicechange_support_required": False,
    "event_means_refresh_not_direct_truth": True,
}

AUTHORITATIVE_RECONCILIATION_SURFACE = {
    "authoritative_inventory_api": "MediaDevices.enumerateDevices",
    "reconciliation_source": "fresh_enumerate_devices_snapshot",
    "cached_inventory_authoritative": False,
    "snapshot_requires_enumeration_eligibility": True,
    "enumeration_preconditions": (
        "secure_context",
        "fully_active_document",
        "visible_document",
    ),
    "inventory_truth_model": "permission_policy_visibility_shaped_snapshot",
}

CAPTURE_SLOT_RECONCILIATION_SCOPE = {
    "authoritative_capture_slots": (
        "mic",
        "camera",
    ),
    "authoritative_capture_kinds": (
        "audioinput",
        "videoinput",
    ),
    "binding_comparison_key": (
        "kind",
        "deviceId",
    ),
    "audiooutput_capture_slot_authority": False,
    "snapshot_absence_means_permission_visible_absence_only": True,
    "snapshot_absence_means_absolute_hardware_absence": False,
}

FALLBACK_REFRESH_TRIGGER_SET = (
    "devicechange_if_available",
    "post_success_getUserMedia",
    "post_device_track_terminal_end",
    "post_device_acquire_failure",
    "document_enumeration_eligibility_recovered",
    "explicit_manual_refresh",
)

DISPLAY_RECONCILIATION_EXCLUSION = {
    "display_source_changes_participate_in_device_reconciliation": False,
    "display_source_discovery_via_enumerateDevices": False,
    "devicechange_used_for_display_source_changes": False,
    "display_reconciliation_governed_by_step": "26.4",
}

DETERMINISTIC_RECONCILIATION_FLOW = {
    "step_1": "detect_refresh_trigger",
    "step_2": "if_enumeration_disallowed_mark_pending_deferred",
    "step_3": "when_allowed_take_fresh_enumerate_devices_snapshot",
    "step_4": "reconcile_mic_camera_bindings_against_snapshot",
    "step_5": "classify_reconciliation_outcome",
    "step_6": "never_derive_display_source_change_from_device_inventory",
    "outcome_classes": (
        "binding_preserved",
        "binding_missing_source",
        "binding_blocked_permission",
        "binding_requires_user_selection",
    ),
}

DEVICE_CHANGE_RECONCILIATION_INVARIANTS = {
    "devicechange_advisory_only": True,
    "fresh_enumerate_devices_required_for_authoritative_reconciliation": True,
    "reconciliation_requires_enumeration_eligibility": True,
    "fallback_refresh_independent_of_devicechange_support": True,
    "mic_camera_reconciliation_separate_from_display_lifecycle": True,
    "no_display_source_decision_from_device_inventory": True,
    "production_runtime_change_allowed_in_26_5": False,
}

STAGE26_CLOSURE_CRITERIA_26_5 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "devicechange_advisory_vs_enumerate_authoritative_distinction_explicit",
    "fallback_trigger_set_explicit_and_devicechange_independent",
    "display_exclusion_from_device_reconciliation_explicit",
    "deterministic_reconcile_flow_and_outcome_classes_defined",
    "checker_and_compileall_pass",
)


def validate_webrtc_device_change_reconciliation_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_capture_source_device_permission_resilience_baseline import (
        CAPTURE_RECONCILIATION_SURFACES,
        CAPTURE_SCOPE_BOUNDARY,
        DEVICE_CAPTURE_FALLBACK_RULES,
        STAGE26_SUBSTEP_DRAFT,
        STAGE26_VERIFICATION_TYPES,
    )
    from app.webrtc_media_device_inventory_permission_gated_visibility_contract_baseline import (
        CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE,
        DISPLAY_CAPTURE_INVENTORY_EXCLUSION,
        MEDIA_DEVICE_INVENTORY_AUTHORITY_SURFACE,
    )
    from app.webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline import (
        DISPLAY_SOURCE_MODEL_CONTRACT,
        DISPLAY_SOURCE_RESELECTION_CONTRACT,
    )

    required_advisory_contract = {
        "devicechange_role": "advisory_refresh_trigger",
        "devicechange_required_for_correctness": False,
        "devicechange_delivery_may_be_delayed_or_coalesced": True,
        "devicechange_support_required": False,
        "event_means_refresh_not_direct_truth": True,
    }
    if DEVICECHANGE_ADVISORY_TRIGGER_CONTRACT != required_advisory_contract:
        errors.append("DEVICECHANGE_ADVISORY_TRIGGER_CONTRACT must match canonical advisory model")

    required_authoritative_surface = {
        "authoritative_inventory_api": "MediaDevices.enumerateDevices",
        "reconciliation_source": "fresh_enumerate_devices_snapshot",
        "cached_inventory_authoritative": False,
        "snapshot_requires_enumeration_eligibility": True,
        "enumeration_preconditions": (
            "secure_context",
            "fully_active_document",
            "visible_document",
        ),
        "inventory_truth_model": "permission_policy_visibility_shaped_snapshot",
    }
    if AUTHORITATIVE_RECONCILIATION_SURFACE != required_authoritative_surface:
        errors.append("AUTHORITATIVE_RECONCILIATION_SURFACE must match canonical reconciliation surface")

    required_scope = {
        "authoritative_capture_slots": ("mic", "camera"),
        "authoritative_capture_kinds": ("audioinput", "videoinput"),
        "binding_comparison_key": ("kind", "deviceId"),
        "audiooutput_capture_slot_authority": False,
        "snapshot_absence_means_permission_visible_absence_only": True,
        "snapshot_absence_means_absolute_hardware_absence": False,
    }
    if CAPTURE_SLOT_RECONCILIATION_SCOPE != required_scope:
        errors.append("CAPTURE_SLOT_RECONCILIATION_SCOPE must match canonical slot scope")

    required_trigger_set = (
        "devicechange_if_available",
        "post_success_getUserMedia",
        "post_device_track_terminal_end",
        "post_device_acquire_failure",
        "document_enumeration_eligibility_recovered",
        "explicit_manual_refresh",
    )
    if FALLBACK_REFRESH_TRIGGER_SET != required_trigger_set:
        errors.append("FALLBACK_REFRESH_TRIGGER_SET must match canonical trigger set")

    required_display_exclusion = {
        "display_source_changes_participate_in_device_reconciliation": False,
        "display_source_discovery_via_enumerateDevices": False,
        "devicechange_used_for_display_source_changes": False,
        "display_reconciliation_governed_by_step": "26.4",
    }
    if DISPLAY_RECONCILIATION_EXCLUSION != required_display_exclusion:
        errors.append("DISPLAY_RECONCILIATION_EXCLUSION must match display exclusion contract")

    required_flow = {
        "step_1": "detect_refresh_trigger",
        "step_2": "if_enumeration_disallowed_mark_pending_deferred",
        "step_3": "when_allowed_take_fresh_enumerate_devices_snapshot",
        "step_4": "reconcile_mic_camera_bindings_against_snapshot",
        "step_5": "classify_reconciliation_outcome",
        "step_6": "never_derive_display_source_change_from_device_inventory",
        "outcome_classes": (
            "binding_preserved",
            "binding_missing_source",
            "binding_blocked_permission",
            "binding_requires_user_selection",
        ),
    }
    if DETERMINISTIC_RECONCILIATION_FLOW != required_flow:
        errors.append("DETERMINISTIC_RECONCILIATION_FLOW must match canonical flow")

    required_invariants = {
        "devicechange_advisory_only": True,
        "fresh_enumerate_devices_required_for_authoritative_reconciliation": True,
        "reconciliation_requires_enumeration_eligibility": True,
        "fallback_refresh_independent_of_devicechange_support": True,
        "mic_camera_reconciliation_separate_from_display_lifecycle": True,
        "no_display_source_decision_from_device_inventory": True,
        "production_runtime_change_allowed_in_26_5": False,
    }
    if DEVICE_CHANGE_RECONCILIATION_INVARIANTS != required_invariants:
        errors.append("DEVICE_CHANGE_RECONCILIATION_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "devicechange_advisory_vs_enumerate_authoritative_distinction_explicit",
        "fallback_trigger_set_explicit_and_devicechange_independent",
        "display_exclusion_from_device_reconciliation_explicit",
        "deterministic_reconcile_flow_and_outcome_classes_defined",
        "checker_and_compileall_pass",
    )
    if STAGE26_CLOSURE_CRITERIA_26_5 != required_closure:
        errors.append("STAGE26_CLOSURE_CRITERIA_26_5 must match closure criteria")

    if STAGE26_SUBSTEP_DRAFT.get("26.5") != "device_change_reconciliation_contract":
        errors.append("Stage 26 draft must define 26.5 device-change reconciliation milestone")

    if STAGE26_VERIFICATION_TYPES.get("26.5") != "build check":
        errors.append("Stage 26 verification map must keep 26.5 as build check")

    if CAPTURE_RECONCILIATION_SURFACES.get("advisory_event_api") != "MediaDevices.devicechange":
        errors.append("26.1 reconciliation surfaces must keep devicechange advisory surface")

    if CAPTURE_RECONCILIATION_SURFACES.get("devicechange_required_for_correctness") is not False:
        errors.append("26.1 reconciliation surfaces must keep devicechange non-required for correctness")

    if CAPTURE_RECONCILIATION_SURFACES.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("26.1 reconciliation surfaces must keep enumerateDevices inventory API")

    if DEVICE_CAPTURE_FALLBACK_RULES.get("requires_fresh_enumerate_devices_snapshot") is not True:
        errors.append("26.1 fallback rules must require fresh enumerateDevices snapshot")

    if MEDIA_DEVICE_INVENTORY_AUTHORITY_SURFACE.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("26.2 must keep enumerateDevices as inventory authority")

    if CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE.get("authoritative_capture_kinds") != ("audioinput", "videoinput"):
        errors.append("26.2 capture inventory scope must remain audioinput/videoinput authoritative")

    if DISPLAY_CAPTURE_INVENTORY_EXCLUSION.get("display_source_inventory_contract_step") != "26.4_and_26.5":
        errors.append("26.2 display inventory exclusion must delegate to 26.4/26.5")

    if DISPLAY_SOURCE_MODEL_CONTRACT.get("display_sources_enumerable_via_enumerateDevices") is not False:
        errors.append("26.4 display source model must keep display sources non-enumerable")

    if DISPLAY_SOURCE_RESELECTION_CONTRACT.get("app_reselection_via_inventory_drift_inference_allowed") is not False:
        errors.append("26.4 must keep inventory-drift-based display reselection forbidden")

    if CAPTURE_SCOPE_BOUNDARY.get("output_sink_routing_in_scope") is not False:
        errors.append("26.1 scope boundary must keep output sink routing out of scope")

    return errors

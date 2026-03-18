from __future__ import annotations


SCREEN_SHARE_ACQUISITION_CONTRACT = {
    "authoritative_acquire_api": "MediaDevices.getDisplayMedia",
    "transient_user_activation_required": True,
    "display_capture_permission_state_model": (
        "prompt",
        "denied",
    ),
    "persistent_granted_permission_allowed": False,
    "stream_track_shape": {
        "required_video_tracks": 1,
        "max_video_tracks": 1,
        "max_audio_tracks": 1,
    },
}

DISPLAY_SOURCE_MODEL_CONTRACT = {
    "display_sources_enumerable_via_enumerateDevices": False,
    "display_sources_selectable_via_deviceid_constraints": False,
    "devicechange_authoritative_for_display_source_set": False,
    "display_source_inventory_derived_from_device_inventory": False,
}

DISPLAY_SOURCE_RESELECTION_CONTRACT = {
    "initial_selection_requires_user_mediation": True,
    "selected_source_fixed_for_track_lifetime_by_default": True,
    "source_change_without_user_interaction_allowed": False,
    "ua_surface_switching_hint_only": True,
    "app_reselection_via_fresh_getdisplaymedia_allowed": True,
    "app_reselection_via_inventory_drift_inference_allowed": False,
    "ua_mediated_user_approved_switch_path_allowed": True,
}

DISPLAY_LIFECYCLE_SIGNAL_CONTRACT = {
    "temporary_inaccessibility_signal_events": (
        "MediaStreamTrack.mute",
        "MediaStreamTrack.unmute",
    ),
    "temporary_inaccessibility_terminal": False,
    "permanent_inaccessibility_terminal_ready_state": "ended",
    "stream_may_start_with_muted_tracks": True,
    "display_video_audio_muted_state_may_change_independently": True,
}

DISPLAY_TERMINAL_PATH_CONTRACT = {
    "local_direct_stop": {
        "trigger": "MediaStreamTrack.stop",
        "ready_state_transition_to_ended_immediate": True,
        "ended_event_required": False,
        "must_not_wait_for_onended": True,
    },
    "event_driven_terminal": {
        "trigger": "permanent_display_surface_loss",
        "terminal_ready_state_value": "ended",
        "recovery_requires_fresh_user_mediated_acquire": True,
    },
}

DISPLAY_SLOT_RUNTIME_MODEL = {
    "displayVideo": {
        "required": True,
        "supports_temporary_mute_unmute": True,
        "supports_terminal_end": True,
    },
    "displayAudio": {
        "required": False,
        "supports_temporary_mute_unmute": True,
        "supports_terminal_end": True,
    },
}

DISPLAY_REPLACETRACK_HANDOFF_BOUNDARY = {
    "authoritative_handoff_api": "RTCRtpSender.replaceTrack",
    "replace_track_is_capture_acquire_api": False,
    "replace_track_is_permission_selection_api": False,
    "same_kind_required": True,
    "renegotiation_free_path_best_effort": True,
    "envelope_break_requires_renegotiation_or_reject": True,
    "kind_mismatch_rejection_type": "TypeError",
    "out_of_envelope_rejection_type": "InvalidModificationError",
}

DISPLAY_CAPTURE_SCOPE_BOUNDARY = {
    "capture_side_only": True,
    "output_sink_routing_in_scope": False,
    "receiver_side_remote_stop_in_scope": False,
}

SCREEN_SHARE_LIFECYCLE_INVARIANTS = {
    "getdisplaymedia_only_authoritative_acquire_path": True,
    "display_sources_non_enumerable_for_inventory_reconcile": True,
    "devicechange_not_authoritative_for_display_source_changes": True,
    "reselection_requires_user_mediation": True,
    "temporary_inaccessible_maps_to_mute_unmute": True,
    "permanent_inaccessible_maps_to_terminal_end": True,
    "direct_stop_without_ended_event_wait": True,
    "replacetrack_handoff_bounded_by_negotiated_envelope": True,
    "production_runtime_change_allowed_in_26_4": False,
}

STAGE26_CLOSURE_CRITERIA_26_4 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "authoritative_acquire_and_non_enumerable_display_model_defined",
    "source_reselection_rules_and_lifecycle_semantics_defined",
    "replacetrack_handoff_boundaries_defined",
    "checker_and_compileall_pass",
)


def validate_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_capture_source_device_permission_resilience_baseline import (
        CAPTURE_RECONCILIATION_SURFACES,
        CAPTURE_SCOPE_BOUNDARY,
        STAGE26_SUBSTEP_DRAFT,
        STAGE26_VERIFICATION_TYPES,
    )
    from app.webrtc_media_device_inventory_permission_gated_visibility_contract_baseline import (
        CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE,
        DISPLAY_CAPTURE_INVENTORY_EXCLUSION,
    )
    from app.webrtc_mute_unmute_source_switch_transceiver_direction_contract import (
        SOURCE_SWITCH_CONTRACT,
    )
    from app.webrtc_track_source_termination_semantics_baseline import (
        DIRECT_STOP_PATH_CONTRACT,
        TEMPORARY_INTERRUPTION_PATH_CONTRACT,
        TRACK_TERMINAL_CAUSE_MATRIX,
    )

    required_acquire_contract = {
        "authoritative_acquire_api": "MediaDevices.getDisplayMedia",
        "transient_user_activation_required": True,
        "display_capture_permission_state_model": ("prompt", "denied"),
        "persistent_granted_permission_allowed": False,
        "stream_track_shape": {
            "required_video_tracks": 1,
            "max_video_tracks": 1,
            "max_audio_tracks": 1,
        },
    }
    if SCREEN_SHARE_ACQUISITION_CONTRACT != required_acquire_contract:
        errors.append("SCREEN_SHARE_ACQUISITION_CONTRACT must match canonical acquire contract")

    required_source_model = {
        "display_sources_enumerable_via_enumerateDevices": False,
        "display_sources_selectable_via_deviceid_constraints": False,
        "devicechange_authoritative_for_display_source_set": False,
        "display_source_inventory_derived_from_device_inventory": False,
    }
    if DISPLAY_SOURCE_MODEL_CONTRACT != required_source_model:
        errors.append("DISPLAY_SOURCE_MODEL_CONTRACT must match non-enumerable source model")

    required_reselection = {
        "initial_selection_requires_user_mediation": True,
        "selected_source_fixed_for_track_lifetime_by_default": True,
        "source_change_without_user_interaction_allowed": False,
        "ua_surface_switching_hint_only": True,
        "app_reselection_via_fresh_getdisplaymedia_allowed": True,
        "app_reselection_via_inventory_drift_inference_allowed": False,
        "ua_mediated_user_approved_switch_path_allowed": True,
    }
    if DISPLAY_SOURCE_RESELECTION_CONTRACT != required_reselection:
        errors.append("DISPLAY_SOURCE_RESELECTION_CONTRACT must match reselection rules")

    required_lifecycle = {
        "temporary_inaccessibility_signal_events": (
            "MediaStreamTrack.mute",
            "MediaStreamTrack.unmute",
        ),
        "temporary_inaccessibility_terminal": False,
        "permanent_inaccessibility_terminal_ready_state": "ended",
        "stream_may_start_with_muted_tracks": True,
        "display_video_audio_muted_state_may_change_independently": True,
    }
    if DISPLAY_LIFECYCLE_SIGNAL_CONTRACT != required_lifecycle:
        errors.append("DISPLAY_LIFECYCLE_SIGNAL_CONTRACT must match lifecycle signal model")

    required_terminal_path = {
        "local_direct_stop": {
            "trigger": "MediaStreamTrack.stop",
            "ready_state_transition_to_ended_immediate": True,
            "ended_event_required": False,
            "must_not_wait_for_onended": True,
        },
        "event_driven_terminal": {
            "trigger": "permanent_display_surface_loss",
            "terminal_ready_state_value": "ended",
            "recovery_requires_fresh_user_mediated_acquire": True,
        },
    }
    if DISPLAY_TERMINAL_PATH_CONTRACT != required_terminal_path:
        errors.append("DISPLAY_TERMINAL_PATH_CONTRACT must match terminal path contract")

    required_slot_model = {
        "displayVideo": {
            "required": True,
            "supports_temporary_mute_unmute": True,
            "supports_terminal_end": True,
        },
        "displayAudio": {
            "required": False,
            "supports_temporary_mute_unmute": True,
            "supports_terminal_end": True,
        },
    }
    if DISPLAY_SLOT_RUNTIME_MODEL != required_slot_model:
        errors.append("DISPLAY_SLOT_RUNTIME_MODEL must match display slot runtime model")

    required_handoff = {
        "authoritative_handoff_api": "RTCRtpSender.replaceTrack",
        "replace_track_is_capture_acquire_api": False,
        "replace_track_is_permission_selection_api": False,
        "same_kind_required": True,
        "renegotiation_free_path_best_effort": True,
        "envelope_break_requires_renegotiation_or_reject": True,
        "kind_mismatch_rejection_type": "TypeError",
        "out_of_envelope_rejection_type": "InvalidModificationError",
    }
    if DISPLAY_REPLACETRACK_HANDOFF_BOUNDARY != required_handoff:
        errors.append("DISPLAY_REPLACETRACK_HANDOFF_BOUNDARY must match handoff boundary contract")

    required_scope_boundary = {
        "capture_side_only": True,
        "output_sink_routing_in_scope": False,
        "receiver_side_remote_stop_in_scope": False,
    }
    if DISPLAY_CAPTURE_SCOPE_BOUNDARY != required_scope_boundary:
        errors.append("DISPLAY_CAPTURE_SCOPE_BOUNDARY must match capture-side scope boundary")

    required_invariants = {
        "getdisplaymedia_only_authoritative_acquire_path": True,
        "display_sources_non_enumerable_for_inventory_reconcile": True,
        "devicechange_not_authoritative_for_display_source_changes": True,
        "reselection_requires_user_mediation": True,
        "temporary_inaccessible_maps_to_mute_unmute": True,
        "permanent_inaccessible_maps_to_terminal_end": True,
        "direct_stop_without_ended_event_wait": True,
        "replacetrack_handoff_bounded_by_negotiated_envelope": True,
        "production_runtime_change_allowed_in_26_4": False,
    }
    if SCREEN_SHARE_LIFECYCLE_INVARIANTS != required_invariants:
        errors.append("SCREEN_SHARE_LIFECYCLE_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "authoritative_acquire_and_non_enumerable_display_model_defined",
        "source_reselection_rules_and_lifecycle_semantics_defined",
        "replacetrack_handoff_boundaries_defined",
        "checker_and_compileall_pass",
    )
    if STAGE26_CLOSURE_CRITERIA_26_4 != required_closure:
        errors.append("STAGE26_CLOSURE_CRITERIA_26_4 must match closure criteria")

    if STAGE26_SUBSTEP_DRAFT.get("26.4") != "screen_share_capture_lifecycle_source_reselection_contract":
        errors.append("Stage 26 draft must define 26.4 screen-share lifecycle milestone")

    if STAGE26_VERIFICATION_TYPES.get("26.4") != "build check":
        errors.append("Stage 26 verification map must keep 26.4 as build check")

    if CAPTURE_RECONCILIATION_SURFACES.get("display_sources_enumerable_via_enumerateDevices") is not False:
        errors.append("26.1 reconciliation surfaces must keep display sources non-enumerable")

    if CAPTURE_RECONCILIATION_SURFACES.get("devicechange_covers_display_source_changes") is not False:
        errors.append("26.1 reconciliation surfaces must keep devicechange non-authoritative for display")

    if CAPTURE_SCOPE_BOUNDARY.get("output_sink_routing_in_scope") is not False:
        errors.append("26.1 scope boundary must keep output sink routing out of scope")

    if CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE.get("display_sources_enumerable_via_enumerate_devices") is not False:
        errors.append("26.2 inventory scope must keep display sources non-enumerable")

    if DISPLAY_CAPTURE_INVENTORY_EXCLUSION.get("display_source_inventory_contract_step") != "26.4_and_26.5":
        errors.append("26.2 display inventory exclusion must delegate source inventory to 26.4/26.5")

    if SOURCE_SWITCH_CONTRACT.get("authoritative_control_surface") != "RTCRtpSender.replaceTrack":
        errors.append("25.3 source switch contract must keep replaceTrack as authoritative handoff API")

    if SOURCE_SWITCH_CONTRACT.get("eligible_track_kind_relation") != "same_kind_required":
        errors.append("25.3 source switch contract must keep same-kind relation")

    if SOURCE_SWITCH_CONTRACT.get("renegotiation_required_on_envelope_break") is not True:
        errors.append("25.3 source switch contract must enforce renegotiation on envelope break")

    if DIRECT_STOP_PATH_CONTRACT.get("ended_event_required") is not False:
        errors.append("26.3 direct stop path must not require ended event")

    if TEMPORARY_INTERRUPTION_PATH_CONTRACT.get("track_remains_non_terminal") is not True:
        errors.append("26.3 temporary interruption path must remain non-terminal")

    display_causes = TRACK_TERMINAL_CAUSE_MATRIX.get("display_capture_terminal_causes", ())
    if "display_surface_permanently_inaccessible" not in display_causes:
        errors.append("26.3 display terminal causes must include permanent display-surface loss")

    return errors

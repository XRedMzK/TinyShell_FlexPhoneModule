from __future__ import annotations


TRACK_TERMINATION_SIGNAL_MODEL = {
    "terminal_ready_state_value": "ended",
    "temporary_interruption_signal_events": (
        "MediaStreamTrack.mute",
        "MediaStreamTrack.unmute",
    ),
    "temporary_interruption_maps_to_terminal": False,
    "muted_state_is_terminal": False,
}

TRACK_TERMINAL_CAUSE_MATRIX = {
    "device_capture_terminal_causes": (
        "local_stop",
        "source_disconnected_or_exhausted",
        "permission_revoked_or_ua_forced_end",
        "hardware_removed_or_ejected",
    ),
    "display_capture_terminal_causes": (
        "local_stop",
        "source_disconnected_or_exhausted",
        "display_surface_permanently_inaccessible",
    ),
    "remote_stop_in_scope": False,
}

DIRECT_STOP_PATH_CONTRACT = {
    "trigger": "MediaStreamTrack.stop",
    "path_class": "direct_local_stop",
    "ready_state_transition_to_ended_immediate": True,
    "ended_event_required": False,
    "must_not_wait_for_onended_to_teardown": True,
}

EVENT_DRIVEN_TERMINAL_PATH_CONTRACT = {
    "path_class": "event_driven_terminal",
    "applies_to_non_stop_terminal_causes": True,
    "terminal_ready_state_value": "ended",
    "ended_event_authoritative_for_terminal_observation": True,
}

TEMPORARY_INTERRUPTION_PATH_CONTRACT = {
    "path_class": "temporary_interruption",
    "signals": (
        "MediaStreamTrack.mute",
        "MediaStreamTrack.unmute",
    ),
    "track_remains_non_terminal": True,
    "teardown_required": False,
    "display_temporary_inaccessibility_terminal": False,
}

TERMINATION_TEARDOWN_RECONCILIATION_ACTIONS = {
    "device_slots": {
        "slots": ("mic", "camera"),
        "actions": (
            "set_effective_state_ended",
            "clear_authoritative_live_track_reference",
            "mark_track_non_reusable",
            "trigger_inventory_reconcile_refresh",
            "allow_fresh_reacquire_if_source_identity_available_and_policy_allows",
            "otherwise_classify_missing_source_or_blocked_permission",
        ),
    },
    "display_slots": {
        "slots": ("displayVideo", "displayAudio"),
        "actions": (
            "set_effective_state_ended",
            "clear_authoritative_live_track_reference",
            "disable_inventory_based_display_rediscovery_assumptions",
            "allow_only_explicit_fresh_getDisplayMedia_reacquire",
        ),
    },
}

TRACK_REUSABILITY_RECOVERY_RULES = {
    "ended_track_reusable": False,
    "ended_track_revival_allowed": False,
    "recovery_requires_fresh_acquire": True,
    "new_track_object_required_for_recovery": True,
}

CAPTURE_SIDE_TERMINATION_SCOPE_BOUNDARY = {
    "capture_side_only": True,
    "receiver_side_remote_stop_in_scope": False,
    "output_sink_routing_in_scope": False,
}

TRACK_TERMINATION_INVARIANTS = {
    "ready_state_ended_is_terminal": True,
    "mute_unmute_non_terminal_by_default": True,
    "direct_stop_path_without_ended_event_wait": True,
    "non_stop_terminal_paths_use_ended_event_observation": True,
    "ended_tracks_not_reused": True,
    "display_permanent_loss_requires_explicit_reacquire": True,
    "remote_stop_excluded_from_capture_side_scope": True,
    "production_runtime_change_allowed_in_26_3": False,
}

STAGE26_CLOSURE_CRITERIA_26_3 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "terminal_vs_temporary_signal_distinction_explicit",
    "direct_stop_vs_event_driven_terminal_paths_explicit",
    "capture_side_terminal_cause_matrix_excludes_remote_stop",
    "teardown_reconciliation_actions_deterministic_by_slot_class",
    "checker_and_compileall_pass",
)


def validate_webrtc_track_source_termination_semantics_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_capture_source_device_permission_resilience_baseline import (
        CAPTURE_FAILURE_CLASSIFICATION,
        CAPTURE_RECONCILIATION_SURFACES,
        CAPTURE_SCOPE_BOUNDARY,
        STAGE26_SUBSTEP_DRAFT,
        STAGE26_VERIFICATION_TYPES,
    )
    from app.webrtc_media_device_inventory_permission_gated_visibility_contract_baseline import (
        CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE,
        DISPLAY_CAPTURE_INVENTORY_EXCLUSION,
    )

    required_signal_model = {
        "terminal_ready_state_value": "ended",
        "temporary_interruption_signal_events": (
            "MediaStreamTrack.mute",
            "MediaStreamTrack.unmute",
        ),
        "temporary_interruption_maps_to_terminal": False,
        "muted_state_is_terminal": False,
    }
    if TRACK_TERMINATION_SIGNAL_MODEL != required_signal_model:
        errors.append("TRACK_TERMINATION_SIGNAL_MODEL must match canonical signal model")

    required_cause_matrix = {
        "device_capture_terminal_causes": (
            "local_stop",
            "source_disconnected_or_exhausted",
            "permission_revoked_or_ua_forced_end",
            "hardware_removed_or_ejected",
        ),
        "display_capture_terminal_causes": (
            "local_stop",
            "source_disconnected_or_exhausted",
            "display_surface_permanently_inaccessible",
        ),
        "remote_stop_in_scope": False,
    }
    if TRACK_TERMINAL_CAUSE_MATRIX != required_cause_matrix:
        errors.append("TRACK_TERMINAL_CAUSE_MATRIX must match canonical capture-side terminal causes")

    required_direct_stop = {
        "trigger": "MediaStreamTrack.stop",
        "path_class": "direct_local_stop",
        "ready_state_transition_to_ended_immediate": True,
        "ended_event_required": False,
        "must_not_wait_for_onended_to_teardown": True,
    }
    if DIRECT_STOP_PATH_CONTRACT != required_direct_stop:
        errors.append("DIRECT_STOP_PATH_CONTRACT must match direct stop semantics")

    required_event_driven_path = {
        "path_class": "event_driven_terminal",
        "applies_to_non_stop_terminal_causes": True,
        "terminal_ready_state_value": "ended",
        "ended_event_authoritative_for_terminal_observation": True,
    }
    if EVENT_DRIVEN_TERMINAL_PATH_CONTRACT != required_event_driven_path:
        errors.append("EVENT_DRIVEN_TERMINAL_PATH_CONTRACT must match canonical event-driven terminal path")

    required_temporary_path = {
        "path_class": "temporary_interruption",
        "signals": (
            "MediaStreamTrack.mute",
            "MediaStreamTrack.unmute",
        ),
        "track_remains_non_terminal": True,
        "teardown_required": False,
        "display_temporary_inaccessibility_terminal": False,
    }
    if TEMPORARY_INTERRUPTION_PATH_CONTRACT != required_temporary_path:
        errors.append("TEMPORARY_INTERRUPTION_PATH_CONTRACT must match temporary interruption contract")

    required_actions = {
        "device_slots": {
            "slots": ("mic", "camera"),
            "actions": (
                "set_effective_state_ended",
                "clear_authoritative_live_track_reference",
                "mark_track_non_reusable",
                "trigger_inventory_reconcile_refresh",
                "allow_fresh_reacquire_if_source_identity_available_and_policy_allows",
                "otherwise_classify_missing_source_or_blocked_permission",
            ),
        },
        "display_slots": {
            "slots": ("displayVideo", "displayAudio"),
            "actions": (
                "set_effective_state_ended",
                "clear_authoritative_live_track_reference",
                "disable_inventory_based_display_rediscovery_assumptions",
                "allow_only_explicit_fresh_getDisplayMedia_reacquire",
            ),
        },
    }
    if TERMINATION_TEARDOWN_RECONCILIATION_ACTIONS != required_actions:
        errors.append("TERMINATION_TEARDOWN_RECONCILIATION_ACTIONS must match deterministic action matrix")

    required_reusability = {
        "ended_track_reusable": False,
        "ended_track_revival_allowed": False,
        "recovery_requires_fresh_acquire": True,
        "new_track_object_required_for_recovery": True,
    }
    if TRACK_REUSABILITY_RECOVERY_RULES != required_reusability:
        errors.append("TRACK_REUSABILITY_RECOVERY_RULES must match canonical recovery rules")

    required_scope_boundary = {
        "capture_side_only": True,
        "receiver_side_remote_stop_in_scope": False,
        "output_sink_routing_in_scope": False,
    }
    if CAPTURE_SIDE_TERMINATION_SCOPE_BOUNDARY != required_scope_boundary:
        errors.append("CAPTURE_SIDE_TERMINATION_SCOPE_BOUNDARY must match capture-side scope boundary")

    required_invariants = {
        "ready_state_ended_is_terminal": True,
        "mute_unmute_non_terminal_by_default": True,
        "direct_stop_path_without_ended_event_wait": True,
        "non_stop_terminal_paths_use_ended_event_observation": True,
        "ended_tracks_not_reused": True,
        "display_permanent_loss_requires_explicit_reacquire": True,
        "remote_stop_excluded_from_capture_side_scope": True,
        "production_runtime_change_allowed_in_26_3": False,
    }
    if TRACK_TERMINATION_INVARIANTS != required_invariants:
        errors.append("TRACK_TERMINATION_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "terminal_vs_temporary_signal_distinction_explicit",
        "direct_stop_vs_event_driven_terminal_paths_explicit",
        "capture_side_terminal_cause_matrix_excludes_remote_stop",
        "teardown_reconciliation_actions_deterministic_by_slot_class",
        "checker_and_compileall_pass",
    )
    if STAGE26_CLOSURE_CRITERIA_26_3 != required_closure:
        errors.append("STAGE26_CLOSURE_CRITERIA_26_3 must match closure criteria")

    if STAGE26_SUBSTEP_DRAFT.get("26.3") != "track_source_termination_semantics_contract":
        errors.append("Stage 26 draft must define 26.3 termination semantics milestone")

    if STAGE26_VERIFICATION_TYPES.get("26.3") != "build check":
        errors.append("Stage 26 verification map must keep 26.3 as build check")

    runtime_terminal_causes_26_1 = CAPTURE_FAILURE_CLASSIFICATION.get("runtime_terminal_loss", {}).get("causes", ())
    if "remote_stop" in runtime_terminal_causes_26_1:
        errors.append("26.1 runtime_terminal_loss must not include remote_stop")
    if "local_direct_stop" not in runtime_terminal_causes_26_1:
        errors.append("26.1 runtime_terminal_loss must include local_direct_stop")

    if CAPTURE_RECONCILIATION_SURFACES.get("display_sources_enumerable_via_enumerateDevices") is not False:
        errors.append("26.1 reconciliation surfaces must keep display sources non-enumerable")
    if CAPTURE_RECONCILIATION_SURFACES.get("devicechange_covers_display_source_changes") is not False:
        errors.append("26.1 reconciliation surfaces must keep devicechange non-authoritative for display")

    if CAPTURE_SCOPE_BOUNDARY.get("output_sink_routing_in_scope") is not False:
        errors.append("26.1 scope boundary must keep output sink routing out of scope")

    if CAPTURE_SIDE_DEVICE_INVENTORY_SCOPE.get("display_sources_enumerable_via_enumerate_devices") is not False:
        errors.append("26.2 inventory scope must keep display sources non-enumerable")

    if DISPLAY_CAPTURE_INVENTORY_EXCLUSION.get("display_source_inventory_contract_step") != "26.4_and_26.5":
        errors.append("26.2 display inventory exclusion must delegate to 26.4/26.5")

    return errors

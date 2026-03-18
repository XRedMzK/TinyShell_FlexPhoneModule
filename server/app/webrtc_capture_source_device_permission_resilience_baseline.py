from __future__ import annotations


STAGE26_NAME = "Capture Source / Device / Permission Resilience Baseline"

STAGE26_SCOPE = (
    "local_capture_acquisition_and_runtime_reconciliation_scope",
    "authoritative_per_slot_capture_state_model",
    "capture_failure_classification_acquisition_runtime_inventory",
    "capture_reconciliation_surfaces_contract",
    "deterministic_fallback_rules_device_vs_display",
    "explicit_capture_side_scope_boundary_excluding_output_sink_routing",
    "stage26_closure_and_verification_plan",
)

CAPTURE_SLOT_STATE_MODEL = {
    "mic": {
        "source_class": "device",
        "required": True,
        "intent_states": ("idle", "acquire_requested", "stop_requested"),
        "effective_states": (
            "idle",
            "live",
            "muted_external",
            "ended",
            "failed_acquire",
            "blocked_permission",
            "missing_source",
        ),
        "identity_model": "kind_plus_deviceid_groupid_optional",
    },
    "camera": {
        "source_class": "device",
        "required": True,
        "intent_states": ("idle", "acquire_requested", "stop_requested"),
        "effective_states": (
            "idle",
            "live",
            "muted_external",
            "ended",
            "failed_acquire",
            "blocked_permission",
            "missing_source",
        ),
        "identity_model": "kind_plus_deviceid_groupid_optional",
    },
    "displayVideo": {
        "source_class": "display",
        "required": True,
        "intent_states": ("idle", "acquire_requested", "stop_requested"),
        "effective_states": (
            "idle",
            "live",
            "muted_external",
            "ended",
            "failed_acquire",
            "blocked_permission",
            "missing_source",
        ),
        "identity_model": "opaque_display_capture_session_identity",
    },
    "displayAudio": {
        "source_class": "display",
        "required": False,
        "intent_states": ("idle", "acquire_requested", "stop_requested"),
        "effective_states": (
            "idle",
            "live",
            "muted_external",
            "ended",
            "failed_acquire",
            "blocked_permission",
            "missing_source",
        ),
        "identity_model": "opaque_display_capture_session_identity",
    },
}

CAPTURE_FAILURE_CLASSIFICATION = {
    "acquire_denial_or_policy_block": {
        "kind": "acquire_time",
        "causes": ("permission_denied", "policy_block", "insecure_context_restriction"),
    },
    "acquire_source_absence_or_constraint_mismatch": {
        "kind": "acquire_time",
        "causes": ("source_not_found", "constraint_mismatch", "invalid_capture_options"),
    },
    "acquire_runtime_lockout_or_abort": {
        "kind": "acquire_time",
        "causes": ("os_or_browser_lockout", "capture_start_abort"),
    },
    "runtime_temporary_interruption": {
        "kind": "runtime",
        "causes": ("temporary_mute", "temporary_source_inaccessible"),
    },
    "runtime_terminal_loss": {
        "kind": "runtime",
        "causes": (
            "revoked_permission",
            "hardware_removal_or_ejection",
            "permanent_display_surface_loss",
            "source_exhaustion_or_disconnect",
            "local_direct_stop",
        ),
    },
    "inventory_drift": {
        "kind": "reconciliation",
        "causes": ("device_inventory_change", "permission_visibility_change"),
    },
}

CAPTURE_RECONCILIATION_SURFACES = {
    "acquisition_apis": (
        "MediaDevices.getUserMedia",
        "MediaDevices.getDisplayMedia",
    ),
    "inventory_api": "MediaDevices.enumerateDevices",
    "advisory_event_api": "MediaDevices.devicechange",
    "track_lifecycle_surfaces": (
        "MediaStreamTrack.mute",
        "MediaStreamTrack.unmute",
        "MediaStreamTrack.ended",
        "MediaStreamTrack.stop",
    ),
    "devicechange_required_for_correctness": False,
    "display_sources_enumerable_via_enumerateDevices": False,
    "devicechange_covers_display_source_changes": False,
}

DEVICE_CAPTURE_FALLBACK_RULES = {
    "reconcile_triggers": (
        "devicechange_if_available",
        "track_ended",
        "acquire_failure",
        "explicit_refresh",
    ),
    "requires_fresh_enumerate_devices_snapshot": True,
    "same_source_reacquire_if_identity_present": True,
    "default_same_kind_fallback_if_policy_allows": True,
    "missing_source_requires_explicit_user_selection": True,
}

DISPLAY_CAPTURE_FALLBACK_RULES = {
    "automatic_display_source_switch_allowed": False,
    "display_source_change_inferred_from_devicechange_or_enumerate": False,
    "reacquire_requires_explicit_user_gesture": True,
    "reacquire_path": "new_getDisplayMedia_session",
    "terminal_display_loss_maps_to_missing_source_until_reacquire": True,
}

CAPTURE_SCOPE_BOUNDARY = {
    "capture_side_only": True,
    "output_sink_routing_in_scope": False,
    "output_sink_api_family_out_of_scope": (
        "MediaDevices.selectAudioOutput",
        "HTMLMediaElement.setSinkId",
    ),
}

STAGE26_INVARIANTS = {
    "capture_side_scope_excludes_output_sink_routing": True,
    "enumerate_devices_is_inventory_surface_not_live_capture_truth": True,
    "devicechange_is_advisory_not_correctness_required": True,
    "display_sources_non_enumerable_and_not_devicechange_modeled": True,
    "local_stop_path_distinct_from_ended_event_path": True,
    "deterministic_fallback_rules_split_by_device_vs_display": True,
    "production_runtime_change_allowed_in_26_1": False,
}

STAGE26_CLOSURE_CRITERIA_26_1 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "scope_slot_model_failure_classes_surfaces_fallback_defined",
    "stage26_closure_and_verification_plan_defined",
    "checker_and_compileall_pass",
)

STAGE26_VERIFICATION_TYPES = {
    "26.1": "build check",
    "26.2": "build check",
    "26.3": "build check",
    "26.4": "build check",
    "26.5": "build check",
    "26.6": "manual runtime check",
    "26.7": "build check",
}

STAGE26_SUBSTEP_DRAFT = {
    "26.1": "capture_source_device_permission_resilience_baseline_definition",
    "26.2": "media_device_inventory_permission_gated_visibility_contract",
    "26.3": "track_source_termination_semantics_contract",
    "26.4": "screen_share_capture_lifecycle_source_reselection_contract",
    "26.5": "device_change_reconciliation_contract",
    "26.6": "capture_resilience_sandbox_smoke_baseline",
    "26.7": "capture_resilience_ci_gate_baseline",
}


def validate_webrtc_capture_source_device_permission_resilience_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_incall_media_control_quality_observability_baseline import (
        STAGE25_SUBSTEP_DRAFT,
        STAGE25_VERIFICATION_TYPES,
    )

    if STAGE26_NAME != "Capture Source / Device / Permission Resilience Baseline":
        errors.append("STAGE26_NAME must match canonical stage name")

    required_scope = (
        "local_capture_acquisition_and_runtime_reconciliation_scope",
        "authoritative_per_slot_capture_state_model",
        "capture_failure_classification_acquisition_runtime_inventory",
        "capture_reconciliation_surfaces_contract",
        "deterministic_fallback_rules_device_vs_display",
        "explicit_capture_side_scope_boundary_excluding_output_sink_routing",
        "stage26_closure_and_verification_plan",
    )
    if STAGE26_SCOPE != required_scope:
        errors.append("STAGE26_SCOPE must match canonical stage scope")

    required_slots = {"mic", "camera", "displayVideo", "displayAudio"}
    if set(CAPTURE_SLOT_STATE_MODEL.keys()) != required_slots:
        errors.append("CAPTURE_SLOT_STATE_MODEL must define canonical slot set")

    for slot_name, slot_spec in CAPTURE_SLOT_STATE_MODEL.items():
        if slot_spec.get("source_class") not in {"device", "display"}:
            errors.append(f"{slot_name}: source_class must be device|display")
        if not slot_spec.get("intent_states"):
            errors.append(f"{slot_name}: intent_states must be non-empty")
        if not slot_spec.get("effective_states"):
            errors.append(f"{slot_name}: effective_states must be non-empty")
        if "identity_model" not in slot_spec:
            errors.append(f"{slot_name}: identity_model is required")

    expected_effective_states = (
        "idle",
        "live",
        "muted_external",
        "ended",
        "failed_acquire",
        "blocked_permission",
        "missing_source",
    )
    for slot_name, slot_spec in CAPTURE_SLOT_STATE_MODEL.items():
        if tuple(slot_spec.get("effective_states", ())) != expected_effective_states:
            errors.append(f"{slot_name}: effective_states must match canonical set/order")

    required_failure_classes = {
        "acquire_denial_or_policy_block",
        "acquire_source_absence_or_constraint_mismatch",
        "acquire_runtime_lockout_or_abort",
        "runtime_temporary_interruption",
        "runtime_terminal_loss",
        "inventory_drift",
    }
    if set(CAPTURE_FAILURE_CLASSIFICATION.keys()) != required_failure_classes:
        errors.append("CAPTURE_FAILURE_CLASSIFICATION must define canonical class set")

    runtime_terminal_causes = CAPTURE_FAILURE_CLASSIFICATION["runtime_terminal_loss"]["causes"]
    if "remote_stop" in runtime_terminal_causes:
        errors.append("runtime_terminal_loss must not include remote_stop in capture-side baseline")
    if "local_direct_stop" not in runtime_terminal_causes:
        errors.append("runtime_terminal_loss must include local_direct_stop cause")

    required_surfaces = {
        "acquisition_apis": (
            "MediaDevices.getUserMedia",
            "MediaDevices.getDisplayMedia",
        ),
        "inventory_api": "MediaDevices.enumerateDevices",
        "advisory_event_api": "MediaDevices.devicechange",
        "track_lifecycle_surfaces": (
            "MediaStreamTrack.mute",
            "MediaStreamTrack.unmute",
            "MediaStreamTrack.ended",
            "MediaStreamTrack.stop",
        ),
        "devicechange_required_for_correctness": False,
        "display_sources_enumerable_via_enumerateDevices": False,
        "devicechange_covers_display_source_changes": False,
    }
    if CAPTURE_RECONCILIATION_SURFACES != required_surfaces:
        errors.append("CAPTURE_RECONCILIATION_SURFACES must match canonical reconciliation surfaces")

    required_device_fallback = {
        "reconcile_triggers": (
            "devicechange_if_available",
            "track_ended",
            "acquire_failure",
            "explicit_refresh",
        ),
        "requires_fresh_enumerate_devices_snapshot": True,
        "same_source_reacquire_if_identity_present": True,
        "default_same_kind_fallback_if_policy_allows": True,
        "missing_source_requires_explicit_user_selection": True,
    }
    if DEVICE_CAPTURE_FALLBACK_RULES != required_device_fallback:
        errors.append("DEVICE_CAPTURE_FALLBACK_RULES must match canonical device fallback rules")

    required_display_fallback = {
        "automatic_display_source_switch_allowed": False,
        "display_source_change_inferred_from_devicechange_or_enumerate": False,
        "reacquire_requires_explicit_user_gesture": True,
        "reacquire_path": "new_getDisplayMedia_session",
        "terminal_display_loss_maps_to_missing_source_until_reacquire": True,
    }
    if DISPLAY_CAPTURE_FALLBACK_RULES != required_display_fallback:
        errors.append("DISPLAY_CAPTURE_FALLBACK_RULES must match canonical display fallback rules")

    required_scope_boundary = {
        "capture_side_only": True,
        "output_sink_routing_in_scope": False,
        "output_sink_api_family_out_of_scope": (
            "MediaDevices.selectAudioOutput",
            "HTMLMediaElement.setSinkId",
        ),
    }
    if CAPTURE_SCOPE_BOUNDARY != required_scope_boundary:
        errors.append("CAPTURE_SCOPE_BOUNDARY must match canonical scope boundary")

    required_invariants = {
        "capture_side_scope_excludes_output_sink_routing": True,
        "enumerate_devices_is_inventory_surface_not_live_capture_truth": True,
        "devicechange_is_advisory_not_correctness_required": True,
        "display_sources_non_enumerable_and_not_devicechange_modeled": True,
        "local_stop_path_distinct_from_ended_event_path": True,
        "deterministic_fallback_rules_split_by_device_vs_display": True,
        "production_runtime_change_allowed_in_26_1": False,
    }
    if STAGE26_INVARIANTS != required_invariants:
        errors.append("STAGE26_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "scope_slot_model_failure_classes_surfaces_fallback_defined",
        "stage26_closure_and_verification_plan_defined",
        "checker_and_compileall_pass",
    )
    if STAGE26_CLOSURE_CRITERIA_26_1 != required_closure:
        errors.append("STAGE26_CLOSURE_CRITERIA_26_1 must match baseline closure criteria")

    required_verification_types = {
        "26.1": "build check",
        "26.2": "build check",
        "26.3": "build check",
        "26.4": "build check",
        "26.5": "build check",
        "26.6": "manual runtime check",
        "26.7": "build check",
    }
    if STAGE26_VERIFICATION_TYPES != required_verification_types:
        errors.append("STAGE26_VERIFICATION_TYPES must match verification map")

    required_substeps = {
        "26.1": "capture_source_device_permission_resilience_baseline_definition",
        "26.2": "media_device_inventory_permission_gated_visibility_contract",
        "26.3": "track_source_termination_semantics_contract",
        "26.4": "screen_share_capture_lifecycle_source_reselection_contract",
        "26.5": "device_change_reconciliation_contract",
        "26.6": "capture_resilience_sandbox_smoke_baseline",
        "26.7": "capture_resilience_ci_gate_baseline",
    }
    if STAGE26_SUBSTEP_DRAFT != required_substeps:
        errors.append("STAGE26_SUBSTEP_DRAFT must match stage draft")

    if STAGE25_SUBSTEP_DRAFT.get("25.7") != "incall_media_control_ci_gate_baseline":
        errors.append("Stage 25 dependency must keep 25.7 CI gate milestone")
    if STAGE25_VERIFICATION_TYPES.get("25.7") != "build check":
        errors.append("Stage 25 dependency must keep 25.7 verification as build check")

    return errors

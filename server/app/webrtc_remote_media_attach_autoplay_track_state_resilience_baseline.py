from __future__ import annotations


STAGE28_NAME = "Remote Media Attach / Autoplay / Track-State Resilience Baseline"

STAGE28_SCOPE = (
    "remote_track_arrival_attach_scope",
    "remote_stream_binding_srcobject_contract",
    "autoplay_and_play_promise_policy_handling",
    "remote_track_state_semantics_mute_unmute_ended",
    "element_remount_reattach_recovery_path",
    "sandbox_smoke_and_ci_gate_plan",
    "explicit_boundary_excluding_capture_output_transport_contracts",
)

REMOTE_MEDIA_SURFACES = {
    "track_event_surface": "RTCPeerConnection.track",
    "attach_surface": "HTMLMediaElement.srcObject",
    "playback_start_surface": "HTMLMediaElement.play",
    "autoplay_surface": "HTMLMediaElement.autoplay",
    "track_state_events": (
        "MediaStreamTrack.mute",
        "MediaStreamTrack.unmute",
        "MediaStreamTrack.ended",
    ),
    "track_muted_property_authoritative": False,
}

REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL = {
    "attach_trigger": "pc.ontrack",
    "authoritative_attach_source": "event.track_or_event.streams",
    "attach_target": "dedicated_remote_media_element",
    "duplicate_attach_guard_required": True,
    "implicit_side_effect_attach_allowed": False,
    "stable_binding_key": "receiver_track_identity",
}

AUTOPLAY_PLAY_PROMISE_MODEL = {
    "play_invocation_is_fire_and_forget": False,
    "play_promise_handling_required": True,
    "autoplay_block_has_dedicated_branch": True,
    "user_gesture_recovery_required_after_block": True,
    "autoplay_flag_allows_stream_active_start_but_not_policy_bypass": True,
    "play_rejection_must_be_observable": True,
}

REMOTE_TRACK_STATE_RESILIENCE_MODEL = {
    "temporary_interruption_surfaces": (
        "MediaStreamTrack.mute",
        "MediaStreamTrack.unmute",
    ),
    "terminal_surface": "MediaStreamTrack.ended",
    "mute_means_terminal": False,
    "ended_means_terminal": True,
    "ended_recoverable_with_same_track_object": False,
    "muted_property_primary_surface": False,
    "no_false_call_end_on_temporary_mute": True,
}

ELEMENT_REMOUNT_REATTACH_RECOVERY_MODEL = {
    "element_remount_requires_srcobject_rebind": True,
    "post_remount_requires_explicit_play_attempt": True,
    "recovery_pipeline": "attach_then_play_with_policy_handling",
    "autoplay_block_resume_path_requires_user_action": True,
    "reattach_reuses_current_remote_track_identity": True,
}

STAGE28_SCOPE_BOUNDARY = {
    "remote_media_attach_autoplay_track_state_in_scope": True,
    "capture_source_resilience_in_scope": False,
    "output_sink_routing_in_scope": False,
    "transport_quality_observability_in_scope": False,
    "negotiation_glare_restart_in_scope": False,
}

STAGE28_INVARIANTS = {
    "ontrack_is_authoritative_attach_trigger": True,
    "play_promise_outcome_handled_explicitly": True,
    "autoplay_block_modeled_as_recoverable_branch": True,
    "mute_unmute_distinct_from_ended": True,
    "temporary_remote_mute_not_terminal": True,
    "remount_reattach_pipeline_deterministic": True,
    "production_runtime_change_allowed_in_28_1": False,
}

STAGE28_CLOSURE_CRITERIA_28_1 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "scope_surfaces_attach_autoplay_track_state_defined",
    "stage28_draft_and_verification_map_defined",
    "checker_and_compileall_pass",
)

STAGE28_VERIFICATION_TYPES = {
    "28.1": "build check",
    "28.2": "build check",
    "28.3": "build check",
    "28.4": "build check",
    "28.5": "build check",
    "28.6": "manual runtime check",
    "28.7": "build check",
}

STAGE28_SUBSTEP_DRAFT = {
    "28.1": "remote_media_attach_autoplay_track_state_resilience_baseline_definition",
    "28.2": "remote_track_attach_and_ownership_contract",
    "28.3": "autoplay_play_promise_user_gesture_recovery_contract",
    "28.4": "remote_track_mute_unmute_ended_resilience_contract",
    "28.5": "media_element_remount_reattach_recovery_contract",
    "28.6": "remote_media_resilience_sandbox_smoke_baseline",
    "28.7": "remote_media_resilience_ci_gate_baseline",
}


def validate_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_audio_output_remote_playout_route_resilience_baseline import (
        STAGE27_SUBSTEP_DRAFT,
        STAGE27_VERIFICATION_TYPES,
    )
    from app.webrtc_output_route_resilience_ci_gate_baseline import (
        CI_OUTPUT_ROUTE_DEPENDENCY_STEPS,
        CI_OUTPUT_ROUTE_INVARIANTS,
    )

    if STAGE28_NAME != "Remote Media Attach / Autoplay / Track-State Resilience Baseline":
        errors.append("STAGE28_NAME must match canonical stage name")

    required_scope = (
        "remote_track_arrival_attach_scope",
        "remote_stream_binding_srcobject_contract",
        "autoplay_and_play_promise_policy_handling",
        "remote_track_state_semantics_mute_unmute_ended",
        "element_remount_reattach_recovery_path",
        "sandbox_smoke_and_ci_gate_plan",
        "explicit_boundary_excluding_capture_output_transport_contracts",
    )
    if STAGE28_SCOPE != required_scope:
        errors.append("STAGE28_SCOPE must match canonical stage scope")

    required_surfaces = {
        "track_event_surface": "RTCPeerConnection.track",
        "attach_surface": "HTMLMediaElement.srcObject",
        "playback_start_surface": "HTMLMediaElement.play",
        "autoplay_surface": "HTMLMediaElement.autoplay",
        "track_state_events": (
            "MediaStreamTrack.mute",
            "MediaStreamTrack.unmute",
            "MediaStreamTrack.ended",
        ),
        "track_muted_property_authoritative": False,
    }
    if REMOTE_MEDIA_SURFACES != required_surfaces:
        errors.append("REMOTE_MEDIA_SURFACES must match canonical surface model")

    required_attach_model = {
        "attach_trigger": "pc.ontrack",
        "authoritative_attach_source": "event.track_or_event.streams",
        "attach_target": "dedicated_remote_media_element",
        "duplicate_attach_guard_required": True,
        "implicit_side_effect_attach_allowed": False,
        "stable_binding_key": "receiver_track_identity",
    }
    if REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL != required_attach_model:
        errors.append("REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL must match canonical attach model")

    required_autoplay_model = {
        "play_invocation_is_fire_and_forget": False,
        "play_promise_handling_required": True,
        "autoplay_block_has_dedicated_branch": True,
        "user_gesture_recovery_required_after_block": True,
        "autoplay_flag_allows_stream_active_start_but_not_policy_bypass": True,
        "play_rejection_must_be_observable": True,
    }
    if AUTOPLAY_PLAY_PROMISE_MODEL != required_autoplay_model:
        errors.append("AUTOPLAY_PLAY_PROMISE_MODEL must match canonical autoplay/play model")

    required_track_state_model = {
        "temporary_interruption_surfaces": (
            "MediaStreamTrack.mute",
            "MediaStreamTrack.unmute",
        ),
        "terminal_surface": "MediaStreamTrack.ended",
        "mute_means_terminal": False,
        "ended_means_terminal": True,
        "ended_recoverable_with_same_track_object": False,
        "muted_property_primary_surface": False,
        "no_false_call_end_on_temporary_mute": True,
    }
    if REMOTE_TRACK_STATE_RESILIENCE_MODEL != required_track_state_model:
        errors.append("REMOTE_TRACK_STATE_RESILIENCE_MODEL must match canonical track-state model")

    required_reattach_model = {
        "element_remount_requires_srcobject_rebind": True,
        "post_remount_requires_explicit_play_attempt": True,
        "recovery_pipeline": "attach_then_play_with_policy_handling",
        "autoplay_block_resume_path_requires_user_action": True,
        "reattach_reuses_current_remote_track_identity": True,
    }
    if ELEMENT_REMOUNT_REATTACH_RECOVERY_MODEL != required_reattach_model:
        errors.append("ELEMENT_REMOUNT_REATTACH_RECOVERY_MODEL must match canonical remount model")

    required_scope_boundary = {
        "remote_media_attach_autoplay_track_state_in_scope": True,
        "capture_source_resilience_in_scope": False,
        "output_sink_routing_in_scope": False,
        "transport_quality_observability_in_scope": False,
        "negotiation_glare_restart_in_scope": False,
    }
    if STAGE28_SCOPE_BOUNDARY != required_scope_boundary:
        errors.append("STAGE28_SCOPE_BOUNDARY must match canonical scope boundary")

    required_invariants = {
        "ontrack_is_authoritative_attach_trigger": True,
        "play_promise_outcome_handled_explicitly": True,
        "autoplay_block_modeled_as_recoverable_branch": True,
        "mute_unmute_distinct_from_ended": True,
        "temporary_remote_mute_not_terminal": True,
        "remount_reattach_pipeline_deterministic": True,
        "production_runtime_change_allowed_in_28_1": False,
    }
    if STAGE28_INVARIANTS != required_invariants:
        errors.append("STAGE28_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "scope_surfaces_attach_autoplay_track_state_defined",
        "stage28_draft_and_verification_map_defined",
        "checker_and_compileall_pass",
    )
    if STAGE28_CLOSURE_CRITERIA_28_1 != required_closure:
        errors.append("STAGE28_CLOSURE_CRITERIA_28_1 must match closure criteria")

    required_verification_types = {
        "28.1": "build check",
        "28.2": "build check",
        "28.3": "build check",
        "28.4": "build check",
        "28.5": "build check",
        "28.6": "manual runtime check",
        "28.7": "build check",
    }
    if STAGE28_VERIFICATION_TYPES != required_verification_types:
        errors.append("STAGE28_VERIFICATION_TYPES must match verification map")

    required_substeps = {
        "28.1": "remote_media_attach_autoplay_track_state_resilience_baseline_definition",
        "28.2": "remote_track_attach_and_ownership_contract",
        "28.3": "autoplay_play_promise_user_gesture_recovery_contract",
        "28.4": "remote_track_mute_unmute_ended_resilience_contract",
        "28.5": "media_element_remount_reattach_recovery_contract",
        "28.6": "remote_media_resilience_sandbox_smoke_baseline",
        "28.7": "remote_media_resilience_ci_gate_baseline",
    }
    if STAGE28_SUBSTEP_DRAFT != required_substeps:
        errors.append("STAGE28_SUBSTEP_DRAFT must match stage draft")

    if STAGE27_SUBSTEP_DRAFT.get("27.7") != "output_route_resilience_ci_gate_baseline":
        errors.append("Stage 27 dependency must keep 27.7 CI gate milestone")

    if STAGE27_VERIFICATION_TYPES.get("27.7") != "build check":
        errors.append("Stage 27 dependency must keep 27.7 verification type as build check")

    if "27.6" not in CI_OUTPUT_ROUTE_DEPENDENCY_STEPS:
        errors.append("Stage 27 CI dependency closure must include 27.6 manual smoke")

    if CI_OUTPUT_ROUTE_INVARIANTS.get("fail_closed_behavior_required") is not True:
        errors.append("Stage 27 CI invariants must keep fail_closed_behavior_required=true")

    if CI_OUTPUT_ROUTE_INVARIANTS.get("production_runtime_path_unchanged") is not True:
        errors.append("Stage 27 CI invariants must keep production_runtime_path_unchanged=true")

    return errors

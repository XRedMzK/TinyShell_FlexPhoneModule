from __future__ import annotations


REMOTE_TRACK_RUNTIME_STATE_MODEL_28_4 = (
    "track_live_flowing",
    "track_live_temporarily_muted",
    "track_live_recovering",
    "track_ended_terminal",
)

REMOTE_TRACK_EVENT_TAXONOMY_28_4 = {
    "temporary_events": (
        "mute",
        "unmute",
    ),
    "terminal_event": "ended",
    "terminal_ready_state": "ended",
    "explicit_stop_terminal_without_ended_event": True,
}

TEMPORARY_TERMINAL_SEMANTICS_28_4 = {
    "mute_is_temporary": True,
    "unmute_is_recovery": True,
    "ended_is_terminal": True,
    "ready_state_ended_is_terminal": True,
    "terminal_recovery_in_place_allowed": False,
}

ENABLED_VS_SOURCE_MUTED_MODEL_28_4 = {
    "enabled_axis_represents_user_or_app_intent": True,
    "source_muted_axis_represents_source_availability": True,
    "axes_non_overlapping_for_runtime_classification": True,
    "mute_event_is_not_user_toggle": True,
}

REMOTE_TRACK_RUNTIME_TRANSITIONS_28_4 = {
    "track_live_flowing": (
        "track_live_temporarily_muted",
        "track_ended_terminal",
    ),
    "track_live_temporarily_muted": (
        "track_live_flowing",
        "track_ended_terminal",
    ),
    "track_live_recovering": (
        "track_live_flowing",
        "track_ended_terminal",
    ),
    "track_ended_terminal": (),
}

REMOTE_TRACK_UI_RUNTIME_BOUNDARIES_28_4 = {
    "mute_preserves_binding": True,
    "mute_not_call_terminal": True,
    "unmute_restores_existing_binding": True,
    "ended_disallows_waiting_for_unmute_same_track": True,
    "temporary_interruption_does_not_detach": True,
}

REMOTE_TRACK_INVARIANTS_28_4 = {
    "mute_non_terminal": True,
    "unmute_recovery_same_binding": True,
    "ended_terminal": True,
    "temporary_branch_preserves_binding_ownership": True,
    "enabled_vs_source_muted_explicitly_separated": True,
    "explicit_stop_terminal_without_ended_event_required": True,
    "production_runtime_change_allowed_in_28_4": False,
}

STAGE28_CLOSURE_CRITERIA_28_4 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "temporary_vs_terminal_and_enabled_vs_muted_defined",
    "explicit_stop_terminal_boundary_defined",
    "dependency_alignment_with_28_1_28_2_28_3_checker_enforced",
    "checker_and_compileall_pass",
)


def is_temporary_interruption(event_name: str | None, ready_state: str) -> bool:
    return event_name == "mute" and ready_state != "ended"


def is_terminal_end(event_name: str | None, ready_state: str, explicit_stop: bool) -> bool:
    return explicit_stop or event_name == "ended" or ready_state == "ended"


def requires_binding_preservation(event_name: str | None, terminal: bool) -> bool:
    return (event_name in {"mute", "unmute"}) and (terminal is False)


def is_user_intent_mute_vs_source_mute(user_enabled: bool, event_name: str | None) -> str:
    if event_name in {"mute", "unmute"}:
        return "source_mute_branch"
    if user_enabled is False:
        return "user_intent_mute_branch"
    return "none"


def validate_webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_media_attach_autoplay_track_state_resilience_baseline import (
        REMOTE_TRACK_STATE_RESILIENCE_MODEL,
        STAGE28_SUBSTEP_DRAFT,
        STAGE28_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_track_attach_ownership_contract_baseline import (
        REMOTE_ATTACH_INVARIANTS_28_2,
    )
    from app.webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline import (
        AUTOPLAY_PLAY_CONTRACT_INVARIANTS_28_3,
        PLAY_PROMISE_OUTCOME_TAXONOMY_28_3,
        PLAYBACK_STARTUP_STATE_MODEL_28_3,
    )

    required_states = (
        "track_live_flowing",
        "track_live_temporarily_muted",
        "track_live_recovering",
        "track_ended_terminal",
    )
    if REMOTE_TRACK_RUNTIME_STATE_MODEL_28_4 != required_states:
        errors.append("REMOTE_TRACK_RUNTIME_STATE_MODEL_28_4 must match canonical runtime state set/order")

    required_event_taxonomy = {
        "temporary_events": (
            "mute",
            "unmute",
        ),
        "terminal_event": "ended",
        "terminal_ready_state": "ended",
        "explicit_stop_terminal_without_ended_event": True,
    }
    if REMOTE_TRACK_EVENT_TAXONOMY_28_4 != required_event_taxonomy:
        errors.append("REMOTE_TRACK_EVENT_TAXONOMY_28_4 must match canonical event taxonomy")

    required_temp_terminal = {
        "mute_is_temporary": True,
        "unmute_is_recovery": True,
        "ended_is_terminal": True,
        "ready_state_ended_is_terminal": True,
        "terminal_recovery_in_place_allowed": False,
    }
    if TEMPORARY_TERMINAL_SEMANTICS_28_4 != required_temp_terminal:
        errors.append("TEMPORARY_TERMINAL_SEMANTICS_28_4 must match canonical semantics")

    required_enabled_vs_source = {
        "enabled_axis_represents_user_or_app_intent": True,
        "source_muted_axis_represents_source_availability": True,
        "axes_non_overlapping_for_runtime_classification": True,
        "mute_event_is_not_user_toggle": True,
    }
    if ENABLED_VS_SOURCE_MUTED_MODEL_28_4 != required_enabled_vs_source:
        errors.append("ENABLED_VS_SOURCE_MUTED_MODEL_28_4 must match canonical separation model")

    required_transitions = {
        "track_live_flowing": (
            "track_live_temporarily_muted",
            "track_ended_terminal",
        ),
        "track_live_temporarily_muted": (
            "track_live_flowing",
            "track_ended_terminal",
        ),
        "track_live_recovering": (
            "track_live_flowing",
            "track_ended_terminal",
        ),
        "track_ended_terminal": (),
    }
    if REMOTE_TRACK_RUNTIME_TRANSITIONS_28_4 != required_transitions:
        errors.append("REMOTE_TRACK_RUNTIME_TRANSITIONS_28_4 must match canonical transition table")

    required_ui_boundaries = {
        "mute_preserves_binding": True,
        "mute_not_call_terminal": True,
        "unmute_restores_existing_binding": True,
        "ended_disallows_waiting_for_unmute_same_track": True,
        "temporary_interruption_does_not_detach": True,
    }
    if REMOTE_TRACK_UI_RUNTIME_BOUNDARIES_28_4 != required_ui_boundaries:
        errors.append("REMOTE_TRACK_UI_RUNTIME_BOUNDARIES_28_4 must match canonical UI/runtime boundaries")

    required_invariants = {
        "mute_non_terminal": True,
        "unmute_recovery_same_binding": True,
        "ended_terminal": True,
        "temporary_branch_preserves_binding_ownership": True,
        "enabled_vs_source_muted_explicitly_separated": True,
        "explicit_stop_terminal_without_ended_event_required": True,
        "production_runtime_change_allowed_in_28_4": False,
    }
    if REMOTE_TRACK_INVARIANTS_28_4 != required_invariants:
        errors.append("REMOTE_TRACK_INVARIANTS_28_4 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "temporary_vs_terminal_and_enabled_vs_muted_defined",
        "explicit_stop_terminal_boundary_defined",
        "dependency_alignment_with_28_1_28_2_28_3_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE28_CLOSURE_CRITERIA_28_4 != required_closure:
        errors.append("STAGE28_CLOSURE_CRITERIA_28_4 must match closure criteria")

    if STAGE28_SUBSTEP_DRAFT.get("28.4") != "remote_track_mute_unmute_ended_resilience_contract":
        errors.append("Stage 28 draft must define 28.4 remote-track resilience milestone")

    if STAGE28_VERIFICATION_TYPES.get("28.4") != "build check":
        errors.append("Stage 28 verification map must keep 28.4 as build check")

    if REMOTE_TRACK_STATE_RESILIENCE_MODEL.get("mute_means_terminal") is not False:
        errors.append("28.1 track-state model must keep mute as non-terminal")

    if REMOTE_TRACK_STATE_RESILIENCE_MODEL.get("ended_means_terminal") is not True:
        errors.append("28.1 track-state model must keep ended as terminal")

    if REMOTE_TRACK_STATE_RESILIENCE_MODEL.get("muted_property_primary_surface") is not False:
        errors.append("28.1 track-state model must keep muted property non-primary")

    if "temporary_branch_preserves_binding_ownership" in REMOTE_ATTACH_INVARIANTS_28_2:
        errors.append("28.2 invariants must not redefine temporary mute semantics")

    if REMOTE_ATTACH_INVARIANTS_28_2.get("srcobject_assignment_single_writer_controlled") is not True:
        errors.append("28.2 invariants must keep single-writer attach ownership")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("NotAllowedError") != "blocked_requires_user_gesture":
        errors.append("28.3 taxonomy must keep NotAllowedError as blocked-gesture branch")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("NotSupportedError") != "source_invalid":
        errors.append("28.3 taxonomy must keep NotSupportedError as source-invalid branch")

    if "blocked_requires_user_gesture" not in PLAYBACK_STARTUP_STATE_MODEL_28_3:
        errors.append("28.3 startup states must include blocked_requires_user_gesture")

    if AUTOPLAY_PLAY_CONTRACT_INVARIANTS_28_3.get("attach_never_implies_playback_success") is not True:
        errors.append("28.3 invariants must keep attach != playback success")

    if is_temporary_interruption("mute", "live") is not True:
        errors.append("is_temporary_interruption must classify mute/live as temporary interruption")

    if is_terminal_end("ended", "live", explicit_stop=False) is not True:
        errors.append("is_terminal_end must classify ended event as terminal")

    if is_terminal_end(None, "ended", explicit_stop=False) is not True:
        errors.append("is_terminal_end must classify readyState=ended as terminal")

    if is_terminal_end(None, "live", explicit_stop=True) is not True:
        errors.append("is_terminal_end must classify explicit stop path as terminal")

    if requires_binding_preservation("mute", terminal=False) is not True:
        errors.append("requires_binding_preservation must preserve binding for non-terminal mute")

    if is_user_intent_mute_vs_source_mute(False, "mute") != "source_mute_branch":
        errors.append("source mute events must remain distinct from user intent mute branch")

    if is_user_intent_mute_vs_source_mute(False, None) != "user_intent_mute_branch":
        errors.append("disabled track without source event must map to user intent mute branch")

    return errors

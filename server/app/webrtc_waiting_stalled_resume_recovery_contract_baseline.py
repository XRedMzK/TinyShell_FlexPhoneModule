from __future__ import annotations


WAITING_STALLED_RECOVERY_SURFACES_29_4 = {
    "waiting_surface": "HTMLMediaElement.waiting",
    "stalled_surface": "HTMLMediaElement.stalled",
    "resume_surface": "HTMLMediaElement.playing",
    "canplay_support_surface": "HTMLMediaElement.canplay",
}

WAITING_STALLED_SEMANTICS_29_4 = {
    "waiting_is_temporary_starvation": True,
    "stalled_is_fetch_starvation": True,
    "waiting_equals_terminal": False,
    "stalled_equals_terminal": False,
    "waiting_stalled_non_equivalent_branches": True,
    "starvation_requires_reattach_by_default": False,
}

RESUME_SIGNAL_MODEL_29_4 = {
    "playing_is_start_or_resume_signal": True,
    "playing_equals_progress_truth": False,
    "resume_requires_followup_progress_reproof": True,
    "resume_without_progress_immediate_freeze": False,
}

CANPLAY_HINT_MODEL_29_4 = {
    "canplay_is_recovery_hint_only": True,
    "canplay_is_final_recovery_truth": False,
    "canplay_non_terminal_by_default": True,
    "canplay_without_playing_counts_as_resumed": False,
}

RESUME_GRACE_POLICY_29_4 = {
    "grace_after_resume_signal_required": True,
    "grace_after_starvation_branch_required": True,
    "during_grace_no_progress_classification": "resume_grace",
    "grace_expiry_without_progress_reverts_to_29_3_evaluation": True,
}

WAITING_STALLED_CLASSIFICATION_STATES_29_4 = (
    "starvation_waiting",
    "starvation_stalled",
    "resume_signal_received",
    "resume_grace",
    "resume_progress_unproven",
    "terminal_out_of_scope",
)

WAITING_STALLED_INVARIANTS_29_4 = {
    "waiting_stalled_non_terminal_by_default": True,
    "waiting_stalled_separately_classifiable": True,
    "playing_resume_signal_not_progress_truth": True,
    "canplay_hint_not_final_recovery_truth": True,
    "starvation_not_equal_terminal_failure": True,
    "resume_grace_before_freeze_recheck_required": True,
    "production_runtime_change_allowed_in_29_4": False,
}

STAGE29_CLOSURE_CRITERIA_29_4 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "waiting_stalled_playing_canplay_boundaries_explicit",
    "resume_grace_semantics_before_freeze_recheck_explicit",
    "dependency_alignment_with_29_1_29_2_29_3_and_28_terminal_boundary_checker_enforced",
    "checker_and_compileall_pass",
)


def is_waiting_starvation(event_name: str | None) -> bool:
    return event_name == "waiting"


def is_stalled_starvation(event_name: str | None) -> bool:
    return event_name == "stalled"


def is_resume_signal(event_name: str | None) -> bool:
    return event_name == "playing"


def is_canplay_hint(event_name: str | None) -> bool:
    return event_name == "canplay"


def requires_reattach_on_starvation(event_name: str | None, terminal: bool) -> bool:
    return terminal and event_name in {"waiting", "stalled"}


def classify_waiting_stalled_resume_state(
    waiting_seen: bool,
    stalled_seen: bool,
    playing_seen: bool,
    in_grace_window: bool,
    terminal: bool,
) -> str:
    if terminal:
        return "terminal_out_of_scope"
    if stalled_seen and not playing_seen:
        return "starvation_stalled"
    if waiting_seen and not playing_seen:
        return "starvation_waiting"
    if playing_seen and in_grace_window:
        return "resume_grace"
    if playing_seen:
        return "resume_signal_received"
    return "resume_progress_unproven"


def validate_webrtc_waiting_stalled_resume_recovery_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline import (
        RENDER_STALL_RECOVERY_MODEL,
        STAGE29_SUBSTEP_DRAFT,
        STAGE29_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_video_first_frame_readiness_contract_baseline import (
        FIRST_FRAME_INVARIANTS_29_2,
    )
    from app.webrtc_frame_progress_freeze_detection_observability_contract_baseline import (
        FRAME_PROGRESS_CONTEXT_EVENT_CLASSIFIER_29_3,
        FRAME_PROGRESS_INVARIANTS_29_3,
    )
    from app.webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline import (
        TEMPORARY_TERMINAL_SEMANTICS_28_4,
    )

    required_surfaces = {
        "waiting_surface": "HTMLMediaElement.waiting",
        "stalled_surface": "HTMLMediaElement.stalled",
        "resume_surface": "HTMLMediaElement.playing",
        "canplay_support_surface": "HTMLMediaElement.canplay",
    }
    if WAITING_STALLED_RECOVERY_SURFACES_29_4 != required_surfaces:
        errors.append("WAITING_STALLED_RECOVERY_SURFACES_29_4 must match canonical surfaces")

    required_semantics = {
        "waiting_is_temporary_starvation": True,
        "stalled_is_fetch_starvation": True,
        "waiting_equals_terminal": False,
        "stalled_equals_terminal": False,
        "waiting_stalled_non_equivalent_branches": True,
        "starvation_requires_reattach_by_default": False,
    }
    if WAITING_STALLED_SEMANTICS_29_4 != required_semantics:
        errors.append("WAITING_STALLED_SEMANTICS_29_4 must match canonical starvation semantics")

    required_resume_model = {
        "playing_is_start_or_resume_signal": True,
        "playing_equals_progress_truth": False,
        "resume_requires_followup_progress_reproof": True,
        "resume_without_progress_immediate_freeze": False,
    }
    if RESUME_SIGNAL_MODEL_29_4 != required_resume_model:
        errors.append("RESUME_SIGNAL_MODEL_29_4 must match canonical resume model")

    required_canplay_hint = {
        "canplay_is_recovery_hint_only": True,
        "canplay_is_final_recovery_truth": False,
        "canplay_non_terminal_by_default": True,
        "canplay_without_playing_counts_as_resumed": False,
    }
    if CANPLAY_HINT_MODEL_29_4 != required_canplay_hint:
        errors.append("CANPLAY_HINT_MODEL_29_4 must match canonical canplay hint model")

    required_grace_policy = {
        "grace_after_resume_signal_required": True,
        "grace_after_starvation_branch_required": True,
        "during_grace_no_progress_classification": "resume_grace",
        "grace_expiry_without_progress_reverts_to_29_3_evaluation": True,
    }
    if RESUME_GRACE_POLICY_29_4 != required_grace_policy:
        errors.append("RESUME_GRACE_POLICY_29_4 must match canonical resume-grace policy")

    required_states = (
        "starvation_waiting",
        "starvation_stalled",
        "resume_signal_received",
        "resume_grace",
        "resume_progress_unproven",
        "terminal_out_of_scope",
    )
    if WAITING_STALLED_CLASSIFICATION_STATES_29_4 != required_states:
        errors.append("WAITING_STALLED_CLASSIFICATION_STATES_29_4 must match canonical state set/order")

    required_invariants = {
        "waiting_stalled_non_terminal_by_default": True,
        "waiting_stalled_separately_classifiable": True,
        "playing_resume_signal_not_progress_truth": True,
        "canplay_hint_not_final_recovery_truth": True,
        "starvation_not_equal_terminal_failure": True,
        "resume_grace_before_freeze_recheck_required": True,
        "production_runtime_change_allowed_in_29_4": False,
    }
    if WAITING_STALLED_INVARIANTS_29_4 != required_invariants:
        errors.append("WAITING_STALLED_INVARIANTS_29_4 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "waiting_stalled_playing_canplay_boundaries_explicit",
        "resume_grace_semantics_before_freeze_recheck_explicit",
        "dependency_alignment_with_29_1_29_2_29_3_and_28_terminal_boundary_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE29_CLOSURE_CRITERIA_29_4 != required_closure:
        errors.append("STAGE29_CLOSURE_CRITERIA_29_4 must match closure criteria")

    if STAGE29_SUBSTEP_DRAFT.get("29.4") != "waiting_stalled_resume_recovery_contract":
        errors.append("Stage 29 draft must keep 29.4 waiting/stalled-resume milestone")

    if STAGE29_VERIFICATION_TYPES.get("29.4") != "build check":
        errors.append("Stage 29 verification map must keep 29.4 as build check")

    if RENDER_STALL_RECOVERY_MODEL.get("waiting_is_recoverable_starvation") is not True:
        errors.append("29.1 recovery model must keep waiting recoverable-starvation semantics")

    if RENDER_STALL_RECOVERY_MODEL.get("stalled_is_recoverable_starvation") is not True:
        errors.append("29.1 recovery model must keep stalled recoverable-starvation semantics")

    if FIRST_FRAME_INVARIANTS_29_2.get("playing_not_ongoing_frame_progress_truth") is not True:
        errors.append("29.2 invariants must keep playing separate from progress truth")

    if FRAME_PROGRESS_CONTEXT_EVENT_CLASSIFIER_29_3.get("playing_sets_active_context") is not True:
        errors.append("29.3 context model must keep playing as active context signal")

    if FRAME_PROGRESS_CONTEXT_EVENT_CLASSIFIER_29_3.get("waiting_sets_starvation_context") is not True:
        errors.append("29.3 context model must keep waiting starvation context signal")

    if FRAME_PROGRESS_CONTEXT_EVENT_CLASSIFIER_29_3.get("stalled_sets_starvation_context") is not True:
        errors.append("29.3 context model must keep stalled starvation context signal")

    if FRAME_PROGRESS_INVARIANTS_29_3.get("waiting_stalled_non_terminal_context") is not True:
        errors.append("29.3 invariants must keep waiting/stalled as non-terminal context")

    if TEMPORARY_TERMINAL_SEMANTICS_28_4.get("ended_is_terminal") is not True:
        errors.append("28.4 terminal model must keep ended terminal semantics")

    if is_waiting_starvation("waiting") is not True:
        errors.append("is_waiting_starvation must classify waiting event")

    if is_stalled_starvation("stalled") is not True:
        errors.append("is_stalled_starvation must classify stalled event")

    if is_resume_signal("playing") is not True:
        errors.append("is_resume_signal must classify playing event")

    if is_canplay_hint("canplay") is not True:
        errors.append("is_canplay_hint must classify canplay event")

    if requires_reattach_on_starvation("waiting", terminal=False) is not False:
        errors.append("requires_reattach_on_starvation must not require reattach for non-terminal waiting")

    if classify_waiting_stalled_resume_state(
        waiting_seen=True,
        stalled_seen=False,
        playing_seen=False,
        in_grace_window=False,
        terminal=False,
    ) != "starvation_waiting":
        errors.append("classify_waiting_stalled_resume_state must map waiting branch to starvation_waiting")

    if classify_waiting_stalled_resume_state(
        waiting_seen=False,
        stalled_seen=True,
        playing_seen=False,
        in_grace_window=False,
        terminal=False,
    ) != "starvation_stalled":
        errors.append("classify_waiting_stalled_resume_state must map stalled branch to starvation_stalled")

    if classify_waiting_stalled_resume_state(
        waiting_seen=True,
        stalled_seen=False,
        playing_seen=True,
        in_grace_window=True,
        terminal=False,
    ) != "resume_grace":
        errors.append("classify_waiting_stalled_resume_state must keep resume_grace branch after resume signal")

    if classify_waiting_stalled_resume_state(
        waiting_seen=False,
        stalled_seen=False,
        playing_seen=True,
        in_grace_window=False,
        terminal=False,
    ) != "resume_signal_received":
        errors.append("classify_waiting_stalled_resume_state must map post-grace playing to resume_signal_received")

    if classify_waiting_stalled_resume_state(
        waiting_seen=False,
        stalled_seen=False,
        playing_seen=False,
        in_grace_window=False,
        terminal=True,
    ) != "terminal_out_of_scope":
        errors.append("classify_waiting_stalled_resume_state must map terminal branch to terminal_out_of_scope")

    return errors

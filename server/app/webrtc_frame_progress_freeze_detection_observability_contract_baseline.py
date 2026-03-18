from __future__ import annotations


FRAME_PROGRESS_SURFACES_29_3 = {
    "primary_progress_surface": "HTMLVideoElement.requestVideoFrameCallback",
    "primary_surface_required": False,
    "fallback_progress_surface": "HTMLVideoElement.getVideoPlaybackQuality",
    "contextual_events": (
        "HTMLMediaElement.playing",
        "HTMLMediaElement.waiting",
        "HTMLMediaElement.stalled",
    ),
}

FRAME_PROGRESS_PROOF_MODEL_29_3 = {
    "rvfc_presentedframes_delta_is_primary_proof": True,
    "quality_totalvideoframes_delta_is_fallback_proof": True,
    "dropped_corrupted_delay_are_contextual_counters": True,
    "first_frame_readiness_equals_ongoing_progress": False,
    "playing_event_equals_progress_truth": False,
    "waiting_stalled_are_context_only": True,
}

FREEZE_GRACE_WINDOW_POLICY_29_3 = {
    "grace_after_playing_start_required": True,
    "grace_after_waiting_stalled_resume_required": True,
    "grace_after_remount_reattach_required": True,
    "freeze_requires_active_playback_context": True,
    "freeze_requires_no_progress_beyond_grace": True,
    "no_progress_without_active_context_means_unproven": True,
}

FALLBACK_QUALITY_METRICS_29_3 = {
    "totalVideoFrames_delta_required": True,
    "droppedVideoFrames_observed": True,
    "corruptedVideoFrames_observed": True,
    "totalFrameDelay_observed": True,
    "single_sample_absolute_value_sufficient": False,
}

FRAME_PROGRESS_CLASSIFICATION_STATES_29_3 = (
    "progress_observed",
    "progress_unproven",
    "resume_grace",
    "starvation_context",
    "freeze_suspected",
    "unsupported",
)

FRAME_PROGRESS_CONTEXT_EVENT_CLASSIFIER_29_3 = {
    "playing_sets_active_context": True,
    "waiting_sets_starvation_context": True,
    "stalled_sets_starvation_context": True,
    "context_events_alone_not_progress_proof": True,
    "terminal_ended_not_classified_as_freeze": True,
}

FRAME_PROGRESS_INVARIANTS_29_3 = {
    "first_frame_and_ongoing_progress_separated": True,
    "playing_not_progress_truth": True,
    "waiting_stalled_non_terminal_context": True,
    "freeze_requires_context_and_window": True,
    "rvfc_primary_with_fallback_quality_branch": True,
    "unsupported_branch_explicit": True,
    "production_runtime_change_allowed_in_29_3": False,
}

STAGE29_CLOSURE_CRITERIA_29_3 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "rvfc_primary_and_quality_fallback_models_explicit",
    "context_boundary_and_grace_window_rules_explicit",
    "dependency_alignment_with_29_1_29_2_and_28_terminal_boundary_checker_enforced",
    "checker_and_compileall_pass",
)


def is_progress_source_supported(rvfc_supported: bool, playback_quality_supported: bool) -> bool:
    return rvfc_supported or playback_quality_supported


def has_rvfc_progress(previous_presented_frames: int | None, current_presented_frames: int | None) -> bool:
    return (
        previous_presented_frames is not None
        and current_presented_frames is not None
        and current_presented_frames > previous_presented_frames
    )


def has_quality_progress(previous_total_video_frames: int | None, current_total_video_frames: int | None) -> bool:
    return (
        previous_total_video_frames is not None
        and current_total_video_frames is not None
        and current_total_video_frames > previous_total_video_frames
    )


def should_suspect_freeze(
    progress_observed: bool,
    active_playback_context: bool,
    in_grace_window: bool,
) -> bool:
    return (not progress_observed) and active_playback_context and (not in_grace_window)


def classify_frame_progress_state(
    progress_observed: bool,
    active_playback_context: bool,
    starvation_context: bool,
    in_grace_window: bool,
    supported: bool,
) -> str:
    if not supported:
        return "unsupported"
    if progress_observed:
        return "progress_observed"
    if starvation_context:
        return "starvation_context"
    if in_grace_window:
        return "resume_grace"
    if active_playback_context:
        return "freeze_suspected"
    return "progress_unproven"


def validate_webrtc_frame_progress_freeze_detection_observability_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline import (
        FIRST_FRAME_PROGRESS_MODEL,
        REMOTE_VIDEO_SURFACES,
        RENDER_STALL_RECOVERY_MODEL,
        STAGE29_SUBSTEP_DRAFT,
        STAGE29_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_video_first_frame_readiness_contract_baseline import (
        FIRST_FRAME_INVARIANTS_29_2,
    )
    from app.webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline import (
        TEMPORARY_TERMINAL_SEMANTICS_28_4,
    )

    required_surfaces = {
        "primary_progress_surface": "HTMLVideoElement.requestVideoFrameCallback",
        "primary_surface_required": False,
        "fallback_progress_surface": "HTMLVideoElement.getVideoPlaybackQuality",
        "contextual_events": (
            "HTMLMediaElement.playing",
            "HTMLMediaElement.waiting",
            "HTMLMediaElement.stalled",
        ),
    }
    if FRAME_PROGRESS_SURFACES_29_3 != required_surfaces:
        errors.append("FRAME_PROGRESS_SURFACES_29_3 must match canonical progress surfaces")

    required_proof_model = {
        "rvfc_presentedframes_delta_is_primary_proof": True,
        "quality_totalvideoframes_delta_is_fallback_proof": True,
        "dropped_corrupted_delay_are_contextual_counters": True,
        "first_frame_readiness_equals_ongoing_progress": False,
        "playing_event_equals_progress_truth": False,
        "waiting_stalled_are_context_only": True,
    }
    if FRAME_PROGRESS_PROOF_MODEL_29_3 != required_proof_model:
        errors.append("FRAME_PROGRESS_PROOF_MODEL_29_3 must match canonical proof model")

    required_grace_policy = {
        "grace_after_playing_start_required": True,
        "grace_after_waiting_stalled_resume_required": True,
        "grace_after_remount_reattach_required": True,
        "freeze_requires_active_playback_context": True,
        "freeze_requires_no_progress_beyond_grace": True,
        "no_progress_without_active_context_means_unproven": True,
    }
    if FREEZE_GRACE_WINDOW_POLICY_29_3 != required_grace_policy:
        errors.append("FREEZE_GRACE_WINDOW_POLICY_29_3 must match canonical grace-window policy")

    required_quality_metrics = {
        "totalVideoFrames_delta_required": True,
        "droppedVideoFrames_observed": True,
        "corruptedVideoFrames_observed": True,
        "totalFrameDelay_observed": True,
        "single_sample_absolute_value_sufficient": False,
    }
    if FALLBACK_QUALITY_METRICS_29_3 != required_quality_metrics:
        errors.append("FALLBACK_QUALITY_METRICS_29_3 must match canonical fallback metrics model")

    required_states = (
        "progress_observed",
        "progress_unproven",
        "resume_grace",
        "starvation_context",
        "freeze_suspected",
        "unsupported",
    )
    if FRAME_PROGRESS_CLASSIFICATION_STATES_29_3 != required_states:
        errors.append("FRAME_PROGRESS_CLASSIFICATION_STATES_29_3 must match canonical states")

    required_context_classifier = {
        "playing_sets_active_context": True,
        "waiting_sets_starvation_context": True,
        "stalled_sets_starvation_context": True,
        "context_events_alone_not_progress_proof": True,
        "terminal_ended_not_classified_as_freeze": True,
    }
    if FRAME_PROGRESS_CONTEXT_EVENT_CLASSIFIER_29_3 != required_context_classifier:
        errors.append("FRAME_PROGRESS_CONTEXT_EVENT_CLASSIFIER_29_3 must match canonical context model")

    required_invariants = {
        "first_frame_and_ongoing_progress_separated": True,
        "playing_not_progress_truth": True,
        "waiting_stalled_non_terminal_context": True,
        "freeze_requires_context_and_window": True,
        "rvfc_primary_with_fallback_quality_branch": True,
        "unsupported_branch_explicit": True,
        "production_runtime_change_allowed_in_29_3": False,
    }
    if FRAME_PROGRESS_INVARIANTS_29_3 != required_invariants:
        errors.append("FRAME_PROGRESS_INVARIANTS_29_3 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "rvfc_primary_and_quality_fallback_models_explicit",
        "context_boundary_and_grace_window_rules_explicit",
        "dependency_alignment_with_29_1_29_2_and_28_terminal_boundary_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE29_CLOSURE_CRITERIA_29_3 != required_closure:
        errors.append("STAGE29_CLOSURE_CRITERIA_29_3 must match closure criteria")

    if STAGE29_SUBSTEP_DRAFT.get("29.3") != "frame_progress_freeze_detection_observability_contract":
        errors.append("Stage 29 draft must keep 29.3 observability milestone")

    if STAGE29_VERIFICATION_TYPES.get("29.3") != "build check":
        errors.append("Stage 29 verification map must keep 29.3 as build check")

    if REMOTE_VIDEO_SURFACES.get("frame_callback_surface") != "HTMLVideoElement.requestVideoFrameCallback":
        errors.append("29.1 surfaces must keep requestVideoFrameCallback as optional primary frame surface")

    if REMOTE_VIDEO_SURFACES.get("frame_progress_fallback_surface") != "HTMLVideoElement.getVideoPlaybackQuality":
        errors.append("29.1 surfaces must keep getVideoPlaybackQuality as fallback frame surface")

    if FIRST_FRAME_PROGRESS_MODEL.get("ongoing_progress_separate_from_first_frame_readiness") is not True:
        errors.append("29.1 model must keep ongoing progress separated from first-frame readiness")

    if RENDER_STALL_RECOVERY_MODEL.get("waiting_is_recoverable_starvation") is not True:
        errors.append("29.1 model must keep waiting as recoverable starvation")

    if RENDER_STALL_RECOVERY_MODEL.get("stalled_is_recoverable_starvation") is not True:
        errors.append("29.1 model must keep stalled as recoverable starvation")

    if FIRST_FRAME_INVARIANTS_29_2.get("playing_not_ongoing_frame_progress_truth") is not True:
        errors.append("29.2 invariants must keep playing != ongoing frame-progress truth")

    if FIRST_FRAME_INVARIANTS_29_2.get("loadeddata_minimum_first_frame_threshold") is not True:
        errors.append("29.2 invariants must keep loadeddata minimum first-frame threshold")

    if TEMPORARY_TERMINAL_SEMANTICS_28_4.get("ended_is_terminal") is not True:
        errors.append("28.4 terminal semantics must keep ended terminal")

    if is_progress_source_supported(False, False) is not False:
        errors.append("is_progress_source_supported must require rvfc or fallback surface")

    if has_rvfc_progress(10, 11) is not True:
        errors.append("has_rvfc_progress must detect presentedFrames growth")

    if has_rvfc_progress(10, 10) is not False:
        errors.append("has_rvfc_progress must reject non-growing presentedFrames")

    if has_quality_progress(20, 21) is not True:
        errors.append("has_quality_progress must detect totalVideoFrames growth")

    if has_quality_progress(20, 20) is not False:
        errors.append("has_quality_progress must reject non-growing totalVideoFrames")

    if should_suspect_freeze(progress_observed=False, active_playback_context=True, in_grace_window=False) is not True:
        errors.append("should_suspect_freeze must classify no-progress active-context outside grace as freeze")

    if should_suspect_freeze(progress_observed=False, active_playback_context=True, in_grace_window=True) is not False:
        errors.append("should_suspect_freeze must suppress freeze during grace window")

    if classify_frame_progress_state(
        progress_observed=True,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=False,
        supported=True,
    ) != "progress_observed":
        errors.append("classify_frame_progress_state must prefer progress_observed when progress exists")

    if classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=True,
        starvation_context=True,
        in_grace_window=False,
        supported=True,
    ) != "starvation_context":
        errors.append("classify_frame_progress_state must classify waiting/stalled branch as starvation_context")

    if classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=True,
        supported=True,
    ) != "resume_grace":
        errors.append("classify_frame_progress_state must classify grace window before freeze")

    if classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=False,
        supported=True,
    ) != "freeze_suspected":
        errors.append("classify_frame_progress_state must classify freeze_suspected when active no-progress outside grace")

    if classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=False,
        starvation_context=False,
        in_grace_window=False,
        supported=True,
    ) != "progress_unproven":
        errors.append("classify_frame_progress_state must keep no-context no-progress as progress_unproven")

    if classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=False,
        starvation_context=False,
        in_grace_window=False,
        supported=False,
    ) != "unsupported":
        errors.append("classify_frame_progress_state must return unsupported when no supported progress surface")

    return errors

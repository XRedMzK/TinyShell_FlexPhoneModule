from __future__ import annotations


STAGE29_NAME = "Remote Video First-Frame / Render-Stall / Dimension-Change Resilience Baseline"

STAGE29_SCOPE = (
    "remote_video_first_frame_readiness_scope",
    "frame_progress_truth_scope",
    "waiting_stalled_recovery_scope",
    "dimension_change_reconciliation_scope",
    "optional_rvfc_with_playback_quality_fallback",
    "sandbox_smoke_and_ci_gate_plan",
    "explicit_boundary_excluding_new_transport_or_signaling_contracts",
)

REMOTE_VIDEO_SURFACES = {
    "metadata_surface": "HTMLMediaElement.loadedmetadata",
    "first_frame_surface": "HTMLMediaElement.loadeddata",
    "playing_surface": "HTMLMediaElement.playing",
    "waiting_surface": "HTMLMediaElement.waiting",
    "stalled_surface": "HTMLMediaElement.stalled",
    "resize_surface": "HTMLVideoElement.resize",
    "frame_callback_surface": "HTMLVideoElement.requestVideoFrameCallback",
    "frame_progress_fallback_surface": "HTMLVideoElement.getVideoPlaybackQuality",
    "frame_callback_baseline_required": False,
}

FIRST_FRAME_PROGRESS_MODEL = {
    "play_or_autoplay_intent_equals_first_frame_truth": False,
    "loadeddata_establishes_first_frame_readiness": True,
    "playing_establishes_playback_started_or_resumed": True,
    "ongoing_progress_separate_from_first_frame_readiness": True,
    "rvfc_primary_when_supported": True,
    "fallback_required_when_rvfc_unavailable": True,
}

RENDER_STALL_RECOVERY_MODEL = {
    "waiting_is_recoverable_starvation": True,
    "stalled_is_recoverable_starvation": True,
    "waiting_or_stalled_terminal_by_default": False,
    "last_rendered_frame_may_persist_during_starvation": True,
    "resume_requires_explicit_progress_recovery_signal": True,
}

DIMENSION_CHANGE_RECONCILIATION_MODEL = {
    "loadedmetadata_initializes_dimension_truth": True,
    "resize_updates_dimension_truth": True,
    "dimension_change_terminal_by_default": False,
    "dimension_reconcile_requires_explicit_runtime_update": True,
}

STAGE29_SCOPE_BOUNDARY = {
    "remote_video_render_truth_in_scope": True,
    "new_webrtc_transport_or_signaling_contracts_in_scope": False,
    "datachannel_baselines_in_scope": False,
    "capture_output_route_baselines_in_scope": False,
    "audio_only_render_contracts_in_scope": False,
}

STAGE29_INVARIANTS = {
    "first_frame_truth_separate_from_play_intent": True,
    "ongoing_progress_separate_from_first_frame": True,
    "waiting_stalled_non_terminal_branches": True,
    "terminal_end_not_merged_with_waiting_stalled": True,
    "dimension_truth_reconciled_via_loadedmetadata_resize": True,
    "rvfc_optional_with_explicit_fallback": True,
    "production_runtime_change_allowed_in_29_1": False,
}

STAGE29_CLOSURE_CRITERIA_29_1 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "first_frame_progress_starvation_dimension_contracts_defined",
    "stage29_draft_and_verification_map_defined",
    "checker_and_compileall_pass",
)

STAGE29_VERIFICATION_TYPES = {
    "29.1": "build check",
    "29.2": "build check",
    "29.3": "build check",
    "29.4": "build check",
    "29.5": "build check",
    "29.6": "manual runtime check",
    "29.7": "build check",
}

STAGE29_SUBSTEP_DRAFT = {
    "29.1": "remote_video_first_frame_render_stall_dimension_change_resilience_baseline_definition",
    "29.2": "remote_video_first_frame_readiness_contract",
    "29.3": "frame_progress_freeze_detection_observability_contract",
    "29.4": "waiting_stalled_resume_recovery_contract",
    "29.5": "dimension_resize_reconciliation_contract",
    "29.6": "remote_video_resilience_sandbox_smoke_baseline",
    "29.7": "remote_video_resilience_ci_gate_baseline",
}


def validate_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_media_resilience_ci_gate_baseline import (
        CI_REMOTE_MEDIA_DEPENDENCY_STEPS,
        CI_REMOTE_MEDIA_INVARIANTS,
        WORKFLOW_BASELINE_28_7,
    )
    from app.webrtc_remote_media_attach_autoplay_track_state_resilience_baseline import (
        STAGE28_SUBSTEP_DRAFT,
        STAGE28_VERIFICATION_TYPES,
    )
    from app.webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline import (
        PLAY_PROMISE_OUTCOME_TAXONOMY_28_3,
    )
    from app.webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline import (
        TEMPORARY_TERMINAL_SEMANTICS_28_4,
    )

    if STAGE29_NAME != "Remote Video First-Frame / Render-Stall / Dimension-Change Resilience Baseline":
        errors.append("STAGE29_NAME must match canonical stage name")

    required_scope = (
        "remote_video_first_frame_readiness_scope",
        "frame_progress_truth_scope",
        "waiting_stalled_recovery_scope",
        "dimension_change_reconciliation_scope",
        "optional_rvfc_with_playback_quality_fallback",
        "sandbox_smoke_and_ci_gate_plan",
        "explicit_boundary_excluding_new_transport_or_signaling_contracts",
    )
    if STAGE29_SCOPE != required_scope:
        errors.append("STAGE29_SCOPE must match canonical stage scope")

    required_surfaces = {
        "metadata_surface": "HTMLMediaElement.loadedmetadata",
        "first_frame_surface": "HTMLMediaElement.loadeddata",
        "playing_surface": "HTMLMediaElement.playing",
        "waiting_surface": "HTMLMediaElement.waiting",
        "stalled_surface": "HTMLMediaElement.stalled",
        "resize_surface": "HTMLVideoElement.resize",
        "frame_callback_surface": "HTMLVideoElement.requestVideoFrameCallback",
        "frame_progress_fallback_surface": "HTMLVideoElement.getVideoPlaybackQuality",
        "frame_callback_baseline_required": False,
    }
    if REMOTE_VIDEO_SURFACES != required_surfaces:
        errors.append("REMOTE_VIDEO_SURFACES must match canonical remote-video surface model")

    required_first_frame_progress = {
        "play_or_autoplay_intent_equals_first_frame_truth": False,
        "loadeddata_establishes_first_frame_readiness": True,
        "playing_establishes_playback_started_or_resumed": True,
        "ongoing_progress_separate_from_first_frame_readiness": True,
        "rvfc_primary_when_supported": True,
        "fallback_required_when_rvfc_unavailable": True,
    }
    if FIRST_FRAME_PROGRESS_MODEL != required_first_frame_progress:
        errors.append("FIRST_FRAME_PROGRESS_MODEL must match canonical first-frame/progress model")

    required_stall_recovery = {
        "waiting_is_recoverable_starvation": True,
        "stalled_is_recoverable_starvation": True,
        "waiting_or_stalled_terminal_by_default": False,
        "last_rendered_frame_may_persist_during_starvation": True,
        "resume_requires_explicit_progress_recovery_signal": True,
    }
    if RENDER_STALL_RECOVERY_MODEL != required_stall_recovery:
        errors.append("RENDER_STALL_RECOVERY_MODEL must match canonical starvation/recovery model")

    required_dimension_reconcile = {
        "loadedmetadata_initializes_dimension_truth": True,
        "resize_updates_dimension_truth": True,
        "dimension_change_terminal_by_default": False,
        "dimension_reconcile_requires_explicit_runtime_update": True,
    }
    if DIMENSION_CHANGE_RECONCILIATION_MODEL != required_dimension_reconcile:
        errors.append("DIMENSION_CHANGE_RECONCILIATION_MODEL must match canonical dimension model")

    required_scope_boundary = {
        "remote_video_render_truth_in_scope": True,
        "new_webrtc_transport_or_signaling_contracts_in_scope": False,
        "datachannel_baselines_in_scope": False,
        "capture_output_route_baselines_in_scope": False,
        "audio_only_render_contracts_in_scope": False,
    }
    if STAGE29_SCOPE_BOUNDARY != required_scope_boundary:
        errors.append("STAGE29_SCOPE_BOUNDARY must match canonical boundary map")

    required_invariants = {
        "first_frame_truth_separate_from_play_intent": True,
        "ongoing_progress_separate_from_first_frame": True,
        "waiting_stalled_non_terminal_branches": True,
        "terminal_end_not_merged_with_waiting_stalled": True,
        "dimension_truth_reconciled_via_loadedmetadata_resize": True,
        "rvfc_optional_with_explicit_fallback": True,
        "production_runtime_change_allowed_in_29_1": False,
    }
    if STAGE29_INVARIANTS != required_invariants:
        errors.append("STAGE29_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "first_frame_progress_starvation_dimension_contracts_defined",
        "stage29_draft_and_verification_map_defined",
        "checker_and_compileall_pass",
    )
    if STAGE29_CLOSURE_CRITERIA_29_1 != required_closure:
        errors.append("STAGE29_CLOSURE_CRITERIA_29_1 must match closure criteria")

    required_verification_types = {
        "29.1": "build check",
        "29.2": "build check",
        "29.3": "build check",
        "29.4": "build check",
        "29.5": "build check",
        "29.6": "manual runtime check",
        "29.7": "build check",
    }
    if STAGE29_VERIFICATION_TYPES != required_verification_types:
        errors.append("STAGE29_VERIFICATION_TYPES must match verification map")

    required_substeps = {
        "29.1": "remote_video_first_frame_render_stall_dimension_change_resilience_baseline_definition",
        "29.2": "remote_video_first_frame_readiness_contract",
        "29.3": "frame_progress_freeze_detection_observability_contract",
        "29.4": "waiting_stalled_resume_recovery_contract",
        "29.5": "dimension_resize_reconciliation_contract",
        "29.6": "remote_video_resilience_sandbox_smoke_baseline",
        "29.7": "remote_video_resilience_ci_gate_baseline",
    }
    if STAGE29_SUBSTEP_DRAFT != required_substeps:
        errors.append("STAGE29_SUBSTEP_DRAFT must match stage draft")

    if STAGE28_SUBSTEP_DRAFT.get("28.7") != "remote_media_resilience_ci_gate_baseline":
        errors.append("Stage 28 dependency must keep 28.7 CI gate milestone")

    if STAGE28_VERIFICATION_TYPES.get("28.7") != "build check":
        errors.append("Stage 28 dependency must keep 28.7 verification type as build check")

    if "28.6" not in CI_REMOTE_MEDIA_DEPENDENCY_STEPS:
        errors.append("Stage 28 CI dependency closure must include 28.6 manual smoke")

    if CI_REMOTE_MEDIA_INVARIANTS.get("fail_closed_behavior_required") is not True:
        errors.append("Stage 28 CI invariants must keep fail_closed behavior")

    required_workflow_28_7 = {
        "workflow_path": ".github/workflows/webrtc-remote-media-resilience-ci.yml",
        "job_name": "webrtc-remote-media-resilience-gate",
        "runner_script": "server/tools/run_webrtc_remote_media_resilience_ci_gate.py",
    }
    if WORKFLOW_BASELINE_28_7 != required_workflow_28_7:
        errors.append("Stage 28 workflow baseline must remain canonical")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("NotAllowedError") != "blocked_requires_user_gesture":
        errors.append("Stage 28 autoplay taxonomy must keep NotAllowedError blocked branch")

    if TEMPORARY_TERMINAL_SEMANTICS_28_4.get("ended_is_terminal") is not True:
        errors.append("Stage 28 terminal semantics must keep ended terminal")

    return errors

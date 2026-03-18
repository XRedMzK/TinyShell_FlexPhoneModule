from __future__ import annotations


FIRST_FRAME_READINESS_SURFACES_29_2 = {
    "metadata_surface": "HTMLMediaElement.loadedmetadata",
    "first_frame_surface": "HTMLMediaElement.loadeddata",
    "play_intent_surface": "HTMLMediaElement.play",
    "playback_started_surface": "HTMLMediaElement.playing",
    "readystate_support_surface": "HTMLMediaElement.readyState",
}

FIRST_FRAME_NON_EQUIVALENCE_RULES_29_2 = {
    "loadedmetadata_equals_first_frame_proof": False,
    "play_equals_first_frame_proof": False,
    "play_equals_playback_truth": False,
    "playing_equals_ongoing_frame_progress_proof": False,
    "attach_only_equals_first_frame_proof": False,
}

FIRST_FRAME_READYSTATE_SUPPORT_MODEL_29_2 = {
    "ready_state_primary_truth_source": False,
    "loadeddata_primary_first_frame_threshold": True,
    "equivalent_fallback_allowed": True,
    "fallback_minimum_ready_state": "HAVE_CURRENT_DATA",
    "fallback_threshold_value": 2,
    "fallback_requires_explicit_guard": True,
}

FIRST_FRAME_RUNTIME_STATE_MODEL_29_2 = (
    "video_unattached",
    "metadata_known_dimensions_ready",
    "play_requested_first_frame_pending",
    "playback_started_first_frame_unproven",
    "first_frame_ready",
    "playback_started_frame_progress_pending",
)

FIRST_FRAME_RUNTIME_TRANSITIONS_29_2 = {
    "video_unattached": (
        "metadata_known_dimensions_ready",
        "play_requested_first_frame_pending",
    ),
    "metadata_known_dimensions_ready": (
        "play_requested_first_frame_pending",
        "first_frame_ready",
    ),
    "play_requested_first_frame_pending": (
        "playback_started_first_frame_unproven",
        "first_frame_ready",
    ),
    "playback_started_first_frame_unproven": (
        "first_frame_ready",
    ),
    "first_frame_ready": (
        "playback_started_frame_progress_pending",
    ),
    "playback_started_frame_progress_pending": (),
}

FIRST_FRAME_INVARIANTS_29_2 = {
    "loadedmetadata_not_first_frame_proof": True,
    "play_not_first_frame_or_playback_truth": True,
    "loadeddata_minimum_first_frame_threshold": True,
    "playing_not_ongoing_frame_progress_truth": True,
    "ready_state_supporting_not_primary": True,
    "playing_without_first_frame_keeps_unproven_branch": True,
    "production_runtime_change_allowed_in_29_2": False,
}

STAGE29_CLOSURE_CRITERIA_29_2 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "first_frame_threshold_and_non_equivalence_rules_explicit",
    "dependency_alignment_with_29_1_and_28x_checker_enforced",
    "checker_and_compileall_pass",
)


def is_first_frame_readiness_event(event_name: str | None) -> bool:
    return event_name == "loadeddata"


def is_equivalent_first_frame_fallback(
    ready_state: int | None,
    loadeddata_seen: bool,
    fallback_enabled: bool,
) -> bool:
    return (
        fallback_enabled
        and (loadeddata_seen is False)
        and (ready_state is not None)
        and (ready_state >= 2)
    )


def is_first_frame_proven(
    loadeddata_seen: bool,
    ready_state: int | None,
    fallback_enabled: bool,
) -> bool:
    return loadeddata_seen or is_equivalent_first_frame_fallback(
        ready_state=ready_state,
        loadeddata_seen=loadeddata_seen,
        fallback_enabled=fallback_enabled,
    )


def can_classify_playback_started(event_name: str | None) -> bool:
    return event_name == "playing"


def classify_first_frame_state(
    metadata_seen: bool,
    play_seen: bool,
    playing_seen: bool,
    first_frame_proven: bool,
) -> str:
    if first_frame_proven and playing_seen:
        return "playback_started_frame_progress_pending"
    if first_frame_proven:
        return "first_frame_ready"
    if playing_seen:
        return "playback_started_first_frame_unproven"
    if play_seen:
        return "play_requested_first_frame_pending"
    if metadata_seen:
        return "metadata_known_dimensions_ready"
    return "video_unattached"


def validate_webrtc_remote_video_first_frame_readiness_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline import (
        FIRST_FRAME_PROGRESS_MODEL,
        REMOTE_VIDEO_SURFACES,
        STAGE29_SUBSTEP_DRAFT,
        STAGE29_VERIFICATION_TYPES,
    )
    from app.webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline import (
        PLAY_PROMISE_OUTCOME_TAXONOMY_28_3,
    )
    from app.webrtc_remote_track_attach_ownership_contract_baseline import (
        REMOTE_ATTACH_TARGET_SCHEMA_28_2,
    )

    required_surfaces = {
        "metadata_surface": "HTMLMediaElement.loadedmetadata",
        "first_frame_surface": "HTMLMediaElement.loadeddata",
        "play_intent_surface": "HTMLMediaElement.play",
        "playback_started_surface": "HTMLMediaElement.playing",
        "readystate_support_surface": "HTMLMediaElement.readyState",
    }
    if FIRST_FRAME_READINESS_SURFACES_29_2 != required_surfaces:
        errors.append("FIRST_FRAME_READINESS_SURFACES_29_2 must match canonical first-frame surfaces")

    required_non_equivalence = {
        "loadedmetadata_equals_first_frame_proof": False,
        "play_equals_first_frame_proof": False,
        "play_equals_playback_truth": False,
        "playing_equals_ongoing_frame_progress_proof": False,
        "attach_only_equals_first_frame_proof": False,
    }
    if FIRST_FRAME_NON_EQUIVALENCE_RULES_29_2 != required_non_equivalence:
        errors.append("FIRST_FRAME_NON_EQUIVALENCE_RULES_29_2 must match canonical non-equivalence rules")

    required_ready_state_model = {
        "ready_state_primary_truth_source": False,
        "loadeddata_primary_first_frame_threshold": True,
        "equivalent_fallback_allowed": True,
        "fallback_minimum_ready_state": "HAVE_CURRENT_DATA",
        "fallback_threshold_value": 2,
        "fallback_requires_explicit_guard": True,
    }
    if FIRST_FRAME_READYSTATE_SUPPORT_MODEL_29_2 != required_ready_state_model:
        errors.append("FIRST_FRAME_READYSTATE_SUPPORT_MODEL_29_2 must match canonical readyState support model")

    required_states = (
        "video_unattached",
        "metadata_known_dimensions_ready",
        "play_requested_first_frame_pending",
        "playback_started_first_frame_unproven",
        "first_frame_ready",
        "playback_started_frame_progress_pending",
    )
    if FIRST_FRAME_RUNTIME_STATE_MODEL_29_2 != required_states:
        errors.append("FIRST_FRAME_RUNTIME_STATE_MODEL_29_2 must match canonical first-frame state set/order")

    required_transitions = {
        "video_unattached": (
            "metadata_known_dimensions_ready",
            "play_requested_first_frame_pending",
        ),
        "metadata_known_dimensions_ready": (
            "play_requested_first_frame_pending",
            "first_frame_ready",
        ),
        "play_requested_first_frame_pending": (
            "playback_started_first_frame_unproven",
            "first_frame_ready",
        ),
        "playback_started_first_frame_unproven": (
            "first_frame_ready",
        ),
        "first_frame_ready": (
            "playback_started_frame_progress_pending",
        ),
        "playback_started_frame_progress_pending": (),
    }
    if FIRST_FRAME_RUNTIME_TRANSITIONS_29_2 != required_transitions:
        errors.append("FIRST_FRAME_RUNTIME_TRANSITIONS_29_2 must match canonical transition map")

    required_invariants = {
        "loadedmetadata_not_first_frame_proof": True,
        "play_not_first_frame_or_playback_truth": True,
        "loadeddata_minimum_first_frame_threshold": True,
        "playing_not_ongoing_frame_progress_truth": True,
        "ready_state_supporting_not_primary": True,
        "playing_without_first_frame_keeps_unproven_branch": True,
        "production_runtime_change_allowed_in_29_2": False,
    }
    if FIRST_FRAME_INVARIANTS_29_2 != required_invariants:
        errors.append("FIRST_FRAME_INVARIANTS_29_2 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "first_frame_threshold_and_non_equivalence_rules_explicit",
        "dependency_alignment_with_29_1_and_28x_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE29_CLOSURE_CRITERIA_29_2 != required_closure:
        errors.append("STAGE29_CLOSURE_CRITERIA_29_2 must match closure criteria")

    if STAGE29_SUBSTEP_DRAFT.get("29.2") != "remote_video_first_frame_readiness_contract":
        errors.append("Stage 29 draft must keep 29.2 first-frame readiness milestone")

    if STAGE29_VERIFICATION_TYPES.get("29.2") != "build check":
        errors.append("Stage 29 verification map must keep 29.2 as build check")

    if REMOTE_VIDEO_SURFACES.get("metadata_surface") != "HTMLMediaElement.loadedmetadata":
        errors.append("29.1 surfaces must keep loadedmetadata as metadata surface")

    if REMOTE_VIDEO_SURFACES.get("first_frame_surface") != "HTMLMediaElement.loadeddata":
        errors.append("29.1 surfaces must keep loadeddata as first-frame surface")

    if FIRST_FRAME_PROGRESS_MODEL.get("loadeddata_establishes_first_frame_readiness") is not True:
        errors.append("29.1 progress model must keep loadeddata as first-frame readiness threshold")

    if FIRST_FRAME_PROGRESS_MODEL.get("ongoing_progress_separate_from_first_frame_readiness") is not True:
        errors.append("29.1 progress model must keep ongoing progress separate from first-frame readiness")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("resolved") != "playing":
        errors.append("28.3 autoplay taxonomy must keep resolved->playing mapping")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("NotAllowedError") != "blocked_requires_user_gesture":
        errors.append("28.3 autoplay taxonomy must keep NotAllowedError blocked branch")

    if REMOTE_ATTACH_TARGET_SCHEMA_28_2.get("attach_property") != "HTMLMediaElement.srcObject":
        errors.append("28.2 attach target must keep srcObject assignment as canonical attach path")

    if is_first_frame_readiness_event("loadeddata") is not True:
        errors.append("is_first_frame_readiness_event must classify loadeddata as first-frame proof")

    if is_first_frame_readiness_event("loadedmetadata") is not False:
        errors.append("is_first_frame_readiness_event must not classify loadedmetadata as first-frame proof")

    if is_equivalent_first_frame_fallback(2, loadeddata_seen=False, fallback_enabled=True) is not True:
        errors.append("is_equivalent_first_frame_fallback must allow explicit HAVE_CURRENT_DATA fallback")

    if is_equivalent_first_frame_fallback(1, loadeddata_seen=False, fallback_enabled=True) is not False:
        errors.append("is_equivalent_first_frame_fallback must reject readyState below HAVE_CURRENT_DATA")

    if is_first_frame_proven(loadeddata_seen=False, ready_state=2, fallback_enabled=True) is not True:
        errors.append("is_first_frame_proven must allow explicit readyState fallback when enabled")

    if is_first_frame_proven(loadeddata_seen=False, ready_state=1, fallback_enabled=True) is not False:
        errors.append("is_first_frame_proven must reject insufficient readyState without loadeddata")

    if can_classify_playback_started("playing") is not True:
        errors.append("can_classify_playback_started must classify playing event as playback started")

    if can_classify_playback_started("play") is not False:
        errors.append("can_classify_playback_started must not classify play event as playback started")

    if classify_first_frame_state(
        metadata_seen=True,
        play_seen=True,
        playing_seen=True,
        first_frame_proven=False,
    ) != "playback_started_first_frame_unproven":
        errors.append("classify_first_frame_state must preserve playback_started_first_frame_unproven branch")

    if classify_first_frame_state(
        metadata_seen=True,
        play_seen=True,
        playing_seen=True,
        first_frame_proven=True,
    ) != "playback_started_frame_progress_pending":
        errors.append("classify_first_frame_state must allow playback_started_frame_progress_pending after first-frame proof")

    return errors

from __future__ import annotations


PLAYBACK_STARTUP_STATE_MODEL_28_3 = (
    "unattached",
    "attached_pending_playback",
    "play_attempt_inflight",
    "playing",
    "blocked_requires_user_gesture",
    "playback_start_failed",
    "source_invalid",
)

AUTOPLAY_INTENT_VS_PLAYBACK_TRUTH_MODEL_28_3 = {
    "attach_equals_playback_started": False,
    "autoplay_flag_is_intent_only": True,
    "playback_truth_source": "HTMLMediaElement.play_promise_outcome",
    "play_attempt_observation_required": True,
}

PLAY_PROMISE_OUTCOME_TAXONOMY_28_3 = {
    "resolved": "playing",
    "NotAllowedError": "blocked_requires_user_gesture",
    "NotSupportedError": "source_invalid",
    "other_rejection": "playback_start_failed",
}

AUTOPLAY_BLOCK_RECOVERY_POLICY_28_3 = {
    "blocked_state": "blocked_requires_user_gesture",
    "background_auto_retry_allowed": False,
    "retry_requires_explicit_user_action": True,
    "retry_success_state": "playing",
    "retry_blocked_state_persists": True,
}

POLICY_SOURCE_FAILURE_SEPARATION_28_3 = {
    "NotAllowedError_branch": "policy_or_user_gesture_block",
    "NotSupportedError_branch": "source_or_media_invalid",
    "branches_non_overlapping": True,
    "advisory_policy_hints_non_authoritative": True,
}

PLAYBACK_START_TRANSITIONS_28_3 = {
    "unattached": (
        "attached_pending_playback",
    ),
    "attached_pending_playback": (
        "play_attempt_inflight",
    ),
    "play_attempt_inflight": (
        "playing",
        "blocked_requires_user_gesture",
        "source_invalid",
        "playback_start_failed",
    ),
    "blocked_requires_user_gesture": (
        "play_attempt_inflight",
    ),
    "playing": (),
    "source_invalid": (),
    "playback_start_failed": (),
}

AUTOPLAY_PLAY_CONTRACT_INVARIANTS_28_3 = {
    "attach_never_implies_playback_success": True,
    "autoplay_intent_not_success_guarantee": True,
    "play_attempt_outcome_always_classified": True,
    "notallowed_vs_notsupported_separated": True,
    "blocked_requires_explicit_user_gesture_recovery": True,
    "no_infinite_blocked_autoplay_retry": True,
    "production_runtime_change_allowed_in_28_3": False,
}

STAGE28_CLOSURE_CRITERIA_28_3 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "playback_truth_and_play_promise_taxonomy_defined",
    "blocked_recovery_and_failure_separation_defined",
    "dependency_alignment_with_28_1_28_2_checker_enforced",
    "checker_and_compileall_pass",
)


def is_policy_block(error_name: str | None) -> bool:
    return error_name == "NotAllowedError"


def is_source_invalid(error_name: str | None) -> bool:
    return error_name == "NotSupportedError"


def requires_user_gesture_recovery(state: str, error_name: str | None) -> bool:
    return state == "blocked_requires_user_gesture" or is_policy_block(error_name)


def can_retry_play_from_explicit_action(state: str, explicit_user_action: bool) -> bool:
    return explicit_user_action and state in {
        "blocked_requires_user_gesture",
        "playback_start_failed",
    }


def validate_webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_media_attach_autoplay_track_state_resilience_baseline import (
        AUTOPLAY_PLAY_PROMISE_MODEL,
        REMOTE_MEDIA_SURFACES,
        STAGE28_SUBSTEP_DRAFT,
        STAGE28_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_track_attach_ownership_contract_baseline import (
        REMOTE_ATTACH_INVARIANTS_28_2,
        REMOTE_ATTACH_TARGET_SCHEMA_28_2,
    )

    required_states = (
        "unattached",
        "attached_pending_playback",
        "play_attempt_inflight",
        "playing",
        "blocked_requires_user_gesture",
        "playback_start_failed",
        "source_invalid",
    )
    if PLAYBACK_STARTUP_STATE_MODEL_28_3 != required_states:
        errors.append("PLAYBACK_STARTUP_STATE_MODEL_28_3 must match canonical state set/order")

    required_intent_model = {
        "attach_equals_playback_started": False,
        "autoplay_flag_is_intent_only": True,
        "playback_truth_source": "HTMLMediaElement.play_promise_outcome",
        "play_attempt_observation_required": True,
    }
    if AUTOPLAY_INTENT_VS_PLAYBACK_TRUTH_MODEL_28_3 != required_intent_model:
        errors.append("AUTOPLAY_INTENT_VS_PLAYBACK_TRUTH_MODEL_28_3 must match canonical intent/truth model")

    required_outcome_taxonomy = {
        "resolved": "playing",
        "NotAllowedError": "blocked_requires_user_gesture",
        "NotSupportedError": "source_invalid",
        "other_rejection": "playback_start_failed",
    }
    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3 != required_outcome_taxonomy:
        errors.append("PLAY_PROMISE_OUTCOME_TAXONOMY_28_3 must match canonical outcome taxonomy")

    required_recovery_policy = {
        "blocked_state": "blocked_requires_user_gesture",
        "background_auto_retry_allowed": False,
        "retry_requires_explicit_user_action": True,
        "retry_success_state": "playing",
        "retry_blocked_state_persists": True,
    }
    if AUTOPLAY_BLOCK_RECOVERY_POLICY_28_3 != required_recovery_policy:
        errors.append("AUTOPLAY_BLOCK_RECOVERY_POLICY_28_3 must match canonical blocked-recovery policy")

    required_separation = {
        "NotAllowedError_branch": "policy_or_user_gesture_block",
        "NotSupportedError_branch": "source_or_media_invalid",
        "branches_non_overlapping": True,
        "advisory_policy_hints_non_authoritative": True,
    }
    if POLICY_SOURCE_FAILURE_SEPARATION_28_3 != required_separation:
        errors.append("POLICY_SOURCE_FAILURE_SEPARATION_28_3 must match canonical failure separation")

    required_transitions = {
        "unattached": (
            "attached_pending_playback",
        ),
        "attached_pending_playback": (
            "play_attempt_inflight",
        ),
        "play_attempt_inflight": (
            "playing",
            "blocked_requires_user_gesture",
            "source_invalid",
            "playback_start_failed",
        ),
        "blocked_requires_user_gesture": (
            "play_attempt_inflight",
        ),
        "playing": (),
        "source_invalid": (),
        "playback_start_failed": (),
    }
    if PLAYBACK_START_TRANSITIONS_28_3 != required_transitions:
        errors.append("PLAYBACK_START_TRANSITIONS_28_3 must match canonical transition table")

    required_invariants = {
        "attach_never_implies_playback_success": True,
        "autoplay_intent_not_success_guarantee": True,
        "play_attempt_outcome_always_classified": True,
        "notallowed_vs_notsupported_separated": True,
        "blocked_requires_explicit_user_gesture_recovery": True,
        "no_infinite_blocked_autoplay_retry": True,
        "production_runtime_change_allowed_in_28_3": False,
    }
    if AUTOPLAY_PLAY_CONTRACT_INVARIANTS_28_3 != required_invariants:
        errors.append("AUTOPLAY_PLAY_CONTRACT_INVARIANTS_28_3 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "playback_truth_and_play_promise_taxonomy_defined",
        "blocked_recovery_and_failure_separation_defined",
        "dependency_alignment_with_28_1_28_2_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE28_CLOSURE_CRITERIA_28_3 != required_closure:
        errors.append("STAGE28_CLOSURE_CRITERIA_28_3 must match closure criteria")

    if STAGE28_SUBSTEP_DRAFT.get("28.3") != "autoplay_play_promise_user_gesture_recovery_contract":
        errors.append("Stage 28 draft must define 28.3 autoplay/play recovery milestone")

    if STAGE28_VERIFICATION_TYPES.get("28.3") != "build check":
        errors.append("Stage 28 verification map must keep 28.3 as build check")

    if AUTOPLAY_PLAY_PROMISE_MODEL.get("play_promise_handling_required") is not True:
        errors.append("28.1 autoplay model must require explicit play-promise handling")

    if AUTOPLAY_PLAY_PROMISE_MODEL.get("autoplay_block_has_dedicated_branch") is not True:
        errors.append("28.1 autoplay model must keep dedicated autoplay-block branch")

    if REMOTE_MEDIA_SURFACES.get("playback_start_surface") != "HTMLMediaElement.play":
        errors.append("28.1 media surfaces must keep HTMLMediaElement.play as playback start surface")

    if REMOTE_ATTACH_TARGET_SCHEMA_28_2.get("attach_property") != "HTMLMediaElement.srcObject":
        errors.append("28.2 attach schema must keep srcObject as attach property")

    if REMOTE_ATTACH_INVARIANTS_28_2.get("srcobject_assignment_single_writer_controlled") is not True:
        errors.append("28.2 invariants must keep single-writer srcObject assignment control")

    if is_policy_block("NotAllowedError") is not True:
        errors.append("is_policy_block must classify NotAllowedError as policy block")

    if is_source_invalid("NotSupportedError") is not True:
        errors.append("is_source_invalid must classify NotSupportedError as source-invalid")

    if requires_user_gesture_recovery("blocked_requires_user_gesture", None) is not True:
        errors.append("requires_user_gesture_recovery must require explicit user branch for blocked state")

    if can_retry_play_from_explicit_action("blocked_requires_user_gesture", True) is not True:
        errors.append("can_retry_play_from_explicit_action must allow explicit retry for blocked state")

    return errors

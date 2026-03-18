from __future__ import annotations


REMOUNT_REATTACH_BINDING_STATE_SCHEMA_28_5 = {
    "required_fields": (
        "owner_key",
        "current_element_key",
        "provider_binding_key",
        "attached_track_ids",
        "reattach_revision",
    ),
    "ownership_outlives_element_instance": True,
    "binding_writer_model": "single_writer_owner_controller",
    "track_membership_comparison": "identity_membership_set",
}

REMOUNT_DETECTION_TRANSFER_MODEL_28_5 = {
    "remount_detected_when_owner_same_element_changed": True,
    "remount_waits_for_new_ontrack": False,
    "remount_branch": "legitimate_reattach",
    "transfer_sequence": (
        "mark_old_element_pending_teardown",
        "mark_new_element_reattach_pending",
        "replay_attach_play_sequence",
    ),
}

OLD_ELEMENT_TEARDOWN_POLICY_28_5 = {
    "teardown_required_for_potentially_playing_detached_element": True,
    "teardown_actions": (
        "revoke_old_element_ownership",
        "pause_old_element",
        "optional_srcobject_clear",
    ),
    "implicit_detached_element_cleanup_allowed": False,
}

REPLAY_SAFE_REATTACH_SEQUENCE_28_5 = {
    "sequence": (
        "bind_new_element_target",
        "assign_srcobject",
        "start_new_media_load_cycle",
        "attempt_play_once",
        "classify_play_outcome",
    ),
    "play_outcome_taxonomy_source": "step_28_3_play_promise_outcome",
    "fire_and_forget_play_allowed": False,
    "repeat_remount_behavior_deterministic": True,
}

DUPLICATE_VS_LEGITIMATE_REATTACH_GUARD_28_5 = {
    "duplicate_condition": (
        "same_owner_key",
        "same_element_key",
        "same_provider_binding",
    ),
    "duplicate_action": "noop",
    "duplicate_reassigns_srcobject": False,
    "legitimate_remount_condition": (
        "same_owner_key",
        "element_key_changed",
    ),
    "legitimate_remount_action": "replay_attach_play_sequence",
}

REATTACH_ABORT_CLASSIFICATION_28_5 = {
    "abort_error_branch": "reattach_replay_interrupted",
    "abort_is_policy_block": False,
    "abort_is_source_invalid": False,
    "owner_driven_current_attempt_authoritative": True,
}

ELEMENT_REMOUNT_RUNTIME_TRANSITIONS_28_5 = {
    "attached": (
        "remount_detected",
        "duplicate_noop",
    ),
    "remount_detected": (
        "old_owner_revoked",
    ),
    "old_owner_revoked": (
        "reattach_pending",
    ),
    "reattach_pending": (
        "play_attempt_inflight",
    ),
    "play_attempt_inflight": (
        "playing",
        "blocked_requires_user_gesture",
        "source_invalid",
        "playback_start_failed",
        "reattach_replay_interrupted",
    ),
    "reattach_replay_interrupted": (
        "play_attempt_inflight",
    ),
    "playing": (),
    "blocked_requires_user_gesture": (),
    "source_invalid": (),
    "playback_start_failed": (),
    "duplicate_noop": (),
}

ELEMENT_REMOUNT_REATTACH_INVARIANTS_28_5 = {
    "binding_ownership_outlives_dom_element": True,
    "remount_never_waits_for_new_ontrack_for_existing_binding": True,
    "old_element_teardown_explicit_for_detached_playback_risk": True,
    "reattach_replays_srcobject_plus_observed_play_outcome": True,
    "duplicate_vs_legitimate_reattach_deterministically_separated": True,
    "aborterror_mapped_to_transitional_replay_branch": True,
    "production_runtime_change_allowed_in_28_5": False,
}

STAGE28_CLOSURE_CRITERIA_28_5 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "ownership_outlives_element_and_old_element_teardown_defined",
    "remount_replay_sequence_and_abort_safe_classification_defined",
    "dependency_alignment_with_28_1_28_2_28_3_28_4_checker_enforced",
    "checker_and_compileall_pass",
)


def is_same_element_duplicate_attach(
    same_owner_key: bool,
    same_element_key: bool,
    same_provider_binding: bool,
) -> bool:
    return same_owner_key and same_element_key and same_provider_binding


def is_legitimate_remount_reattach(same_owner_key: bool, element_instance_changed: bool) -> bool:
    return same_owner_key and element_instance_changed


def requires_old_element_teardown(old_element_exists: bool, old_element_potentially_playing: bool) -> bool:
    return old_element_exists and old_element_potentially_playing


def is_abort_safe_replay_outcome(error_name: str | None, during_reattach: bool) -> bool:
    return during_reattach and error_name == "AbortError"


def validate_webrtc_media_element_remount_reattach_recovery_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_media_attach_autoplay_track_state_resilience_baseline import (
        ELEMENT_REMOUNT_REATTACH_RECOVERY_MODEL,
        STAGE28_SUBSTEP_DRAFT,
        STAGE28_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_track_attach_ownership_contract_baseline import (
        REMOTE_ATTACH_INVARIANTS_28_2,
        REMOTE_ATTACH_TRANSITIONS_28_2,
    )
    from app.webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline import (
        PLAY_PROMISE_OUTCOME_TAXONOMY_28_3,
        PLAYBACK_STARTUP_STATE_MODEL_28_3,
    )
    from app.webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline import (
        REMOTE_TRACK_INVARIANTS_28_4,
        REMOTE_TRACK_RUNTIME_STATE_MODEL_28_4,
    )

    required_state_schema = {
        "required_fields": (
            "owner_key",
            "current_element_key",
            "provider_binding_key",
            "attached_track_ids",
            "reattach_revision",
        ),
        "ownership_outlives_element_instance": True,
        "binding_writer_model": "single_writer_owner_controller",
        "track_membership_comparison": "identity_membership_set",
    }
    if REMOUNT_REATTACH_BINDING_STATE_SCHEMA_28_5 != required_state_schema:
        errors.append("REMOUNT_REATTACH_BINDING_STATE_SCHEMA_28_5 must match canonical state schema")

    required_remount_transfer = {
        "remount_detected_when_owner_same_element_changed": True,
        "remount_waits_for_new_ontrack": False,
        "remount_branch": "legitimate_reattach",
        "transfer_sequence": (
            "mark_old_element_pending_teardown",
            "mark_new_element_reattach_pending",
            "replay_attach_play_sequence",
        ),
    }
    if REMOUNT_DETECTION_TRANSFER_MODEL_28_5 != required_remount_transfer:
        errors.append("REMOUNT_DETECTION_TRANSFER_MODEL_28_5 must match canonical remount-transfer contract")

    required_old_teardown = {
        "teardown_required_for_potentially_playing_detached_element": True,
        "teardown_actions": (
            "revoke_old_element_ownership",
            "pause_old_element",
            "optional_srcobject_clear",
        ),
        "implicit_detached_element_cleanup_allowed": False,
    }
    if OLD_ELEMENT_TEARDOWN_POLICY_28_5 != required_old_teardown:
        errors.append("OLD_ELEMENT_TEARDOWN_POLICY_28_5 must match canonical teardown policy")

    required_replay_sequence = {
        "sequence": (
            "bind_new_element_target",
            "assign_srcobject",
            "start_new_media_load_cycle",
            "attempt_play_once",
            "classify_play_outcome",
        ),
        "play_outcome_taxonomy_source": "step_28_3_play_promise_outcome",
        "fire_and_forget_play_allowed": False,
        "repeat_remount_behavior_deterministic": True,
    }
    if REPLAY_SAFE_REATTACH_SEQUENCE_28_5 != required_replay_sequence:
        errors.append("REPLAY_SAFE_REATTACH_SEQUENCE_28_5 must match canonical replay-safe sequence")

    required_duplicate_guard = {
        "duplicate_condition": (
            "same_owner_key",
            "same_element_key",
            "same_provider_binding",
        ),
        "duplicate_action": "noop",
        "duplicate_reassigns_srcobject": False,
        "legitimate_remount_condition": (
            "same_owner_key",
            "element_key_changed",
        ),
        "legitimate_remount_action": "replay_attach_play_sequence",
    }
    if DUPLICATE_VS_LEGITIMATE_REATTACH_GUARD_28_5 != required_duplicate_guard:
        errors.append(
            "DUPLICATE_VS_LEGITIMATE_REATTACH_GUARD_28_5 must match duplicate-vs-reattach guard"
        )

    required_abort_classification = {
        "abort_error_branch": "reattach_replay_interrupted",
        "abort_is_policy_block": False,
        "abort_is_source_invalid": False,
        "owner_driven_current_attempt_authoritative": True,
    }
    if REATTACH_ABORT_CLASSIFICATION_28_5 != required_abort_classification:
        errors.append("REATTACH_ABORT_CLASSIFICATION_28_5 must match canonical abort classification")

    required_runtime_transitions = {
        "attached": (
            "remount_detected",
            "duplicate_noop",
        ),
        "remount_detected": (
            "old_owner_revoked",
        ),
        "old_owner_revoked": (
            "reattach_pending",
        ),
        "reattach_pending": (
            "play_attempt_inflight",
        ),
        "play_attempt_inflight": (
            "playing",
            "blocked_requires_user_gesture",
            "source_invalid",
            "playback_start_failed",
            "reattach_replay_interrupted",
        ),
        "reattach_replay_interrupted": (
            "play_attempt_inflight",
        ),
        "playing": (),
        "blocked_requires_user_gesture": (),
        "source_invalid": (),
        "playback_start_failed": (),
        "duplicate_noop": (),
    }
    if ELEMENT_REMOUNT_RUNTIME_TRANSITIONS_28_5 != required_runtime_transitions:
        errors.append("ELEMENT_REMOUNT_RUNTIME_TRANSITIONS_28_5 must match canonical transition table")

    required_invariants = {
        "binding_ownership_outlives_dom_element": True,
        "remount_never_waits_for_new_ontrack_for_existing_binding": True,
        "old_element_teardown_explicit_for_detached_playback_risk": True,
        "reattach_replays_srcobject_plus_observed_play_outcome": True,
        "duplicate_vs_legitimate_reattach_deterministically_separated": True,
        "aborterror_mapped_to_transitional_replay_branch": True,
        "production_runtime_change_allowed_in_28_5": False,
    }
    if ELEMENT_REMOUNT_REATTACH_INVARIANTS_28_5 != required_invariants:
        errors.append("ELEMENT_REMOUNT_REATTACH_INVARIANTS_28_5 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "ownership_outlives_element_and_old_element_teardown_defined",
        "remount_replay_sequence_and_abort_safe_classification_defined",
        "dependency_alignment_with_28_1_28_2_28_3_28_4_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE28_CLOSURE_CRITERIA_28_5 != required_closure:
        errors.append("STAGE28_CLOSURE_CRITERIA_28_5 must match closure criteria")

    if STAGE28_SUBSTEP_DRAFT.get("28.5") != "media_element_remount_reattach_recovery_contract":
        errors.append("Stage 28 draft must define 28.5 media-element-remount milestone")

    if STAGE28_VERIFICATION_TYPES.get("28.5") != "build check":
        errors.append("Stage 28 verification map must keep 28.5 as build check")

    required_28_1_model = {
        "element_remount_requires_srcobject_rebind": True,
        "post_remount_requires_explicit_play_attempt": True,
        "recovery_pipeline": "attach_then_play_with_policy_handling",
        "autoplay_block_resume_path_requires_user_action": True,
        "reattach_reuses_current_remote_track_identity": True,
    }
    if ELEMENT_REMOUNT_REATTACH_RECOVERY_MODEL != required_28_1_model:
        errors.append("28.1 remount model must keep canonical remount/reattach baseline")

    if REMOTE_ATTACH_TRANSITIONS_28_2.get("remount") != "reattach_same_binding":
        errors.append("28.2 transitions must keep remount->reattach_same_binding contract")

    if REMOTE_ATTACH_INVARIANTS_28_2.get("stable_remount_reattach_semantics") is not True:
        errors.append("28.2 invariants must keep stable remount/reattach semantics")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("NotAllowedError") != "blocked_requires_user_gesture":
        errors.append("28.3 taxonomy must keep NotAllowedError autoplay-policy branch")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("NotSupportedError") != "source_invalid":
        errors.append("28.3 taxonomy must keep NotSupportedError source-invalid branch")

    if "play_attempt_inflight" not in PLAYBACK_STARTUP_STATE_MODEL_28_3:
        errors.append("28.3 state model must include play_attempt_inflight for replay-safe remount")

    if REMOTE_TRACK_INVARIANTS_28_4.get("temporary_branch_preserves_binding_ownership") is not True:
        errors.append("28.4 invariants must keep temporary branch binding preservation")

    if "track_ended_terminal" not in REMOTE_TRACK_RUNTIME_STATE_MODEL_28_4:
        errors.append("28.4 runtime states must include terminal ended branch")

    if is_same_element_duplicate_attach(True, True, True) is not True:
        errors.append("is_same_element_duplicate_attach must classify unchanged owner/element/provider as duplicate")

    if is_legitimate_remount_reattach(True, True) is not True:
        errors.append("is_legitimate_remount_reattach must classify owner-stable element-changed path")

    if requires_old_element_teardown(old_element_exists=True, old_element_potentially_playing=True) is not True:
        errors.append("requires_old_element_teardown must require teardown for potentially playing old element")

    if is_abort_safe_replay_outcome("AbortError", during_reattach=True) is not True:
        errors.append("is_abort_safe_replay_outcome must classify AbortError during reattach as replay interruption")

    return errors

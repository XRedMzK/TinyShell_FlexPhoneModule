from __future__ import annotations


CI_REMOTE_MEDIA_SCENARIO_IDS = (
    "A_clean_remote_attach",
    "B_streamless_remote_attach",
    "C_autoplay_blocked_user_gesture_recovery",
    "D_temporary_interruption_mute_unmute",
    "E_terminal_track_end",
    "F_remount_reattach_abort_safe_replay",
)

CI_REMOTE_MEDIA_DEPENDENCY_STEPS = (
    "27.7",
    "28.1",
    "28.2",
    "28.3",
    "28.4",
    "28.5",
    "28.6",
)

CI_REMOTE_MEDIA_REQUIRED_INVARIANTS = {
    "A_clean_remote_attach": (
        "ontrack_attach_with_stream",
        "play_resolved_to_playing",
    ),
    "B_streamless_remote_attach": (
        "streamless_fallback_binding",
        "duplicate_attach_noop",
    ),
    "C_autoplay_blocked_user_gesture_recovery": (
        "blocked_requires_user_gesture_branch",
        "explicit_retry_recovered_to_playing",
    ),
    "D_temporary_interruption_mute_unmute": (
        "mute_non_terminal",
        "unmute_restores_flowing_without_reattach",
    ),
    "E_terminal_track_end": (
        "ended_terminal_state",
        "no_fake_in_place_auto_recovery",
    ),
    "F_remount_reattach_abort_safe_replay": (
        "old_element_teardown_before_new_playback",
        "aborterror_transitional_replay_branch",
        "reattach_retry_recovered_to_playing",
    ),
}

CI_REMOTE_MEDIA_EVIDENCE_SCHEMA_REQUIRED_FIELDS = (
    "scenario_id",
    "executed_at",
    "runtime",
    "browser_engine",
    "track_kind",
    "has_stream",
    "initial_play_outcome",
    "retry_play_outcome",
    "mute_seen",
    "unmute_seen",
    "ended_seen",
    "old_element_torn_down",
    "duplicate_attach_prevented",
    "final_binding_owner_key",
    "result",
    "proof_refs",
    "verified_invariants",
    "notes",
)

CI_REMOTE_MEDIA_OUTCOME_MODEL = (
    "PASS",
    "FAIL",
    "UNSUPPORTED",
)

CI_REMOTE_MEDIA_FAIL_CONDITIONS = (
    "dependency_checker_missing_or_failed",
    "baseline_artifact_missing",
    "smoke_evidence_manifest_missing",
    "required_scenario_missing",
    "required_invariant_marker_missing",
    "unsupported_treated_as_pass",
    "compile_or_import_failure",
)

CI_REMOTE_MEDIA_INVARIANTS = {
    "ci_validates_contract_and_evidence_not_full_browser_policy_truth": True,
    "manual_smoke_evidence_required": True,
    "streamless_attach_branch_enforced": True,
    "autoplay_blocked_recovery_branch_enforced": True,
    "temporary_vs_terminal_track_branch_enforced": True,
    "remount_abort_transitional_branch_enforced": True,
    "unsupported_is_explicit_non_pass_outcome": True,
    "fail_closed_behavior_required": True,
    "production_runtime_path_unchanged": True,
}

WORKFLOW_BASELINE_28_7 = {
    "workflow_path": ".github/workflows/webrtc-remote-media-resilience-ci.yml",
    "job_name": "webrtc-remote-media-resilience-gate",
    "runner_script": "server/tools/run_webrtc_remote_media_resilience_ci_gate.py",
}


def validate_webrtc_remote_media_resilience_ci_gate_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_output_route_resilience_ci_gate_baseline import (
        CI_OUTPUT_ROUTE_DEPENDENCY_STEPS,
        CI_OUTPUT_ROUTE_INVARIANTS,
    )
    from app.webrtc_remote_media_attach_autoplay_track_state_resilience_baseline import (
        STAGE28_SUBSTEP_DRAFT,
        STAGE28_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_track_attach_ownership_contract_baseline import (
        REMOTE_STREAMLESS_TRACK_FALLBACK_28_2,
    )
    from app.webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline import (
        AUTOPLAY_BLOCK_RECOVERY_POLICY_28_3,
        PLAY_PROMISE_OUTCOME_TAXONOMY_28_3,
    )
    from app.webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline import (
        REMOTE_TRACK_UI_RUNTIME_BOUNDARIES_28_4,
        TEMPORARY_TERMINAL_SEMANTICS_28_4,
    )
    from app.webrtc_media_element_remount_reattach_recovery_contract_baseline import (
        OLD_ELEMENT_TEARDOWN_POLICY_28_5,
        REATTACH_ABORT_CLASSIFICATION_28_5,
    )
    from tools.run_webrtc_remote_media_resilience_sandbox_smoke import (
        REMOTE_MEDIA_SMOKE_SCENARIO_IDS,
    )

    required_steps = (
        "27.7",
        "28.1",
        "28.2",
        "28.3",
        "28.4",
        "28.5",
        "28.6",
    )
    if CI_REMOTE_MEDIA_DEPENDENCY_STEPS != required_steps:
        errors.append("CI_REMOTE_MEDIA_DEPENDENCY_STEPS must match mandatory dependency closure")

    if tuple(REMOTE_MEDIA_SMOKE_SCENARIO_IDS) != CI_REMOTE_MEDIA_SCENARIO_IDS:
        errors.append("CI_REMOTE_MEDIA_SCENARIO_IDS must match 28.6 smoke scenario IDs")

    if set(CI_REMOTE_MEDIA_REQUIRED_INVARIANTS.keys()) != set(CI_REMOTE_MEDIA_SCENARIO_IDS):
        errors.append("CI_REMOTE_MEDIA_REQUIRED_INVARIANTS must cover all required scenarios")

    required_fields = (
        "scenario_id",
        "executed_at",
        "runtime",
        "browser_engine",
        "track_kind",
        "has_stream",
        "initial_play_outcome",
        "retry_play_outcome",
        "mute_seen",
        "unmute_seen",
        "ended_seen",
        "old_element_torn_down",
        "duplicate_attach_prevented",
        "final_binding_owner_key",
        "result",
        "proof_refs",
        "verified_invariants",
        "notes",
    )
    if CI_REMOTE_MEDIA_EVIDENCE_SCHEMA_REQUIRED_FIELDS != required_fields:
        errors.append("CI_REMOTE_MEDIA_EVIDENCE_SCHEMA_REQUIRED_FIELDS must match canonical schema")

    required_outcomes = (
        "PASS",
        "FAIL",
        "UNSUPPORTED",
    )
    if CI_REMOTE_MEDIA_OUTCOME_MODEL != required_outcomes:
        errors.append("CI_REMOTE_MEDIA_OUTCOME_MODEL must include PASS/FAIL/UNSUPPORTED")

    if len(CI_REMOTE_MEDIA_FAIL_CONDITIONS) < 7:
        errors.append("CI_REMOTE_MEDIA_FAIL_CONDITIONS must include full failure-class baseline")

    required_invariants = {
        "ci_validates_contract_and_evidence_not_full_browser_policy_truth": True,
        "manual_smoke_evidence_required": True,
        "streamless_attach_branch_enforced": True,
        "autoplay_blocked_recovery_branch_enforced": True,
        "temporary_vs_terminal_track_branch_enforced": True,
        "remount_abort_transitional_branch_enforced": True,
        "unsupported_is_explicit_non_pass_outcome": True,
        "fail_closed_behavior_required": True,
        "production_runtime_path_unchanged": True,
    }
    if CI_REMOTE_MEDIA_INVARIANTS != required_invariants:
        errors.append("CI_REMOTE_MEDIA_INVARIANTS must match canonical invariant set")

    required_workflow = {
        "workflow_path": ".github/workflows/webrtc-remote-media-resilience-ci.yml",
        "job_name": "webrtc-remote-media-resilience-gate",
        "runner_script": "server/tools/run_webrtc_remote_media_resilience_ci_gate.py",
    }
    if WORKFLOW_BASELINE_28_7 != required_workflow:
        errors.append("WORKFLOW_BASELINE_28_7 must match workflow baseline")

    if STAGE28_SUBSTEP_DRAFT.get("28.7") != "remote_media_resilience_ci_gate_baseline":
        errors.append("Stage 28 draft must keep 28.7 CI gate milestone")

    if STAGE28_VERIFICATION_TYPES.get("28.7") != "build check":
        errors.append("Stage 28 verification map must keep 28.7 as build check")

    if "27.6" not in CI_OUTPUT_ROUTE_DEPENDENCY_STEPS:
        errors.append("27.7 dependency closure must include 27.6 manual smoke")

    if CI_OUTPUT_ROUTE_INVARIANTS.get("fail_closed_behavior_required") is not True:
        errors.append("27.7 invariants must keep fail_closed behavior")

    if REMOTE_STREAMLESS_TRACK_FALLBACK_28_2.get("streamless_branch_required") is not True:
        errors.append("28.2 streamless fallback must remain required")

    if PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get("NotAllowedError") != "blocked_requires_user_gesture":
        errors.append("28.3 taxonomy must keep NotAllowedError blocked branch")

    if AUTOPLAY_BLOCK_RECOVERY_POLICY_28_3.get("retry_requires_explicit_user_action") is not True:
        errors.append("28.3 policy must keep explicit user action recovery")

    if TEMPORARY_TERMINAL_SEMANTICS_28_4.get("mute_is_temporary") is not True:
        errors.append("28.4 semantics must keep mute temporary")

    if TEMPORARY_TERMINAL_SEMANTICS_28_4.get("ended_is_terminal") is not True:
        errors.append("28.4 semantics must keep ended terminal")

    if REMOTE_TRACK_UI_RUNTIME_BOUNDARIES_28_4.get("mute_preserves_binding") is not True:
        errors.append("28.4 boundaries must keep binding on mute")

    if (
        OLD_ELEMENT_TEARDOWN_POLICY_28_5.get("teardown_required_for_potentially_playing_detached_element")
        is not True
    ):
        errors.append("28.5 teardown policy must require explicit old-element teardown")

    if REATTACH_ABORT_CLASSIFICATION_28_5.get("abort_error_branch") != "reattach_replay_interrupted":
        errors.append("28.5 classification must keep AbortError transitional branch")

    return errors

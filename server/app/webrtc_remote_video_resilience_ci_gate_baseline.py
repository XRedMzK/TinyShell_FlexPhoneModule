from __future__ import annotations


CI_REMOTE_VIDEO_SCENARIO_IDS = (
    "A_cold_attach_happy_path",
    "B_metadata_without_first_frame_false_positive_guard",
    "C_waiting_resume_grace_then_progress",
    "D_stalled_fetch_starvation_branch",
    "E_intrinsic_dimension_update_no_failure_reattach",
    "F_remount_reattach_continuity",
    "G_rvfc_unavailable_quality_fallback",
    "H_playing_without_real_frames_non_success_guard",
)

CI_REMOTE_VIDEO_DEPENDENCY_STEPS = (
    "28.7",
    "29.1",
    "29.2",
    "29.3",
    "29.4",
    "29.5",
    "29.6",
)

CI_REMOTE_VIDEO_REQUIRED_INVARIANTS = {
    "A_cold_attach_happy_path": (
        "first_frame_proven_after_loadeddata",
        "progress_observed_after_playing",
    ),
    "B_metadata_without_first_frame_false_positive_guard": (
        "metadata_only_not_first_frame_ready",
        "no_false_ready_classification",
    ),
    "C_waiting_resume_grace_then_progress": (
        "waiting_starvation_non_terminal",
        "resume_grace_before_progress_reproof",
        "post_resume_progress_observed",
    ),
    "D_stalled_fetch_starvation_branch": (
        "stalled_fetch_starvation_branch",
        "non_terminal_starvation_context",
    ),
    "E_intrinsic_dimension_update_no_failure_reattach": (
        "videoWidth_videoHeight_intrinsic_truth",
        "resize_reconciles_dimensions",
        "dimension_change_not_reattach_failure",
    ),
    "F_remount_reattach_continuity": (
        "legitimate_remount_detected",
        "old_element_teardown_required",
        "dimension_and_progress_truth_continuity",
    ),
    "G_rvfc_unavailable_quality_fallback": (
        "rvfc_unavailable_fallback_supported",
        "quality_delta_progress_observed",
    ),
    "H_playing_without_real_frames_non_success_guard": (
        "no_early_progress_success",
        "resume_grace_or_unproven_branch_preserved",
    ),
}

CI_REMOTE_VIDEO_EVIDENCE_SCHEMA_REQUIRED_FIELDS = (
    "scenario_id",
    "runtime",
    "browser_engine",
    "result",
    "proof_refs",
    "verified_invariants",
)

CI_REMOTE_VIDEO_OUTCOME_MODEL = (
    "PASS",
    "FAIL",
    "UNSUPPORTED",
)

CI_REMOTE_VIDEO_FAIL_CONDITIONS = (
    "dependency_checker_missing_or_failed",
    "baseline_artifact_missing",
    "smoke_evidence_manifest_missing",
    "required_scenario_missing",
    "required_invariant_marker_missing",
    "unsupported_treated_as_pass",
    "compile_or_import_failure",
)

CI_REMOTE_VIDEO_INVARIANTS = {
    "ci_validates_contract_and_evidence_not_full_webview_truth": True,
    "manual_smoke_evidence_required": True,
    "first_frame_false_positive_guard_enforced": True,
    "starvation_resume_grace_enforced": True,
    "dimension_non_failure_boundary_enforced": True,
    "rvfc_fallback_branch_enforced": True,
    "unsupported_is_explicit_non_pass_outcome": True,
    "fail_closed_behavior_required": True,
    "production_runtime_path_unchanged": True,
}

WORKFLOW_BASELINE_29_7 = {
    "workflow_path": ".github/workflows/webrtc-remote-video-resilience-ci.yml",
    "job_name": "webrtc-remote-video-resilience-gate",
    "runner_script": "server/tools/run_webrtc_remote_video_resilience_ci_gate.py",
}


def validate_webrtc_remote_video_resilience_ci_gate_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_media_resilience_ci_gate_baseline import (
        CI_REMOTE_MEDIA_DEPENDENCY_STEPS,
        CI_REMOTE_MEDIA_INVARIANTS,
    )
    from app.webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline import (
        STAGE29_SUBSTEP_DRAFT,
        STAGE29_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_video_first_frame_readiness_contract_baseline import (
        FIRST_FRAME_INVARIANTS_29_2,
    )
    from app.webrtc_frame_progress_freeze_detection_observability_contract_baseline import (
        FRAME_PROGRESS_INVARIANTS_29_3,
    )
    from app.webrtc_waiting_stalled_resume_recovery_contract_baseline import (
        WAITING_STALLED_INVARIANTS_29_4,
    )
    from app.webrtc_dimension_resize_reconciliation_contract_baseline import (
        DIMENSION_INVARIANTS_29_5,
    )
    from tools.run_webrtc_remote_video_resilience_sandbox_smoke import (
        REMOTE_VIDEO_SMOKE_SCENARIO_IDS,
    )

    required_steps = (
        "28.7",
        "29.1",
        "29.2",
        "29.3",
        "29.4",
        "29.5",
        "29.6",
    )
    if CI_REMOTE_VIDEO_DEPENDENCY_STEPS != required_steps:
        errors.append("CI_REMOTE_VIDEO_DEPENDENCY_STEPS must match mandatory dependency closure")

    if tuple(REMOTE_VIDEO_SMOKE_SCENARIO_IDS) != CI_REMOTE_VIDEO_SCENARIO_IDS:
        errors.append("CI_REMOTE_VIDEO_SCENARIO_IDS must match 29.6 smoke scenario IDs")

    if set(CI_REMOTE_VIDEO_REQUIRED_INVARIANTS.keys()) != set(CI_REMOTE_VIDEO_SCENARIO_IDS):
        errors.append("CI_REMOTE_VIDEO_REQUIRED_INVARIANTS must cover all required scenarios")

    required_fields = (
        "scenario_id",
        "runtime",
        "browser_engine",
        "result",
        "proof_refs",
        "verified_invariants",
    )
    if CI_REMOTE_VIDEO_EVIDENCE_SCHEMA_REQUIRED_FIELDS != required_fields:
        errors.append("CI_REMOTE_VIDEO_EVIDENCE_SCHEMA_REQUIRED_FIELDS must match canonical schema")

    required_outcomes = (
        "PASS",
        "FAIL",
        "UNSUPPORTED",
    )
    if CI_REMOTE_VIDEO_OUTCOME_MODEL != required_outcomes:
        errors.append("CI_REMOTE_VIDEO_OUTCOME_MODEL must include PASS/FAIL/UNSUPPORTED")

    if len(CI_REMOTE_VIDEO_FAIL_CONDITIONS) < 7:
        errors.append("CI_REMOTE_VIDEO_FAIL_CONDITIONS must include full failure-class baseline")

    required_invariants = {
        "ci_validates_contract_and_evidence_not_full_webview_truth": True,
        "manual_smoke_evidence_required": True,
        "first_frame_false_positive_guard_enforced": True,
        "starvation_resume_grace_enforced": True,
        "dimension_non_failure_boundary_enforced": True,
        "rvfc_fallback_branch_enforced": True,
        "unsupported_is_explicit_non_pass_outcome": True,
        "fail_closed_behavior_required": True,
        "production_runtime_path_unchanged": True,
    }
    if CI_REMOTE_VIDEO_INVARIANTS != required_invariants:
        errors.append("CI_REMOTE_VIDEO_INVARIANTS must match canonical invariant set")

    required_workflow = {
        "workflow_path": ".github/workflows/webrtc-remote-video-resilience-ci.yml",
        "job_name": "webrtc-remote-video-resilience-gate",
        "runner_script": "server/tools/run_webrtc_remote_video_resilience_ci_gate.py",
    }
    if WORKFLOW_BASELINE_29_7 != required_workflow:
        errors.append("WORKFLOW_BASELINE_29_7 must match workflow baseline")

    if STAGE29_SUBSTEP_DRAFT.get("29.7") != "remote_video_resilience_ci_gate_baseline":
        errors.append("Stage 29 draft must keep 29.7 CI gate milestone")

    if STAGE29_VERIFICATION_TYPES.get("29.7") != "build check":
        errors.append("Stage 29 verification map must keep 29.7 as build check")

    if "28.6" not in CI_REMOTE_MEDIA_DEPENDENCY_STEPS:
        errors.append("28.7 dependency closure must include 28.6 manual smoke")

    if CI_REMOTE_MEDIA_INVARIANTS.get("fail_closed_behavior_required") is not True:
        errors.append("28.7 invariants must keep fail_closed behavior")

    if FIRST_FRAME_INVARIANTS_29_2.get("loadedmetadata_not_first_frame_proof") is not True:
        errors.append("29.2 invariants must keep metadata-not-first-frame-proof guard")

    if FRAME_PROGRESS_INVARIANTS_29_3.get("rvfc_primary_with_fallback_quality_branch") is not True:
        errors.append("29.3 invariants must keep rvfc primary with fallback branch")

    if WAITING_STALLED_INVARIANTS_29_4.get("resume_grace_before_freeze_recheck_required") is not True:
        errors.append("29.4 invariants must keep resume-grace boundary")

    if DIMENSION_INVARIANTS_29_5.get("dimension_change_not_reattach_trigger") is not True:
        errors.append("29.5 invariants must keep dimension change non-reattach boundary")

    return errors

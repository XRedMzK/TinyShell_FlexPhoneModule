from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.webrtc_remote_video_first_frame_readiness_contract_baseline import (
    FIRST_FRAME_INVARIANTS_29_2,
    FIRST_FRAME_READINESS_SURFACES_29_2,
    classify_first_frame_state,
    is_first_frame_proven,
)
from app.webrtc_frame_progress_freeze_detection_observability_contract_baseline import (
    FRAME_PROGRESS_INVARIANTS_29_3,
    FRAME_PROGRESS_SURFACES_29_3,
    FREEZE_GRACE_WINDOW_POLICY_29_3,
    classify_frame_progress_state,
    has_quality_progress,
    has_rvfc_progress,
    is_progress_source_supported,
)
from app.webrtc_waiting_stalled_resume_recovery_contract_baseline import (
    WAITING_STALLED_INVARIANTS_29_4,
    WAITING_STALLED_RECOVERY_SURFACES_29_4,
    classify_waiting_stalled_resume_state,
)
from app.webrtc_dimension_resize_reconciliation_contract_baseline import (
    DIMENSION_INVARIANTS_29_5,
    DIMENSION_RECONCILIATION_SURFACES_29_5,
    classify_dimension_reconciliation_state,
    is_intrinsic_dimension_known,
    requires_reattach_on_dimension_change,
)
from app.webrtc_media_element_remount_reattach_recovery_contract_baseline import (
    is_legitimate_remount_reattach,
    requires_old_element_teardown,
)


class RemoteVideoSmokeError(RuntimeError):
    pass


REMOTE_VIDEO_SMOKE_SCENARIO_IDS = (
    "A_cold_attach_happy_path",
    "B_metadata_without_first_frame_false_positive_guard",
    "C_waiting_resume_grace_then_progress",
    "D_stalled_fetch_starvation_branch",
    "E_intrinsic_dimension_update_no_failure_reattach",
    "F_remount_reattach_continuity",
    "G_rvfc_unavailable_quality_fallback",
    "H_playing_without_real_frames_non_success_guard",
)

REMOTE_VIDEO_SMOKE_SUCCESS_MARKER = "WebRTC remote video resilience sandbox smoke: OK"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RemoteVideoSmokeError(message)


def _scenario_a_cold_attach_happy_path() -> dict[str, Any]:
    first_frame_proven = is_first_frame_proven(
        loadeddata_seen=True,
        ready_state=2,
        fallback_enabled=True,
    )
    first_frame_state = classify_first_frame_state(
        metadata_seen=True,
        play_seen=True,
        playing_seen=True,
        first_frame_proven=first_frame_proven,
    )

    rvfc_progress = has_rvfc_progress(10, 11)
    progress_state = classify_frame_progress_state(
        progress_observed=rvfc_progress,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=False,
        supported=True,
    )

    _require(first_frame_proven is True, "Scenario A must prove first frame")
    _require(
        first_frame_state == "playback_started_frame_progress_pending",
        "Scenario A first-frame state mismatch",
    )
    _require(progress_state == "progress_observed", "Scenario A progress state mismatch")

    return {
        "scenario_id": "A_cold_attach_happy_path",
        "trigger": "loadedmetadata_loadeddata_playing_with_progress",
        "authoritative_surfaces": [
            "HTMLMediaElement.loadedmetadata",
            "HTMLMediaElement.loadeddata",
            "HTMLMediaElement.playing",
            "requestVideoFrameCallback",
        ],
        "deterministic_actions": [
            "first_frame_proven",
            "progress_observed",
        ],
        "expected_state_assertions": [
            "playback_started_frame_progress_pending",
            "progress_observed",
        ],
        "status": "PASS",
    }


def _scenario_b_metadata_without_first_frame_false_positive_guard() -> dict[str, Any]:
    first_frame_proven = is_first_frame_proven(
        loadeddata_seen=False,
        ready_state=1,
        fallback_enabled=False,
    )
    first_frame_state = classify_first_frame_state(
        metadata_seen=True,
        play_seen=True,
        playing_seen=False,
        first_frame_proven=first_frame_proven,
    )

    _require(first_frame_proven is False, "Scenario B must keep first frame unproven")
    _require(
        first_frame_state == "play_requested_first_frame_pending",
        "Scenario B must stay in first-frame-pending branch",
    )

    return {
        "scenario_id": "B_metadata_without_first_frame_false_positive_guard",
        "trigger": "loadedmetadata_without_loadeddata",
        "authoritative_surfaces": [
            "HTMLMediaElement.loadedmetadata",
            "HTMLMediaElement.loadeddata",
            "HTMLMediaElement.readyState",
        ],
        "deterministic_actions": [
            "guard_against_metadata_only_readiness",
        ],
        "expected_state_assertions": [
            "first_frame_unproven",
            "no_false_ready",
        ],
        "status": "PASS",
    }


def _scenario_c_waiting_resume_grace_then_progress() -> dict[str, Any]:
    waiting_state = classify_waiting_stalled_resume_state(
        waiting_seen=True,
        stalled_seen=False,
        playing_seen=False,
        in_grace_window=False,
        terminal=False,
    )
    resume_state = classify_waiting_stalled_resume_state(
        waiting_seen=True,
        stalled_seen=False,
        playing_seen=True,
        in_grace_window=True,
        terminal=False,
    )
    progress_during_grace = classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=True,
        supported=True,
    )
    progress_after_resume = classify_frame_progress_state(
        progress_observed=has_rvfc_progress(50, 52),
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=False,
        supported=True,
    )

    _require(waiting_state == "starvation_waiting", "Scenario C waiting branch mismatch")
    _require(resume_state == "resume_grace", "Scenario C resume-grace branch mismatch")
    _require(progress_during_grace == "resume_grace", "Scenario C grace progress classification mismatch")
    _require(progress_after_resume == "progress_observed", "Scenario C post-resume progress mismatch")

    return {
        "scenario_id": "C_waiting_resume_grace_then_progress",
        "trigger": "waiting_to_playing_resume_with_grace",
        "authoritative_surfaces": [
            "HTMLMediaElement.waiting",
            "HTMLMediaElement.playing",
            "requestVideoFrameCallback",
        ],
        "deterministic_actions": [
            "waiting_starvation_classified",
            "resume_grace_applied",
            "progress_recovered_after_grace",
        ],
        "expected_state_assertions": [
            "starvation_waiting",
            "resume_grace",
            "progress_observed",
        ],
        "status": "PASS",
    }


def _scenario_d_stalled_fetch_starvation_branch() -> dict[str, Any]:
    stalled_state = classify_waiting_stalled_resume_state(
        waiting_seen=False,
        stalled_seen=True,
        playing_seen=False,
        in_grace_window=False,
        terminal=False,
    )
    progress_state = classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=True,
        starvation_context=True,
        in_grace_window=False,
        supported=True,
    )

    _require(stalled_state == "starvation_stalled", "Scenario D stalled branch mismatch")
    _require(progress_state == "starvation_context", "Scenario D progress context mismatch")

    return {
        "scenario_id": "D_stalled_fetch_starvation_branch",
        "trigger": "stalled_event_without_terminal_end",
        "authoritative_surfaces": [
            "HTMLMediaElement.stalled",
            "frame_progress_context_classifier",
        ],
        "deterministic_actions": [
            "stalled_classified_as_fetch_starvation",
            "non_terminal_starvation_context_preserved",
        ],
        "expected_state_assertions": [
            "starvation_stalled",
            "starvation_context",
        ],
        "status": "PASS",
    }


def _scenario_e_intrinsic_dimension_update_no_failure_reattach() -> dict[str, Any]:
    initial_state = classify_dimension_reconciliation_state(
        metadata_seen=True,
        resize_seen=False,
        video_width=1280,
        video_height=720,
        ready_state=1,
        reconciled=False,
        terminal=False,
    )
    update_state = classify_dimension_reconciliation_state(
        metadata_seen=True,
        resize_seen=True,
        video_width=1920,
        video_height=1080,
        ready_state=4,
        reconciled=True,
        terminal=False,
    )
    known_after_resize = is_intrinsic_dimension_known(1920, 1080, 4)
    reattach_required = requires_reattach_on_dimension_change(dimension_changed=True, terminal=False)

    _require(initial_state == "dimension_initial_proven", "Scenario E initial dimension state mismatch")
    _require(update_state == "dimension_reconciled", "Scenario E reconciled dimension state mismatch")
    _require(known_after_resize is True, "Scenario E intrinsic dimensions must be known")
    _require(reattach_required is False, "Scenario E must not require reattach for non-terminal resize")

    return {
        "scenario_id": "E_intrinsic_dimension_update_no_failure_reattach",
        "trigger": "resize_updates_intrinsic_dimensions",
        "authoritative_surfaces": [
            "HTMLVideoElement.videoWidth",
            "HTMLVideoElement.videoHeight",
            "HTMLVideoElement.resize",
        ],
        "deterministic_actions": [
            "dimension_initial_proven",
            "dimension_reconciled_on_resize",
            "no_reattach_on_dimension_change",
        ],
        "expected_state_assertions": [
            "dimension_reconciled",
            "non_failure_non_reattach",
        ],
        "status": "PASS",
    }


def _scenario_f_remount_reattach_continuity() -> dict[str, Any]:
    legitimate_remount = is_legitimate_remount_reattach(same_owner_key=True, element_instance_changed=True)
    old_teardown_required = requires_old_element_teardown(
        old_element_exists=True,
        old_element_potentially_playing=True,
    )
    dimension_state_after_remount = classify_dimension_reconciliation_state(
        metadata_seen=True,
        resize_seen=True,
        video_width=1280,
        video_height=720,
        ready_state=4,
        reconciled=True,
        terminal=False,
    )
    progress_state_after_remount = classify_frame_progress_state(
        progress_observed=True,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=False,
        supported=True,
    )

    _require(legitimate_remount is True, "Scenario F remount must be classified as legitimate reattach")
    _require(old_teardown_required is True, "Scenario F must require old-element teardown")
    _require(
        dimension_state_after_remount == "dimension_reconciled",
        "Scenario F dimension continuity mismatch after remount",
    )
    _require(progress_state_after_remount == "progress_observed", "Scenario F progress continuity mismatch")

    return {
        "scenario_id": "F_remount_reattach_continuity",
        "trigger": "element_remount_with_existing_owner_binding",
        "authoritative_surfaces": [
            "remount_reattach_guard",
            "dimension_reconciliation_state",
            "frame_progress_state",
        ],
        "deterministic_actions": [
            "legitimate_remount_detected",
            "old_element_teardown_required",
            "dimension_and_progress_truth_preserved",
        ],
        "expected_state_assertions": [
            "dimension_reconciled",
            "progress_observed",
        ],
        "status": "PASS",
    }


def _scenario_g_rvfc_unavailable_quality_fallback() -> dict[str, Any]:
    supported = is_progress_source_supported(rvfc_supported=False, playback_quality_supported=True)
    quality_progress = has_quality_progress(100, 103)
    progress_state = classify_frame_progress_state(
        progress_observed=quality_progress,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=False,
        supported=supported,
    )

    _require(supported is True, "Scenario G must keep progress support through fallback branch")
    _require(quality_progress is True, "Scenario G fallback must detect quality progress deltas")
    _require(progress_state == "progress_observed", "Scenario G fallback progress classification mismatch")

    return {
        "scenario_id": "G_rvfc_unavailable_quality_fallback",
        "trigger": "rvfc_not_supported_quality_supported",
        "authoritative_surfaces": [
            "HTMLVideoElement.getVideoPlaybackQuality",
            "frame_progress_fallback_classifier",
        ],
        "deterministic_actions": [
            "fallback_progress_branch_entered",
            "quality_delta_progress_observed",
        ],
        "expected_state_assertions": [
            "fallback_branch_supported",
            "progress_observed",
        ],
        "status": "PASS",
    }


def _scenario_h_playing_without_real_frames_non_success_guard() -> dict[str, Any]:
    no_progress_grace_state = classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=True,
        starvation_context=False,
        in_grace_window=True,
        supported=True,
    )
    no_progress_unproven_state = classify_frame_progress_state(
        progress_observed=False,
        active_playback_context=False,
        starvation_context=False,
        in_grace_window=False,
        supported=True,
    )

    _require(
        no_progress_grace_state in {"resume_grace", "progress_unproven"},
        "Scenario H must not classify no-progress grace branch as success",
    )
    _require(
        no_progress_unproven_state == "progress_unproven",
        "Scenario H no-context no-progress must remain unproven",
    )

    return {
        "scenario_id": "H_playing_without_real_frames_non_success_guard",
        "trigger": "playing_without_progress_deltas",
        "authoritative_surfaces": [
            "frame_progress_classifier",
            "resume_grace_policy",
        ],
        "deterministic_actions": [
            "no_early_progress_success",
            "non_success_guard_preserved",
        ],
        "expected_state_assertions": [
            "resume_grace_or_unproven_before_freeze_recheck",
            "no_false_progress_success",
        ],
        "status": "PASS",
    }


def run_remote_video_resilience_sandbox_smoke() -> dict[str, Any]:
    required_checks = {
        "metadata_surface": FIRST_FRAME_READINESS_SURFACES_29_2["metadata_surface"]
        == "HTMLMediaElement.loadedmetadata",
        "first_frame_guard": FIRST_FRAME_INVARIANTS_29_2["loadedmetadata_not_first_frame_proof"] is True,
        "rvfc_primary_surface": FRAME_PROGRESS_SURFACES_29_3["primary_progress_surface"]
        == "HTMLVideoElement.requestVideoFrameCallback",
        "fallback_surface": FRAME_PROGRESS_SURFACES_29_3["fallback_progress_surface"]
        == "HTMLVideoElement.getVideoPlaybackQuality",
        "resume_grace_required": FREEZE_GRACE_WINDOW_POLICY_29_3["grace_after_waiting_stalled_resume_required"]
        is True,
        "waiting_surface": WAITING_STALLED_RECOVERY_SURFACES_29_4["waiting_surface"]
        == "HTMLMediaElement.waiting",
        "stalled_surface": WAITING_STALLED_RECOVERY_SURFACES_29_4["stalled_surface"]
        == "HTMLMediaElement.stalled",
        "waiting_non_terminal": WAITING_STALLED_INVARIANTS_29_4["waiting_stalled_non_terminal_by_default"] is True,
        "dimension_intrinsic_truth": DIMENSION_INVARIANTS_29_5["intrinsic_dimensions_canonical_truth"] is True,
        "dimension_non_failure": DIMENSION_INVARIANTS_29_5["dimension_change_not_failure_branch"] is True,
        "dimension_resize_surface": DIMENSION_RECONCILIATION_SURFACES_29_5["dimension_update_event"]
        == "HTMLVideoElement.resize",
        "playing_not_progress_truth": FRAME_PROGRESS_INVARIANTS_29_3["playing_not_progress_truth"] is True,
    }

    if not all(required_checks.values()):
        failed = [key for key, ok in required_checks.items() if not ok]
        raise RemoteVideoSmokeError(f"Contract dependency precheck failed: {', '.join(failed)}")

    scenarios = [
        _scenario_a_cold_attach_happy_path(),
        _scenario_b_metadata_without_first_frame_false_positive_guard(),
        _scenario_c_waiting_resume_grace_then_progress(),
        _scenario_d_stalled_fetch_starvation_branch(),
        _scenario_e_intrinsic_dimension_update_no_failure_reattach(),
        _scenario_f_remount_reattach_continuity(),
        _scenario_g_rvfc_unavailable_quality_fallback(),
        _scenario_h_playing_without_real_frames_non_success_guard(),
    ]

    statuses = [scenario["status"] for scenario in scenarios]
    if any(status != "PASS" for status in statuses):
        raise RemoteVideoSmokeError("One or more remote-video resilience smoke scenarios failed")

    return {
        "overall_status": "PASS",
        "scenarios_total": len(scenarios),
        "scenarios_passed": len([scenario for scenario in scenarios if scenario["status"] == "PASS"]),
        "scenario_ids": REMOTE_VIDEO_SMOKE_SCENARIO_IDS,
        "first_frame_false_positive_guard_enforced": True,
        "resume_grace_before_freeze_recheck_enforced": True,
        "dimension_non_failure_boundary_enforced": True,
        "fallback_progress_branch_enforced": True,
        "scenarios": scenarios,
    }


def main() -> int:
    try:
        proof = run_remote_video_resilience_sandbox_smoke()
        print(json.dumps(proof, indent=2, sort_keys=True))
        print(REMOTE_VIDEO_SMOKE_SUCCESS_MARKER)
        return 0
    except Exception as exc:  # pragma: no cover - smoke entrypoint
        print(f"WebRTC remote video resilience sandbox smoke: FAILED: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

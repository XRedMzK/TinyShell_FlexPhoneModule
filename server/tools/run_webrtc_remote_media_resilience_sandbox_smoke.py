from __future__ import annotations

import json
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.webrtc_remote_media_attach_autoplay_track_state_resilience_baseline import (
    AUTOPLAY_PLAY_PROMISE_MODEL,
    REMOTE_MEDIA_SURFACES,
    REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL,
    REMOTE_TRACK_STATE_RESILIENCE_MODEL,
)
from app.webrtc_remote_track_attach_ownership_contract_baseline import (
    REMOTE_DUPLICATE_ATTACH_GUARD_28_2,
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
    DUPLICATE_VS_LEGITIMATE_REATTACH_GUARD_28_5,
    OLD_ELEMENT_TEARDOWN_POLICY_28_5,
    REATTACH_ABORT_CLASSIFICATION_28_5,
    REPLAY_SAFE_REATTACH_SEQUENCE_28_5,
    REMOUNT_DETECTION_TRANSFER_MODEL_28_5,
)


class RemoteMediaSmokeError(RuntimeError):
    pass


REMOTE_MEDIA_SMOKE_SCENARIO_IDS = (
    "A_clean_remote_attach",
    "B_streamless_remote_attach",
    "C_autoplay_blocked_user_gesture_recovery",
    "D_temporary_interruption_mute_unmute",
    "E_terminal_track_end",
    "F_remount_reattach_abort_safe_replay",
)

REMOTE_MEDIA_SMOKE_SUCCESS_MARKER = "WebRTC remote media resilience sandbox smoke: OK"


@dataclass
class RemoteMediaSandboxSession:
    owner_key: str
    current_element_key: str = "element-1"
    stream_binding_kind: str = "none"
    attached: bool = False
    playback_state: str = "unattached"
    track_runtime_state: str = "track_live_flowing"
    track_ready_state: str = "live"
    duplicate_attach_prevented: bool = False
    old_element_torn_down: bool = False
    reattach_revision: int = 0
    last_play_error: str | None = None
    operations: list[str] = field(default_factory=list)

    def ontrack_attach(self, *, has_stream: bool) -> None:
        if self.attached:
            self.duplicate_attach_prevented = True
            self.operations.append("duplicate_attach_noop")
            return

        self.stream_binding_kind = "canonical_stream" if has_stream else "synthetic_stream"
        self.attached = True
        self.playback_state = "attached_pending_playback"
        self.operations.append(f"attach_{self.stream_binding_kind}")

    def attempt_play(self, outcome: str) -> None:
        if not self.attached:
            raise RemoteMediaSmokeError("attempt_play called before attach")

        self.playback_state = "play_attempt_inflight"
        self.operations.append(f"play_attempt_{outcome}")

        if outcome == "resolved":
            self.playback_state = PLAY_PROMISE_OUTCOME_TAXONOMY_28_3["resolved"]
            self.last_play_error = None
            return

        mapped = PLAY_PROMISE_OUTCOME_TAXONOMY_28_3.get(outcome)
        if mapped is None:
            mapped = PLAY_PROMISE_OUTCOME_TAXONOMY_28_3["other_rejection"]

        self.playback_state = mapped
        self.last_play_error = outcome

    def emit_track_event(self, event_name: str) -> None:
        if event_name == "mute":
            self.track_runtime_state = "track_live_temporarily_muted"
            self.operations.append("track_mute")
            return

        if event_name == "unmute":
            self.track_runtime_state = "track_live_flowing"
            self.operations.append("track_unmute")
            return

        if event_name == "ended":
            self.track_runtime_state = "track_ended_terminal"
            self.track_ready_state = "ended"
            self.operations.append("track_ended")
            return

        raise RemoteMediaSmokeError(f"Unsupported track event: {event_name}")

    def remount_and_reattach(self, *, new_element_key: str, first_play_outcome: str) -> None:
        if new_element_key == self.current_element_key:
            self.duplicate_attach_prevented = True
            self.operations.append("remount_same_element_noop")
            return

        self.old_element_torn_down = True
        self.current_element_key = new_element_key
        self.reattach_revision += 1
        self.playback_state = "reattach_pending"
        self.operations.append("old_element_teardown")
        self.operations.append("remount_reattach_pending")

        self.attempt_play(first_play_outcome)
        if first_play_outcome == "AbortError":
            self.playback_state = "reattach_replay_interrupted"
            self.operations.append("reattach_replay_interrupted")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RemoteMediaSmokeError(message)


def _scenario_a_clean_remote_attach() -> dict[str, Any]:
    session = RemoteMediaSandboxSession(owner_key="receiver-1/transceiver-1")
    session.ontrack_attach(has_stream=True)
    session.attempt_play("resolved")

    _require(session.attached is True, "Scenario A attach must complete")
    _require(session.stream_binding_kind == "canonical_stream", "Scenario A must bind canonical stream")
    _require(session.playback_state == "playing", "Scenario A play result mismatch")

    return {
        "scenario_id": "A_clean_remote_attach",
        "trigger": "ontrack_with_stream",
        "authoritative_surfaces": [
            "RTCPeerConnection.track",
            "HTMLMediaElement.srcObject",
            "HTMLMediaElement.play",
        ],
        "deterministic_actions": [
            "attach_canonical_stream",
            "play_resolved_to_playing",
        ],
        "expected_state_assertions": [
            "attached_true",
            "playback_state_playing",
        ],
        "status": "PASS",
    }


def _scenario_b_streamless_remote_attach() -> dict[str, Any]:
    session = RemoteMediaSandboxSession(owner_key="receiver-2/transceiver-2")
    session.ontrack_attach(has_stream=False)
    session.ontrack_attach(has_stream=False)
    session.attempt_play("resolved")

    _require(session.stream_binding_kind == "synthetic_stream", "Scenario B must use streamless synthetic binding")
    _require(session.duplicate_attach_prevented is True, "Scenario B duplicate attach guard must trigger")
    _require(session.playback_state == "playing", "Scenario B play result mismatch")

    return {
        "scenario_id": "B_streamless_remote_attach",
        "trigger": "ontrack_with_empty_streams",
        "authoritative_surfaces": [
            "RTCPeerConnection.track",
            "streamless_fallback_binding",
            "HTMLMediaElement.play",
        ],
        "deterministic_actions": [
            "attach_synthetic_stream",
            "duplicate_attach_noop",
            "play_resolved_to_playing",
        ],
        "expected_state_assertions": [
            "streamless_fallback_active",
            "duplicate_attach_prevented",
        ],
        "status": "PASS",
    }


def _scenario_c_autoplay_blocked_user_gesture_recovery() -> dict[str, Any]:
    session = RemoteMediaSandboxSession(owner_key="receiver-3/transceiver-3")
    session.ontrack_attach(has_stream=True)
    session.attempt_play("NotAllowedError")

    _require(
        session.playback_state == "blocked_requires_user_gesture",
        "Scenario C initial play must classify as blocked_requires_user_gesture",
    )

    session.attempt_play("resolved")
    _require(session.playback_state == "playing", "Scenario C user-gesture retry must recover to playing")

    return {
        "scenario_id": "C_autoplay_blocked_user_gesture_recovery",
        "trigger": "autoplay_policy_block_then_explicit_retry",
        "authoritative_surfaces": [
            "HTMLMediaElement.play",
            "play_promise_outcome",
        ],
        "deterministic_actions": [
            "play_rejected_notallowed",
            "explicit_retry_play_resolved",
        ],
        "expected_state_assertions": [
            "blocked_branch_entered",
            "user_gesture_recovery_to_playing",
        ],
        "status": "PASS",
    }


def _scenario_d_temporary_interruption_mute_unmute() -> dict[str, Any]:
    session = RemoteMediaSandboxSession(owner_key="receiver-4/transceiver-4")
    session.ontrack_attach(has_stream=True)
    session.attempt_play("resolved")
    before_element = session.current_element_key

    session.emit_track_event("mute")
    _require(
        session.track_runtime_state == "track_live_temporarily_muted",
        "Scenario D mute must map to temporary muted branch",
    )
    _require(session.current_element_key == before_element, "Scenario D mute must preserve binding target")

    session.emit_track_event("unmute")
    _require(session.track_runtime_state == "track_live_flowing", "Scenario D unmute must restore flowing branch")
    _require(session.current_element_key == before_element, "Scenario D unmute must preserve binding target")

    return {
        "scenario_id": "D_temporary_interruption_mute_unmute",
        "trigger": "remote_track_mute_then_unmute",
        "authoritative_surfaces": [
            "MediaStreamTrack.mute",
            "MediaStreamTrack.unmute",
            "binding_state",
        ],
        "deterministic_actions": [
            "mute_to_temporary_branch",
            "unmute_to_flowing_branch",
            "preserve_binding_across_temporary_interruptions",
        ],
        "expected_state_assertions": [
            "no_terminal_transition_on_mute",
            "no_reattach_required_for_unmute",
        ],
        "status": "PASS",
    }


def _scenario_e_terminal_track_end() -> dict[str, Any]:
    session = RemoteMediaSandboxSession(owner_key="receiver-5/transceiver-5")
    session.ontrack_attach(has_stream=True)
    session.attempt_play("resolved")

    session.emit_track_event("ended")

    _require(session.track_runtime_state == "track_ended_terminal", "Scenario E ended must map to terminal state")
    _require(session.track_ready_state == "ended", "Scenario E readyState must be ended")

    return {
        "scenario_id": "E_terminal_track_end",
        "trigger": "remote_track_ended",
        "authoritative_surfaces": [
            "MediaStreamTrack.ended",
            "MediaStreamTrack.readyState",
        ],
        "deterministic_actions": [
            "ended_to_terminal_branch",
        ],
        "expected_state_assertions": [
            "terminal_state_reached",
            "no_in_place_auto_recovery",
        ],
        "status": "PASS",
    }


def _scenario_f_remount_reattach_abort_safe_replay() -> dict[str, Any]:
    session = RemoteMediaSandboxSession(owner_key="receiver-6/transceiver-6")
    session.ontrack_attach(has_stream=True)
    session.attempt_play("resolved")

    old_key = session.current_element_key
    session.remount_and_reattach(new_element_key="element-2", first_play_outcome="AbortError")

    _require(session.old_element_torn_down is True, "Scenario F must teardown old element explicitly")
    _require(session.current_element_key != old_key, "Scenario F must bind to new element instance")
    _require(
        session.playback_state == "reattach_replay_interrupted",
        "Scenario F AbortError must map to transitional reattach interruption",
    )

    session.attempt_play("resolved")
    _require(session.playback_state == "playing", "Scenario F replay retry must recover to playing")

    return {
        "scenario_id": "F_remount_reattach_abort_safe_replay",
        "trigger": "element_remount_during_playback",
        "authoritative_surfaces": [
            "binding_owner_state",
            "HTMLMediaElement.srcObject",
            "HTMLMediaElement.play",
        ],
        "deterministic_actions": [
            "old_element_teardown",
            "new_element_reattach",
            "aborterror_to_transitional_branch",
            "replay_retry_to_playing",
        ],
        "expected_state_assertions": [
            "ownership_preserved_across_remount",
            "old_element_teardown_confirmed",
            "abort_branch_not_source_invalid",
        ],
        "status": "PASS",
    }


def run_remote_media_resilience_sandbox_smoke() -> dict[str, Any]:
    required_checks = {
        "track_surface": REMOTE_MEDIA_SURFACES["track_event_surface"] == "RTCPeerConnection.track",
        "attach_surface": REMOTE_MEDIA_SURFACES["attach_surface"] == "HTMLMediaElement.srcObject",
        "play_surface": REMOTE_MEDIA_SURFACES["playback_start_surface"] == "HTMLMediaElement.play",
        "attach_trigger": REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL["attach_trigger"] == "pc.ontrack",
        "streamless_required": REMOTE_STREAMLESS_TRACK_FALLBACK_28_2["streamless_branch_required"] is True,
        "duplicate_noop": REMOTE_DUPLICATE_ATTACH_GUARD_28_2["duplicate_branch_action"] == "noop",
        "play_notallowed_branch": PLAY_PROMISE_OUTCOME_TAXONOMY_28_3["NotAllowedError"]
        == "blocked_requires_user_gesture",
        "play_notsupported_branch": PLAY_PROMISE_OUTCOME_TAXONOMY_28_3["NotSupportedError"] == "source_invalid",
        "blocked_recovery_explicit_action": AUTOPLAY_BLOCK_RECOVERY_POLICY_28_3[
            "retry_requires_explicit_user_action"
        ]
        is True,
        "autoplay_block_branch_required": AUTOPLAY_PLAY_PROMISE_MODEL["autoplay_block_has_dedicated_branch"]
        is True,
        "mute_non_terminal": TEMPORARY_TERMINAL_SEMANTICS_28_4["mute_is_temporary"] is True,
        "ended_terminal": TEMPORARY_TERMINAL_SEMANTICS_28_4["ended_is_terminal"] is True,
        "mute_preserves_binding": REMOTE_TRACK_UI_RUNTIME_BOUNDARIES_28_4["mute_preserves_binding"] is True,
        "remount_no_new_ontrack_wait": REMOUNT_DETECTION_TRANSFER_MODEL_28_5[
            "remount_waits_for_new_ontrack"
        ]
        is False,
        "old_teardown_required": OLD_ELEMENT_TEARDOWN_POLICY_28_5[
            "teardown_required_for_potentially_playing_detached_element"
        ]
        is True,
        "duplicate_vs_legitimate_guard": DUPLICATE_VS_LEGITIMATE_REATTACH_GUARD_28_5[
            "legitimate_remount_action"
        ]
        == "replay_attach_play_sequence",
        "abort_transitional_branch": REATTACH_ABORT_CLASSIFICATION_28_5[
            "abort_error_branch"
        ]
        == "reattach_replay_interrupted",
        "replay_sequence_starts_with_bind": REPLAY_SAFE_REATTACH_SEQUENCE_28_5["sequence"][0]
        == "bind_new_element_target",
        "track_model_terminal_not_recoverable": REMOTE_TRACK_STATE_RESILIENCE_MODEL[
            "ended_recoverable_with_same_track_object"
        ]
        is False,
    }

    if not all(required_checks.values()):
        failed = [key for key, ok in required_checks.items() if not ok]
        raise RemoteMediaSmokeError(f"Contract dependency precheck failed: {', '.join(failed)}")

    scenarios = [
        _scenario_a_clean_remote_attach(),
        _scenario_b_streamless_remote_attach(),
        _scenario_c_autoplay_blocked_user_gesture_recovery(),
        _scenario_d_temporary_interruption_mute_unmute(),
        _scenario_e_terminal_track_end(),
        _scenario_f_remount_reattach_abort_safe_replay(),
    ]

    statuses = [scenario["status"] for scenario in scenarios]
    if any(status != "PASS" for status in statuses):
        raise RemoteMediaSmokeError("One or more remote-media resilience smoke scenarios failed")

    return {
        "overall_status": "PASS",
        "scenarios_total": len(scenarios),
        "scenarios_passed": len([scenario for scenario in scenarios if scenario["status"] == "PASS"]),
        "scenario_ids": REMOTE_MEDIA_SMOKE_SCENARIO_IDS,
        "autoplay_block_recovery_supported": True,
        "streamless_attach_supported": True,
        "temporary_vs_terminal_track_boundary_enforced": True,
        "remount_abort_transitional_branch_enforced": True,
        "scenarios": scenarios,
    }


def main() -> int:
    try:
        proof = run_remote_media_resilience_sandbox_smoke()
        print(json.dumps(proof, indent=2, sort_keys=True))
        print(REMOTE_MEDIA_SMOKE_SUCCESS_MARKER)
        return 0
    except Exception as exc:  # pragma: no cover - smoke entrypoint
        print(f"WebRTC remote media resilience sandbox smoke: FAILED: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

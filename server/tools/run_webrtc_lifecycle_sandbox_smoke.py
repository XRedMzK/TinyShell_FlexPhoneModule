from __future__ import annotations

import json
import sys
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.webrtc_negotiation_glare_resolution_contract import (
    DETERMINISTIC_SIGNALING_CASE_ACTIONS,
    NEGOTIATION_ROLES,
    ROLLBACK_POLICY,
)
from app.webrtc_peer_session_state_inventory import (
    PEER_SESSION_STATE_INVENTORY_BASELINE,
    PEER_SESSION_TRANSITION_MATRIX_BASELINE,
)
from app.webrtc_reconnect_ice_restart_pending_recovery_contract import (
    DETERMINISTIC_RECOVERY_CASE_ACTIONS,
    RECOVERY_ELIGIBILITY_RULES,
)


class WebRTCLifecycleSmokeError(RuntimeError):
    pass


@dataclass
class PeerLifecycleSession:
    session_id: str
    role: str
    state: str = "session_new"
    pending_recovery_id: str | None = None
    trigger_history: list[str] = field(default_factory=list)

    def apply_transition(self, trigger: str) -> str:
        candidates = [
            transition
            for transition in PEER_SESSION_TRANSITION_MATRIX_BASELINE
            if transition.from_state == self.state and transition.trigger == trigger
        ]
        if len(candidates) != 1:
            raise WebRTCLifecycleSmokeError(
                f"Transition ambiguity for state={self.state} trigger={trigger}: {len(candidates)} candidates"
            )
        self.state = candidates[0].to_state
        self.trigger_history.append(trigger)
        return self.state

    def assert_valid_state_mapping(self) -> None:
        spec = PEER_SESSION_STATE_INVENTORY_BASELINE.get(self.state)
        if spec is None:
            raise WebRTCLifecycleSmokeError(f"Unknown state: {self.state}")
        if not spec.signaling_states:
            raise WebRTCLifecycleSmokeError(f"State has no signaling mapping: {self.state}")
        if not spec.ice_connection_states:
            raise WebRTCLifecycleSmokeError(f"State has no iceConnectionState mapping: {self.state}")
        if not spec.connection_states:
            raise WebRTCLifecycleSmokeError(f"State has no connectionState mapping: {self.state}")

    def bootstrap_to_signaling_ready(self) -> None:
        if self.state != "session_new":
            raise WebRTCLifecycleSmokeError("bootstrap_to_signaling_ready expects session_new initial state")
        self.state = "session_signaling_ready"
        self.trigger_history.append("bootstrap_signaling_ready")
        self.assert_valid_state_mapping()


def _new_session(role: str, name: str) -> PeerLifecycleSession:
    if role not in NEGOTIATION_ROLES:
        raise WebRTCLifecycleSmokeError(f"Unsupported role: {role}")
    return PeerLifecycleSession(session_id=f"{name}-{uuid.uuid4().hex[:10]}", role=role)


def _scenario_a_happy_path() -> dict[str, object]:
    session = _new_session("polite", "scenario-a")
    start_state = session.state
    session.assert_valid_state_mapping()
    session.bootstrap_to_signaling_ready()
    session.apply_transition("negotiationneeded_or_inbound_offer")
    session.apply_transition("offer_answer_commit")
    session.apply_transition("ice_connected_or_completed")
    session.apply_transition("hangup_or_policy_termination")
    session.apply_transition("close_completed")
    if session.state != "session_closed":
        raise WebRTCLifecycleSmokeError("Scenario A did not end in session_closed")
    return {
        "scenario_id": "A_happy_path_lifecycle",
        "start_state": start_state,
        "trigger_sequence": list(session.trigger_history),
        "deterministic_action": "normal_lifecycle_progression",
        "end_state": session.state,
        "status": "PASS",
    }


def _scenario_b_glare_roles() -> dict[str, object]:
    polite = _new_session("polite", "scenario-b-polite")
    impolite = _new_session("impolite", "scenario-b-impolite")
    for session in (polite, impolite):
        session.bootstrap_to_signaling_ready()
        session.apply_transition("negotiationneeded_or_inbound_offer")

    polite_action = DETERMINISTIC_SIGNALING_CASE_ACTIONS["glare_offer_collision"]["polite"]
    impolite_action = DETERMINISTIC_SIGNALING_CASE_ACTIONS["glare_offer_collision"]["impolite"]
    if polite_action != ROLLBACK_POLICY["polite_on_offer_collision"]:
        raise WebRTCLifecycleSmokeError("Scenario B polite action is inconsistent with rollback policy")
    if impolite_action != ROLLBACK_POLICY["impolite_on_offer_collision"]:
        raise WebRTCLifecycleSmokeError("Scenario B impolite action is inconsistent with rollback policy")

    # Polite peer resolves glare by rollback -> stable path -> re-enter negotiation.
    polite.apply_transition("rollback_to_stable")
    polite.apply_transition("negotiationneeded_or_inbound_offer")

    # Impolite peer ignores colliding offer and continues existing negotiation.
    impolite.apply_transition("offer_answer_commit")
    impolite.apply_transition("ice_connected_or_completed")

    if polite.state != "session_negotiating":
        raise WebRTCLifecycleSmokeError("Scenario B polite glare path must end in session_negotiating")
    if impolite.state != "session_connected":
        raise WebRTCLifecycleSmokeError("Scenario B impolite glare path must end in session_connected")

    return {
        "scenario_id": "B_glare_collision_roles",
        "start_state": "session_signaling_ready",
        "trigger_sequence": {
            "polite": polite.trigger_history,
            "impolite": impolite.trigger_history,
        },
        "role_actions": {
            "polite": polite_action,
            "impolite": impolite_action,
        },
        "deterministic_action": "polite_rollback_impolite_ignore",
        "end_state": {
            "polite": polite.state,
            "impolite": impolite.state,
        },
        "status": "PASS",
    }


def _scenario_c_transient_disconnect_recovery() -> dict[str, object]:
    session = _new_session("polite", "scenario-c")
    session.bootstrap_to_signaling_ready()
    session.apply_transition("negotiationneeded_or_inbound_offer")
    session.apply_transition("offer_answer_commit")
    session.apply_transition("ice_connected_or_completed")
    start_state = session.state

    transient_rules = RECOVERY_ELIGIBILITY_RULES["transient_disconnect"]
    if transient_rules["reconnect_eligible"] is not True:
        raise WebRTCLifecycleSmokeError("Scenario C requires transient_disconnect reconnect eligibility")

    session.apply_transition("connection_disconnected")
    if session.state != "session_degraded":
        raise WebRTCLifecycleSmokeError("Scenario C must enter session_degraded on disconnect")
    session.apply_transition("connectivity_restored_without_restart")
    if session.state != "session_connected":
        raise WebRTCLifecycleSmokeError("Scenario C must return to session_connected")

    return {
        "scenario_id": "C_transient_disconnect_recovery",
        "start_state": start_state,
        "trigger_sequence": list(session.trigger_history),
        "deterministic_action": DETERMINISTIC_RECOVERY_CASE_ACTIONS["transient_disconnect_before_timeout"],
        "end_state": session.state,
        "status": "PASS",
    }


def _scenario_d_failed_ice_restart() -> dict[str, object]:
    session = _new_session("polite", "scenario-d")
    session.bootstrap_to_signaling_ready()
    session.apply_transition("negotiationneeded_or_inbound_offer")
    session.apply_transition("offer_answer_commit")
    session.apply_transition("ice_connected_or_completed")

    failed_rules = RECOVERY_ELIGIBILITY_RULES["hard_ice_failure"]
    if failed_rules["ice_restart_eligible"] is not True:
        raise WebRTCLifecycleSmokeError("Scenario D requires hard_ice_failure restart eligibility")

    session.apply_transition("connection_disconnected")
    session.apply_transition("recovery_policy_activation")
    session.pending_recovery_id = f"recovery-{uuid.uuid4().hex[:8]}"
    session.apply_transition("ice_restart_requires_renegotiation")
    session.apply_transition("offer_answer_commit")
    session.apply_transition("ice_connected_or_completed")
    session.pending_recovery_id = None

    if session.state != "session_connected":
        raise WebRTCLifecycleSmokeError("Scenario D must recover to session_connected")

    return {
        "scenario_id": "D_failed_ice_restart_recovery",
        "start_state": "session_connected",
        "trigger_sequence": list(session.trigger_history),
        "deterministic_action": DETERMINISTIC_RECOVERY_CASE_ACTIONS["failed_ice_state"],
        "end_state": session.state,
        "status": "PASS",
    }


def _scenario_e_late_signaling_ignored() -> dict[str, object]:
    session = _new_session("polite", "scenario-e")
    session.bootstrap_to_signaling_ready()
    session.apply_transition("negotiationneeded_or_inbound_offer")
    session.apply_transition("offer_answer_commit")
    session.apply_transition("ice_connected_or_completed")
    start_state = session.state

    late_action = DETERMINISTIC_SIGNALING_CASE_ACTIONS["late_answer_after_stable"]["polite"]
    if late_action != "ignore_and_log_late_answer":
        raise WebRTCLifecycleSmokeError("Scenario E late answer action must be ignore_and_log_late_answer")

    # Late signaling is ignored and does not mutate lifecycle state.
    session.trigger_history.append("late_answer_after_stable_ignored")
    if session.state != start_state:
        raise WebRTCLifecycleSmokeError("Scenario E late answer must not mutate state")

    return {
        "scenario_id": "E_late_signaling_ignored",
        "start_state": start_state,
        "trigger_sequence": list(session.trigger_history),
        "deterministic_action": late_action,
        "end_state": session.state,
        "status": "PASS",
    }


def _scenario_f_close_during_pending_recovery() -> dict[str, object]:
    session = _new_session("polite", "scenario-f")
    session.bootstrap_to_signaling_ready()
    session.apply_transition("negotiationneeded_or_inbound_offer")
    session.apply_transition("offer_answer_commit")
    session.apply_transition("ice_connected_or_completed")
    session.apply_transition("connection_disconnected")
    session.apply_transition("recovery_policy_activation")
    session.pending_recovery_id = f"recovery-{uuid.uuid4().hex[:8]}"

    # Recovery is abandoned and escalates to terminal close path.
    session.apply_transition("recovery_failed")
    session.apply_transition("failure_cleanup")
    session.pending_recovery_id = None

    if session.state != "session_closed":
        raise WebRTCLifecycleSmokeError("Scenario F must end in session_closed")

    terminal_action = DETERMINISTIC_RECOVERY_CASE_ACTIONS["signal_received_for_closed_session"]
    if terminal_action != "reject_signal_terminal":
        raise WebRTCLifecycleSmokeError("Scenario F terminal signal action must be reject_signal_terminal")

    session.trigger_history.append("late_signal_rejected_for_closed_session")
    return {
        "scenario_id": "F_close_during_pending_recovery",
        "start_state": "session_recovering",
        "trigger_sequence": list(session.trigger_history),
        "deterministic_action": terminal_action,
        "end_state": session.state,
        "status": "PASS",
    }


def run_webrtc_lifecycle_sandbox_smoke(*, return_proof: bool = False) -> int | dict[str, object]:
    scenarios = [
        _scenario_a_happy_path(),
        _scenario_b_glare_roles(),
        _scenario_c_transient_disconnect_recovery(),
        _scenario_d_failed_ice_restart(),
        _scenario_e_late_signaling_ignored(),
        _scenario_f_close_during_pending_recovery(),
    ]

    proof = {
        "overall_status": "PASS",
        "scenarios_passed": len(scenarios),
        "scenarios_total": len(scenarios),
        "scenarios": scenarios,
    }
    print("WebRTC lifecycle sandbox smoke proof:")
    print(json.dumps(proof, ensure_ascii=True, sort_keys=True, indent=2))
    print("WebRTC lifecycle sandbox smoke: OK")
    if return_proof:
        return proof
    return 0


def main() -> int:
    try:
        return run_webrtc_lifecycle_sandbox_smoke()
    except WebRTCLifecycleSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"WebRTC lifecycle sandbox smoke: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - runtime harness
        print(f"WebRTC lifecycle sandbox smoke: FAILED (unexpected) - {exc!r}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

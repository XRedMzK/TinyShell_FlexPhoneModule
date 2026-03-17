from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PeerSessionStateSpec:
    state_name: str
    signaling_states: tuple[str, ...]
    ice_connection_states: tuple[str, ...]
    connection_states: tuple[str, ...]
    terminal_state: bool
    recovery_eligible: bool
    ownership_domain: str
    next_step_policy: str


@dataclass(frozen=True)
class PeerSessionTransitionSpec:
    from_state: str
    to_state: str
    trigger: str
    transition_group: str
    recovery_path: bool
    requires_negotiation_owner: bool


SIGNALING_STATE_VALUES = {
    "stable",
    "have-local-offer",
    "have-remote-offer",
    "have-local-pranswer",
    "have-remote-pranswer",
    "closed",
}

ICE_CONNECTION_STATE_VALUES = {
    "new",
    "checking",
    "connected",
    "completed",
    "failed",
    "disconnected",
    "closed",
}

CONNECTION_STATE_VALUES = {
    "new",
    "connecting",
    "connected",
    "disconnected",
    "failed",
    "closed",
}

CANONICAL_PEER_SESSION_STATES = (
    "session_new",
    "session_signaling_ready",
    "session_negotiating",
    "session_connecting",
    "session_connected",
    "session_degraded",
    "session_recovering",
    "session_closing",
    "session_closed",
    "session_failed",
)

TERMINAL_STATES = {"session_closed", "session_failed"}
RECOVERY_ELIGIBLE_STATES = {"session_degraded", "session_recovering", "session_connecting"}

OWNERSHIP_BOUNDARIES = {
    "client_lifecycle_owner": (
        "peer_connection_state_tracking",
        "negotiation_owner_selection",
        "reconnect_and_ice_restart_execution",
        "stale_peer_cleanup",
    ),
    "signaling_session_metadata_owner": (
        "session_member_metadata",
        "authoritative_signaling_event_metadata",
        "rollback_eligible_transition_metadata",
    ),
    "shared_contract_fields": (
        "session_id",
        "peer_id",
        "negotiation_epoch",
        "last_authoritative_event_id",
    ),
    "ownership_overlap_forbidden": True,
}


PEER_SESSION_STATE_INVENTORY_BASELINE: dict[str, PeerSessionStateSpec] = {
    "session_new": PeerSessionStateSpec(
        state_name="session_new",
        signaling_states=("stable",),
        ice_connection_states=("new",),
        connection_states=("new",),
        terminal_state=False,
        recovery_eligible=False,
        ownership_domain="client_lifecycle",
        next_step_policy="wait_for_signaling_ready",
    ),
    "session_signaling_ready": PeerSessionStateSpec(
        state_name="session_signaling_ready",
        signaling_states=("stable",),
        ice_connection_states=("new", "checking"),
        connection_states=("new", "connecting"),
        terminal_state=False,
        recovery_eligible=False,
        ownership_domain="client_lifecycle",
        next_step_policy="enter_negotiation_on_offer_answer_required",
    ),
    "session_negotiating": PeerSessionStateSpec(
        state_name="session_negotiating",
        signaling_states=(
            "stable",
            "have-local-offer",
            "have-remote-offer",
            "have-local-pranswer",
            "have-remote-pranswer",
        ),
        ice_connection_states=("new", "checking", "connected", "completed"),
        connection_states=("new", "connecting", "connected"),
        terminal_state=False,
        recovery_eligible=False,
        ownership_domain="client_lifecycle",
        next_step_policy="resolve_glare_or_commit_offer_answer",
    ),
    "session_connecting": PeerSessionStateSpec(
        state_name="session_connecting",
        signaling_states=("stable", "have-local-pranswer", "have-remote-pranswer"),
        ice_connection_states=("checking", "new"),
        connection_states=("connecting", "new"),
        terminal_state=False,
        recovery_eligible=True,
        ownership_domain="client_lifecycle",
        next_step_policy="wait_for_ice_connectivity_or_recovery",
    ),
    "session_connected": PeerSessionStateSpec(
        state_name="session_connected",
        signaling_states=("stable",),
        ice_connection_states=("connected", "completed"),
        connection_states=("connected",),
        terminal_state=False,
        recovery_eligible=False,
        ownership_domain="client_lifecycle",
        next_step_policy="monitor_health_or_begin_close_sequence",
    ),
    "session_degraded": PeerSessionStateSpec(
        state_name="session_degraded",
        signaling_states=("stable",),
        ice_connection_states=("disconnected",),
        connection_states=("disconnected",),
        terminal_state=False,
        recovery_eligible=True,
        ownership_domain="client_lifecycle",
        next_step_policy="attempt_recovery_or_fail",
    ),
    "session_recovering": PeerSessionStateSpec(
        state_name="session_recovering",
        signaling_states=("stable", "have-local-offer", "have-remote-offer"),
        ice_connection_states=("checking", "disconnected", "failed"),
        connection_states=("connecting", "disconnected", "failed"),
        terminal_state=False,
        recovery_eligible=True,
        ownership_domain="client_lifecycle",
        next_step_policy="run_ice_restart_and_renegotiate",
    ),
    "session_closing": PeerSessionStateSpec(
        state_name="session_closing",
        signaling_states=("stable", "closed"),
        ice_connection_states=("disconnected", "failed", "closed"),
        connection_states=("disconnected", "failed", "closed"),
        terminal_state=False,
        recovery_eligible=False,
        ownership_domain="client_lifecycle",
        next_step_policy="move_to_closed",
    ),
    "session_closed": PeerSessionStateSpec(
        state_name="session_closed",
        signaling_states=("closed",),
        ice_connection_states=("closed",),
        connection_states=("closed",),
        terminal_state=True,
        recovery_eligible=False,
        ownership_domain="client_lifecycle",
        next_step_policy="terminal",
    ),
    "session_failed": PeerSessionStateSpec(
        state_name="session_failed",
        signaling_states=("stable", "have-local-offer", "have-remote-offer"),
        ice_connection_states=("failed",),
        connection_states=("failed",),
        terminal_state=True,
        recovery_eligible=False,
        ownership_domain="client_lifecycle",
        next_step_policy="close_or_recreate_session",
    ),
}


PEER_SESSION_TRANSITION_MATRIX_BASELINE: tuple[PeerSessionTransitionSpec, ...] = (
    PeerSessionTransitionSpec(
        from_state="session_signaling_ready",
        to_state="session_negotiating",
        trigger="negotiationneeded_or_inbound_offer",
        transition_group="negotiation_path",
        recovery_path=False,
        requires_negotiation_owner=True,
    ),
    PeerSessionTransitionSpec(
        from_state="session_negotiating",
        to_state="session_connecting",
        trigger="offer_answer_commit",
        transition_group="negotiation_path",
        recovery_path=False,
        requires_negotiation_owner=True,
    ),
    PeerSessionTransitionSpec(
        from_state="session_connecting",
        to_state="session_connected",
        trigger="ice_connected_or_completed",
        transition_group="negotiation_path",
        recovery_path=False,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_negotiating",
        to_state="session_negotiating",
        trigger="glare_resolution_retry",
        transition_group="glare_rollback_path",
        recovery_path=False,
        requires_negotiation_owner=True,
    ),
    PeerSessionTransitionSpec(
        from_state="session_negotiating",
        to_state="session_signaling_ready",
        trigger="rollback_to_stable",
        transition_group="glare_rollback_path",
        recovery_path=False,
        requires_negotiation_owner=True,
    ),
    PeerSessionTransitionSpec(
        from_state="session_connected",
        to_state="session_degraded",
        trigger="connection_disconnected",
        transition_group="connectivity_degradation_path",
        recovery_path=True,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_degraded",
        to_state="session_connected",
        trigger="connectivity_restored_without_restart",
        transition_group="connectivity_degradation_path",
        recovery_path=True,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_degraded",
        to_state="session_recovering",
        trigger="recovery_policy_activation",
        transition_group="connectivity_degradation_path",
        recovery_path=True,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_degraded",
        to_state="session_failed",
        trigger="recovery_budget_exhausted",
        transition_group="connectivity_degradation_path",
        recovery_path=False,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_recovering",
        to_state="session_negotiating",
        trigger="ice_restart_requires_renegotiation",
        transition_group="ice_restart_path",
        recovery_path=True,
        requires_negotiation_owner=True,
    ),
    PeerSessionTransitionSpec(
        from_state="session_recovering",
        to_state="session_connected",
        trigger="recovery_successful",
        transition_group="ice_restart_path",
        recovery_path=True,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_recovering",
        to_state="session_failed",
        trigger="recovery_failed",
        transition_group="ice_restart_path",
        recovery_path=False,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_connected",
        to_state="session_closing",
        trigger="hangup_or_policy_termination",
        transition_group="terminal_path",
        recovery_path=False,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_closing",
        to_state="session_closed",
        trigger="close_completed",
        transition_group="terminal_path",
        recovery_path=False,
        requires_negotiation_owner=False,
    ),
    PeerSessionTransitionSpec(
        from_state="session_failed",
        to_state="session_closed",
        trigger="failure_cleanup",
        transition_group="terminal_path",
        recovery_path=False,
        requires_negotiation_owner=False,
    ),
)


STATE_TRANSITION_INVARIANTS = {
    "single_canonical_state_per_peer_session": True,
    "session_closed_terminal": True,
    "session_failed_terminal_for_active_session": True,
    "recovery_states_explicitly_listed": True,
    "non_terminal_states_have_next_step_policy": True,
    "browser_closed_not_mapped_to_recoverable_state": True,
    "negotiation_owner_required_for_negotiation_transitions": True,
}


def validate_webrtc_peer_session_state_inventory() -> list[str]:
    errors: list[str] = []

    from app.webrtc_session_lifecycle_hardening_baseline import (
        SIGNALING_MEDIA_OWNERSHIP_BOUNDARIES,
        STAGE24_SUBSTEP_DRAFT,
    )

    if tuple(PEER_SESSION_STATE_INVENTORY_BASELINE.keys()) != CANONICAL_PEER_SESSION_STATES:
        errors.append("PEER_SESSION_STATE_INVENTORY_BASELINE keys must match canonical state order")

    for state_name, spec in PEER_SESSION_STATE_INVENTORY_BASELINE.items():
        if spec.state_name != state_name:
            errors.append(f"{state_name}: state_name field must match dictionary key")
        if not set(spec.signaling_states).issubset(SIGNALING_STATE_VALUES):
            errors.append(f"{state_name}: invalid signalingState mapping values")
        if not set(spec.ice_connection_states).issubset(ICE_CONNECTION_STATE_VALUES):
            errors.append(f"{state_name}: invalid iceConnectionState mapping values")
        if not set(spec.connection_states).issubset(CONNECTION_STATE_VALUES):
            errors.append(f"{state_name}: invalid connectionState mapping values")
        if spec.terminal_state and spec.recovery_eligible:
            errors.append(f"{state_name}: terminal state cannot be recovery-eligible")
        if spec.ownership_domain != "client_lifecycle":
            errors.append(f"{state_name}: ownership_domain must be client_lifecycle")
        if not spec.next_step_policy:
            errors.append(f"{state_name}: next_step_policy must be non-empty")
        if "closed" in spec.signaling_states and state_name not in {"session_closed", "session_closing"}:
            errors.append(f"{state_name}: signalingState=closed may map only to closing/closed canonical states")

    if {k for k, v in PEER_SESSION_STATE_INVENTORY_BASELINE.items() if v.terminal_state} != TERMINAL_STATES:
        errors.append("terminal state set must match session_closed and session_failed")

    if not set(RECOVERY_ELIGIBLE_STATES).issubset(set(CANONICAL_PEER_SESSION_STATES)):
        errors.append("RECOVERY_ELIGIBLE_STATES must be subset of canonical states")

    closed_spec = PEER_SESSION_STATE_INVENTORY_BASELINE["session_closed"]
    if closed_spec.signaling_states != ("closed",):
        errors.append("session_closed must map signalingState strictly to closed")
    if closed_spec.ice_connection_states != ("closed",):
        errors.append("session_closed must map iceConnectionState strictly to closed")
    if closed_spec.connection_states != ("closed",):
        errors.append("session_closed must map connectionState strictly to closed")

    transition_pairs: set[tuple[str, str]] = set()
    for transition in PEER_SESSION_TRANSITION_MATRIX_BASELINE:
        if transition.from_state not in PEER_SESSION_STATE_INVENTORY_BASELINE:
            errors.append(f"transition {transition.from_state}->{transition.to_state}: unknown from_state")
            continue
        if transition.to_state not in PEER_SESSION_STATE_INVENTORY_BASELINE:
            errors.append(f"transition {transition.from_state}->{transition.to_state}: unknown to_state")
            continue
        pair = (transition.from_state, transition.to_state)
        if pair in transition_pairs:
            errors.append(f"transition {transition.from_state}->{transition.to_state}: duplicated transition pair")
        transition_pairs.add(pair)
        if transition.requires_negotiation_owner and transition.transition_group not in {
            "negotiation_path",
            "glare_rollback_path",
            "ice_restart_path",
        }:
            errors.append(
                f"transition {transition.from_state}->{transition.to_state}: negotiation owner required outside negotiation/recovery groups"
            )

    required_pairs = {
        ("session_signaling_ready", "session_negotiating"),
        ("session_negotiating", "session_connecting"),
        ("session_connecting", "session_connected"),
        ("session_negotiating", "session_negotiating"),
        ("session_negotiating", "session_signaling_ready"),
        ("session_connected", "session_degraded"),
        ("session_degraded", "session_connected"),
        ("session_degraded", "session_recovering"),
        ("session_degraded", "session_failed"),
        ("session_recovering", "session_negotiating"),
        ("session_recovering", "session_connected"),
        ("session_recovering", "session_failed"),
        ("session_connected", "session_closing"),
        ("session_closing", "session_closed"),
        ("session_failed", "session_closed"),
    }
    missing_pairs = sorted(required_pairs - transition_pairs)
    if missing_pairs:
        errors.append(f"transition matrix missing required pairs: {missing_pairs}")

    # Terminal state outgoing rules: closed has no outgoing; failed may only go to closed.
    outgoing_by_from: dict[str, set[str]] = {}
    for from_state, to_state in transition_pairs:
        outgoing_by_from.setdefault(from_state, set()).add(to_state)
    if outgoing_by_from.get("session_closed"):
        errors.append("session_closed must not have outgoing transitions")
    if outgoing_by_from.get("session_failed", set()) - {"session_closed"}:
        errors.append("session_failed may only transition to session_closed")

    # Link against Step 24.1 ownership boundaries and stage draft.
    if SIGNALING_MEDIA_OWNERSHIP_BOUNDARIES.get("ownership_overlap_forbidden") is not True:
        errors.append("Step 24.1 ownership boundary invariant must remain true")
    if STAGE24_SUBSTEP_DRAFT.get("24.2") != "peer_session_state_inventory_and_transition_matrix":
        errors.append("Step 24.1 substep draft must define 24.2 inventory/matrix milestone")

    required_invariants = {
        "single_canonical_state_per_peer_session": True,
        "session_closed_terminal": True,
        "session_failed_terminal_for_active_session": True,
        "recovery_states_explicitly_listed": True,
        "non_terminal_states_have_next_step_policy": True,
        "browser_closed_not_mapped_to_recoverable_state": True,
        "negotiation_owner_required_for_negotiation_transitions": True,
    }
    if STATE_TRANSITION_INVARIANTS != required_invariants:
        errors.append("STATE_TRANSITION_INVARIANTS must match baseline invariant set")

    return errors

from __future__ import annotations


NEGOTIATION_ROLES = ("polite", "impolite")

NEGOTIATION_OWNER_RULES = {
    "single_active_negotiation_owner_per_session": True,
    "owner_identity_fields": ("session_id", "negotiation_epoch", "owner_peer_id", "owner_role"),
    "owner_required_for_local_offer_creation": True,
    "owner_required_for_local_answer_commit": True,
    "owner_transfer_allowed_on_glare_for_polite_peer": True,
}

OFFER_COLLISION_DETECTION_RULES = {
    "incoming_offer_required": True,
    "collision_if_local_signaling_state_in": ("have-local-offer", "have-local-pranswer"),
    "collision_if_local_negotiation_inflight": True,
    "collision_if_non_stable_offer_processing": True,
}

NEGOTIATIONNEEDED_HANDLING_POLICY = {
    "event_is_primary_local_renegotiation_trigger": True,
    "only_start_offer_when_signaling_state_stable": True,
    "suppress_parallel_offer_attempts": True,
    "queue_when_non_stable": True,
    "coalesce_duplicate_events_while_queued": True,
}

SIGNALING_API_PRECONDITIONS = {
    "setLocalDescription_offer": ("stable",),
    "setRemoteDescription_offer": ("stable",),
    "setLocalDescription_answer": ("have-remote-offer",),
    "setRemoteDescription_answer": ("have-local-offer",),
    "setLocalDescription_rollback": (
        "have-local-offer",
        "have-remote-offer",
        "have-local-pranswer",
        "have-remote-pranswer",
    ),
}

ROLLBACK_POLICY = {
    "polite_on_offer_collision": "rollback_then_apply_remote_offer",
    "impolite_on_offer_collision": "ignore_incoming_offer",
    "rollback_from_stable_allowed": False,
    "rollback_requires_collision_or_glare_path": True,
    "post_rollback_target_signaling_state": "stable",
}

DETERMINISTIC_SIGNALING_CASE_ACTIONS = {
    "glare_offer_collision": {
        "polite": "rollback_then_apply_remote_offer",
        "impolite": "ignore_incoming_offer",
    },
    "late_answer_after_stable": {
        "polite": "ignore_and_log_late_answer",
        "impolite": "ignore_and_log_late_answer",
    },
    "duplicate_answer": {
        "polite": "ignore_and_log_duplicate_answer",
        "impolite": "ignore_and_log_duplicate_answer",
    },
    "out_of_order_offer_non_stable": {
        "polite": "rollback_then_apply_remote_offer",
        "impolite": "ignore_incoming_offer",
    },
    "stale_offer_after_rollback_epoch_mismatch": {
        "polite": "ignore_and_request_resync",
        "impolite": "ignore_and_request_resync",
    },
    "signaling_for_closed_or_failed_session": {
        "polite": "reject_signal_and_close_path",
        "impolite": "reject_signal_and_close_path",
    },
}

NEGOTIATION_GLARE_INVARIANTS = {
    "single_active_local_negotiation_attempt": True,
    "signaling_state_is_legality_source_of_truth": True,
    "collision_handling_deterministic_by_role": True,
    "rollback_not_generic_error_recovery": True,
    "glare_resolution_returns_to_stable_path": True,
    "out_of_order_cases_have_deterministic_action": True,
    "production_runtime_change_allowed_in_24_3": False,
}


def validate_webrtc_negotiation_glare_resolution_contract() -> list[str]:
    errors: list[str] = []

    from app.webrtc_peer_session_state_inventory import (
        PEER_SESSION_TRANSITION_MATRIX_BASELINE,
        SIGNALING_STATE_VALUES,
    )
    from app.webrtc_session_lifecycle_hardening_baseline import STAGE24_SUBSTEP_DRAFT

    if NEGOTIATION_ROLES != ("polite", "impolite"):
        errors.append("NEGOTIATION_ROLES must be (polite, impolite)")

    required_owner_rules = {
        "single_active_negotiation_owner_per_session": True,
        "owner_identity_fields": ("session_id", "negotiation_epoch", "owner_peer_id", "owner_role"),
        "owner_required_for_local_offer_creation": True,
        "owner_required_for_local_answer_commit": True,
        "owner_transfer_allowed_on_glare_for_polite_peer": True,
    }
    if NEGOTIATION_OWNER_RULES != required_owner_rules:
        errors.append("NEGOTIATION_OWNER_RULES must match canonical owner rule set")

    required_collision_rules = {
        "incoming_offer_required": True,
        "collision_if_local_signaling_state_in": ("have-local-offer", "have-local-pranswer"),
        "collision_if_local_negotiation_inflight": True,
        "collision_if_non_stable_offer_processing": True,
    }
    if OFFER_COLLISION_DETECTION_RULES != required_collision_rules:
        errors.append("OFFER_COLLISION_DETECTION_RULES must match canonical collision detection baseline")

    required_negotiationneeded_policy = {
        "event_is_primary_local_renegotiation_trigger": True,
        "only_start_offer_when_signaling_state_stable": True,
        "suppress_parallel_offer_attempts": True,
        "queue_when_non_stable": True,
        "coalesce_duplicate_events_while_queued": True,
    }
    if NEGOTIATIONNEEDED_HANDLING_POLICY != required_negotiationneeded_policy:
        errors.append("NEGOTIATIONNEEDED_HANDLING_POLICY must match canonical policy")

    required_precondition_keys = {
        "setLocalDescription_offer",
        "setRemoteDescription_offer",
        "setLocalDescription_answer",
        "setRemoteDescription_answer",
        "setLocalDescription_rollback",
    }
    if set(SIGNALING_API_PRECONDITIONS.keys()) != required_precondition_keys:
        errors.append("SIGNALING_API_PRECONDITIONS must define canonical SDP API precondition set")
    for api_name, states in SIGNALING_API_PRECONDITIONS.items():
        if not states:
            errors.append(f"{api_name}: precondition states must be non-empty")
            continue
        if not set(states).issubset(SIGNALING_STATE_VALUES):
            errors.append(f"{api_name}: precondition states must be valid signalingState values")

    required_rollback_policy = {
        "polite_on_offer_collision": "rollback_then_apply_remote_offer",
        "impolite_on_offer_collision": "ignore_incoming_offer",
        "rollback_from_stable_allowed": False,
        "rollback_requires_collision_or_glare_path": True,
        "post_rollback_target_signaling_state": "stable",
    }
    if ROLLBACK_POLICY != required_rollback_policy:
        errors.append("ROLLBACK_POLICY must match canonical glare rollback baseline")

    required_cases = {
        "glare_offer_collision",
        "late_answer_after_stable",
        "duplicate_answer",
        "out_of_order_offer_non_stable",
        "stale_offer_after_rollback_epoch_mismatch",
        "signaling_for_closed_or_failed_session",
    }
    if set(DETERMINISTIC_SIGNALING_CASE_ACTIONS.keys()) != required_cases:
        errors.append("DETERMINISTIC_SIGNALING_CASE_ACTIONS must define canonical case set")
    for case_name, role_actions in DETERMINISTIC_SIGNALING_CASE_ACTIONS.items():
        if set(role_actions.keys()) != {"polite", "impolite"}:
            errors.append(f"{case_name}: action mapping must define polite and impolite actions")

    if DETERMINISTIC_SIGNALING_CASE_ACTIONS["glare_offer_collision"]["polite"] != "rollback_then_apply_remote_offer":
        errors.append("glare_offer_collision polite action must be rollback_then_apply_remote_offer")
    if DETERMINISTIC_SIGNALING_CASE_ACTIONS["glare_offer_collision"]["impolite"] != "ignore_incoming_offer":
        errors.append("glare_offer_collision impolite action must be ignore_incoming_offer")

    required_transitions = {
        ("session_signaling_ready", "session_negotiating"),
        ("session_negotiating", "session_connecting"),
        ("session_negotiating", "session_signaling_ready"),
    }
    transition_pairs = {
        (transition.from_state, transition.to_state)
        for transition in PEER_SESSION_TRANSITION_MATRIX_BASELINE
    }
    missing_transitions = sorted(required_transitions - transition_pairs)
    if missing_transitions:
        errors.append(
            f"Step 24.2 transition matrix missing negotiation/glare required transitions: {missing_transitions}"
        )

    required_invariants = {
        "single_active_local_negotiation_attempt": True,
        "signaling_state_is_legality_source_of_truth": True,
        "collision_handling_deterministic_by_role": True,
        "rollback_not_generic_error_recovery": True,
        "glare_resolution_returns_to_stable_path": True,
        "out_of_order_cases_have_deterministic_action": True,
        "production_runtime_change_allowed_in_24_3": False,
    }
    if NEGOTIATION_GLARE_INVARIANTS != required_invariants:
        errors.append("NEGOTIATION_GLARE_INVARIANTS must match canonical invariant set")

    if STAGE24_SUBSTEP_DRAFT.get("24.3") != "negotiation_and_glare_resolution_contract":
        errors.append("Step 24.1 substep draft must define 24.3 negotiation/glare contract milestone")

    return errors

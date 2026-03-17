from __future__ import annotations


RECOVERY_TRIGGER_CLASSES = {
    "transient_disconnect": {
        "ice_connection_states": ("disconnected",),
        "connection_states": ("disconnected",),
        "terminal_trigger": False,
    },
    "hard_ice_failure": {
        "ice_connection_states": ("failed",),
        "connection_states": ("failed", "disconnected"),
        "terminal_trigger": False,
    },
    "aggregate_connection_failure": {
        "ice_connection_states": ("failed", "disconnected"),
        "connection_states": ("failed",),
        "terminal_trigger": False,
    },
    "late_recovery": {
        "ice_connection_states": ("checking", "connected", "completed", "failed"),
        "connection_states": ("connecting", "connected", "disconnected", "failed"),
        "terminal_trigger": False,
    },
    "abandoned_recovery": {
        "ice_connection_states": ("failed", "disconnected"),
        "connection_states": ("failed", "disconnected"),
        "terminal_trigger": False,
    },
    "terminal_close": {
        "ice_connection_states": ("closed",),
        "connection_states": ("closed",),
        "terminal_trigger": True,
    },
}

RECOVERY_ELIGIBILITY_RULES = {
    "transient_disconnect": {
        "reconnect_eligible": True,
        "ice_restart_eligible": False,
        "terminal_close_required": False,
        "next_action": "observe_or_reconnect_with_timeout",
    },
    "hard_ice_failure": {
        "reconnect_eligible": False,
        "ice_restart_eligible": True,
        "terminal_close_required": False,
        "next_action": "start_ice_restart_negotiation",
    },
    "aggregate_connection_failure": {
        "reconnect_eligible": False,
        "ice_restart_eligible": True,
        "terminal_close_required": False,
        "next_action": "start_ice_restart_or_escalate_close",
    },
    "late_recovery": {
        "reconnect_eligible": False,
        "ice_restart_eligible": False,
        "terminal_close_required": False,
        "next_action": "ignore_late_recovery_and_log",
    },
    "abandoned_recovery": {
        "reconnect_eligible": False,
        "ice_restart_eligible": False,
        "terminal_close_required": True,
        "next_action": "close_and_recreate_session",
    },
    "terminal_close": {
        "reconnect_eligible": False,
        "ice_restart_eligible": False,
        "terminal_close_required": True,
        "next_action": "reject_recovery_new_session_required",
    },
}

PENDING_RECOVERY_SCHEMA = (
    "recovery_id",
    "session_id",
    "peer_id",
    "trigger_class",
    "started_at_ms",
    "deadline_ms",
    "owner",
    "allowed_action_set",
    "escalation_target",
    "status",
)

PENDING_RECOVERY_OWNERSHIP = {
    "pending_recovery_owner": "client_lifecycle",
    "metadata_owner": "signaling_session_metadata",
    "single_active_recovery_attempt_per_session": True,
    "status_values": ("pending", "escalated", "resolved", "abandoned"),
}

ICE_RESTART_SIGNALING_REQUIREMENTS = {
    "requires_negotiation_owner": True,
    "requires_restart_offer_generation": True,
    "requires_offer_answer_cycle": True,
    "follows_24_3_glare_policy": True,
    "reject_restart_for_terminal_session": True,
}

RECOVERY_TIMEOUT_ESCALATION_POLICY = {
    "transient_disconnect_grace_ms": 8000,
    "recovery_attempt_timeout_ms": 25000,
    "max_recovery_attempts_per_epoch": 2,
    "escalate_to_ice_restart_after_transient_timeout": True,
    "escalate_to_terminal_after_recovery_budget_exhausted": True,
}

DETERMINISTIC_RECOVERY_CASE_ACTIONS = {
    "transient_disconnect_before_timeout": "observe_then_reconnect_wait",
    "transient_disconnect_timeout": "escalate_to_ice_restart",
    "failed_ice_state": "start_ice_restart_negotiation",
    "late_recovery_after_timeout": "ignore_late_recovery_and_log",
    "pending_recovery_expired": "mark_abandoned_and_close_or_recreate",
    "signal_received_for_closed_session": "reject_signal_terminal",
    "recovery_collision_during_restart": "apply_24_3_glare_resolution_policy",
}

RECOVERY_INVARIANTS = {
    "disconnected_not_terminal_by_default": True,
    "failed_is_restart_eligible": True,
    "closed_not_recoverable": True,
    "single_active_pending_recovery_per_session": True,
    "recovery_has_terminal_outcome": True,
    "recovery_must_not_violate_24_3_negotiation_contract": True,
    "production_runtime_change_allowed_in_24_4": False,
}


def validate_webrtc_reconnect_ice_restart_pending_recovery_contract() -> list[str]:
    errors: list[str] = []

    from app.webrtc_peer_session_state_inventory import (
        CONNECTION_STATE_VALUES,
        ICE_CONNECTION_STATE_VALUES,
        PEER_SESSION_STATE_INVENTORY_BASELINE,
    )
    from app.webrtc_negotiation_glare_resolution_contract import (
        NEGOTIATION_ROLES,
        ROLLBACK_POLICY,
    )
    from app.webrtc_session_lifecycle_hardening_baseline import STAGE24_SUBSTEP_DRAFT

    required_triggers = {
        "transient_disconnect",
        "hard_ice_failure",
        "aggregate_connection_failure",
        "late_recovery",
        "abandoned_recovery",
        "terminal_close",
    }
    if set(RECOVERY_TRIGGER_CLASSES.keys()) != required_triggers:
        errors.append("RECOVERY_TRIGGER_CLASSES must define canonical trigger class set")

    for trigger_name, trigger_spec in RECOVERY_TRIGGER_CLASSES.items():
        ice_states = set(trigger_spec.get("ice_connection_states", ()))
        connection_states = set(trigger_spec.get("connection_states", ()))
        if not ice_states:
            errors.append(f"{trigger_name}: ice_connection_states must be non-empty")
        if not connection_states:
            errors.append(f"{trigger_name}: connection_states must be non-empty")
        if not ice_states.issubset(ICE_CONNECTION_STATE_VALUES):
            errors.append(f"{trigger_name}: invalid iceConnectionState values")
        if not connection_states.issubset(CONNECTION_STATE_VALUES):
            errors.append(f"{trigger_name}: invalid connectionState values")
        if trigger_name == "terminal_close" and trigger_spec.get("terminal_trigger") is not True:
            errors.append("terminal_close: terminal_trigger must be true")
        if trigger_name != "terminal_close" and trigger_spec.get("terminal_trigger") is True:
            errors.append(f"{trigger_name}: terminal_trigger must be false for non-terminal trigger")

    if set(RECOVERY_ELIGIBILITY_RULES.keys()) != required_triggers:
        errors.append("RECOVERY_ELIGIBILITY_RULES must define eligibility for every trigger class")

    transient_eligibility = RECOVERY_ELIGIBILITY_RULES.get("transient_disconnect", {})
    if transient_eligibility.get("reconnect_eligible") is not True:
        errors.append("transient_disconnect must be reconnect-eligible")
    if transient_eligibility.get("ice_restart_eligible") is not False:
        errors.append("transient_disconnect must not immediately require ice restart")
    if transient_eligibility.get("terminal_close_required") is not False:
        errors.append("transient_disconnect must not be terminal by default")

    failed_eligibility = RECOVERY_ELIGIBILITY_RULES.get("hard_ice_failure", {})
    if failed_eligibility.get("ice_restart_eligible") is not True:
        errors.append("hard_ice_failure must be ice-restart-eligible")

    terminal_eligibility = RECOVERY_ELIGIBILITY_RULES.get("terminal_close", {})
    if terminal_eligibility.get("terminal_close_required") is not True:
        errors.append("terminal_close must require terminal close")
    if terminal_eligibility.get("reconnect_eligible") is not False:
        errors.append("terminal_close must not be reconnect-eligible")
    if terminal_eligibility.get("ice_restart_eligible") is not False:
        errors.append("terminal_close must not be ice-restart-eligible")

    required_schema = (
        "recovery_id",
        "session_id",
        "peer_id",
        "trigger_class",
        "started_at_ms",
        "deadline_ms",
        "owner",
        "allowed_action_set",
        "escalation_target",
        "status",
    )
    if PENDING_RECOVERY_SCHEMA != required_schema:
        errors.append("PENDING_RECOVERY_SCHEMA must match canonical schema")

    required_ownership = {
        "pending_recovery_owner": "client_lifecycle",
        "metadata_owner": "signaling_session_metadata",
        "single_active_recovery_attempt_per_session": True,
        "status_values": ("pending", "escalated", "resolved", "abandoned"),
    }
    if PENDING_RECOVERY_OWNERSHIP != required_ownership:
        errors.append("PENDING_RECOVERY_OWNERSHIP must match canonical ownership contract")

    required_restart_requirements = {
        "requires_negotiation_owner": True,
        "requires_restart_offer_generation": True,
        "requires_offer_answer_cycle": True,
        "follows_24_3_glare_policy": True,
        "reject_restart_for_terminal_session": True,
    }
    if ICE_RESTART_SIGNALING_REQUIREMENTS != required_restart_requirements:
        errors.append("ICE_RESTART_SIGNALING_REQUIREMENTS must match canonical restart signaling requirements")

    if NEGOTIATION_ROLES != ("polite", "impolite"):
        errors.append("Step 24.3 negotiation roles must remain polite/impolite")
    if ROLLBACK_POLICY.get("post_rollback_target_signaling_state") != "stable":
        errors.append("Step 24.3 rollback policy target must remain stable")

    required_timeout_policy = {
        "transient_disconnect_grace_ms": 8000,
        "recovery_attempt_timeout_ms": 25000,
        "max_recovery_attempts_per_epoch": 2,
        "escalate_to_ice_restart_after_transient_timeout": True,
        "escalate_to_terminal_after_recovery_budget_exhausted": True,
    }
    if RECOVERY_TIMEOUT_ESCALATION_POLICY != required_timeout_policy:
        errors.append("RECOVERY_TIMEOUT_ESCALATION_POLICY must match canonical timeout policy")
    if (
        RECOVERY_TIMEOUT_ESCALATION_POLICY["transient_disconnect_grace_ms"]
        >= RECOVERY_TIMEOUT_ESCALATION_POLICY["recovery_attempt_timeout_ms"]
    ):
        errors.append("transient_disconnect_grace_ms must be less than recovery_attempt_timeout_ms")

    required_case_actions = {
        "transient_disconnect_before_timeout": "observe_then_reconnect_wait",
        "transient_disconnect_timeout": "escalate_to_ice_restart",
        "failed_ice_state": "start_ice_restart_negotiation",
        "late_recovery_after_timeout": "ignore_late_recovery_and_log",
        "pending_recovery_expired": "mark_abandoned_and_close_or_recreate",
        "signal_received_for_closed_session": "reject_signal_terminal",
        "recovery_collision_during_restart": "apply_24_3_glare_resolution_policy",
    }
    if DETERMINISTIC_RECOVERY_CASE_ACTIONS != required_case_actions:
        errors.append("DETERMINISTIC_RECOVERY_CASE_ACTIONS must match canonical recovery case actions")

    closed_state = PEER_SESSION_STATE_INVENTORY_BASELINE.get("session_closed")
    failed_state = PEER_SESSION_STATE_INVENTORY_BASELINE.get("session_failed")
    degraded_state = PEER_SESSION_STATE_INVENTORY_BASELINE.get("session_degraded")
    if closed_state is None or failed_state is None or degraded_state is None:
        errors.append("Step 24.2 must define session_closed/session_failed/session_degraded states")
    else:
        if not closed_state.terminal_state:
            errors.append("session_closed must remain terminal in Step 24.2")
        if not failed_state.terminal_state:
            errors.append("session_failed must remain terminal in Step 24.2")
        if degraded_state.terminal_state:
            errors.append("session_degraded must remain non-terminal in Step 24.2")

    required_invariants = {
        "disconnected_not_terminal_by_default": True,
        "failed_is_restart_eligible": True,
        "closed_not_recoverable": True,
        "single_active_pending_recovery_per_session": True,
        "recovery_has_terminal_outcome": True,
        "recovery_must_not_violate_24_3_negotiation_contract": True,
        "production_runtime_change_allowed_in_24_4": False,
    }
    if RECOVERY_INVARIANTS != required_invariants:
        errors.append("RECOVERY_INVARIANTS must match canonical recovery invariant set")

    if STAGE24_SUBSTEP_DRAFT.get("24.4") != "reconnect_ice_restart_and_pending_recovery_contract":
        errors.append("Step 24.1 substep draft must define 24.4 recovery contract milestone")

    return errors

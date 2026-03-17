from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RedisRecoveryEventSpec:
    event_id: str
    description: str
    expected_behavior: str


@dataclass(frozen=True)
class AuthRecoveryOutcomeSpec:
    outcome_id: str
    trigger_state: str
    verify_outcome: str
    recovery_path: str
    fail_closed: bool


REDIS_PUBSUB_DELIVERY_MODEL = "at_most_once_bounded_loss"

REDIS_RECOVERY_EVENTS_BASELINE: dict[str, RedisRecoveryEventSpec] = {
    "redis_loss": RedisRecoveryEventSpec(
        event_id="redis_loss",
        description="Redis state unavailable due to loss/outage",
        expected_behavior="state_dependent_paths_fail_closed_then_converge",
    ),
    "redis_restart": RedisRecoveryEventSpec(
        event_id="redis_restart",
        description="Redis process restart with potentially incomplete transient state",
        expected_behavior="clients_reconnect_and_server_reconciles_current_state",
    ),
    "pubsub_gap": RedisRecoveryEventSpec(
        event_id="pubsub_gap",
        description="Missed Pub/Sub fan-out event during disconnect/restart",
        expected_behavior="event_loss_acceptable_correctness_via_shared_state_convergence",
    ),
    "instance_restart": RedisRecoveryEventSpec(
        event_id="instance_restart",
        description="App instance restart with local runtime state reset",
        expected_behavior="startup_reconciliation_rebuilds_runtime_visible_state",
    ),
}

AUTH_RECOVERY_OUTCOME_BASELINE: dict[str, AuthRecoveryOutcomeSpec] = {
    "missing_challenge": AuthRecoveryOutcomeSpec(
        outcome_id="missing_challenge",
        trigger_state="challenge_not_found",
        verify_outcome="verify_fail_closed",
        recovery_path="reauth_path",
        fail_closed=True,
    ),
    "expired_challenge": AuthRecoveryOutcomeSpec(
        outcome_id="expired_challenge",
        trigger_state="challenge_expired",
        verify_outcome="verify_fail_closed",
        recovery_path="reauth_path",
        fail_closed=True,
    ),
    "inconsistent_challenge": AuthRecoveryOutcomeSpec(
        outcome_id="inconsistent_challenge",
        trigger_state="challenge_inconsistent_or_consumed",
        verify_outcome="verify_fail_closed",
        recovery_path="reauth_path",
        fail_closed=True,
    ),
    "fresh_challenge": AuthRecoveryOutcomeSpec(
        outcome_id="fresh_challenge",
        trigger_state="fresh_challenge_issued",
        verify_outcome="verify_allowed",
        recovery_path="normal_verify",
        fail_closed=False,
    ),
}

SIGNALING_RECOVERY_SEMANTICS_BASELINE = {
    "missed_pubsub_allowed": True,
    "stale_session_rejected": True,
    "phantom_presence_not_authoritative": True,
    "reconnect_reconciliation_required": True,
    "exact_transient_state_restoration_required": False,
}

STARTUP_RECONCILIATION_ASSUMPTIONS = {
    "redis_state_may_be_empty": True,
    "redis_state_may_be_partial": True,
    "redis_state_may_be_stale": True,
}

EXPECTED_CONVERGENCE_PATH = (
    "reconnect",
    "re-auth_if_needed",
    "startup_reconciliation",
)


def validate_recovery_restore_redis_semantics_baseline_contract() -> list[str]:
    errors: list[str] = []

    if REDIS_PUBSUB_DELIVERY_MODEL != "at_most_once_bounded_loss":
        errors.append("REDIS_PUBSUB_DELIVERY_MODEL must be at_most_once_bounded_loss")

    expected_events = ("redis_loss", "redis_restart", "pubsub_gap", "instance_restart")
    if tuple(REDIS_RECOVERY_EVENTS_BASELINE.keys()) != expected_events:
        errors.append("REDIS_RECOVERY_EVENTS_BASELINE keys must be ordered as redis_loss, redis_restart, pubsub_gap, instance_restart")

    for event_id, event_spec in REDIS_RECOVERY_EVENTS_BASELINE.items():
        if event_spec.event_id != event_id:
            errors.append(f"{event_id}: event_id field must match dictionary key")
        if not event_spec.expected_behavior:
            errors.append(f"{event_id}: expected_behavior must not be empty")

    required_auth_outcomes = {
        "missing_challenge",
        "expired_challenge",
        "inconsistent_challenge",
        "fresh_challenge",
    }
    if set(AUTH_RECOVERY_OUTCOME_BASELINE.keys()) != required_auth_outcomes:
        errors.append("AUTH_RECOVERY_OUTCOME_BASELINE must contain required challenge outcomes")

    for outcome_id, outcome_spec in AUTH_RECOVERY_OUTCOME_BASELINE.items():
        if outcome_spec.outcome_id != outcome_id:
            errors.append(f"{outcome_id}: outcome_id field must match dictionary key")

    for fail_closed_outcome in ("missing_challenge", "expired_challenge", "inconsistent_challenge"):
        outcome_spec = AUTH_RECOVERY_OUTCOME_BASELINE[fail_closed_outcome]
        if outcome_spec.verify_outcome != "verify_fail_closed":
            errors.append(f"{fail_closed_outcome}: verify_outcome must be verify_fail_closed")
        if not outcome_spec.fail_closed:
            errors.append(f"{fail_closed_outcome}: fail_closed must be true")

    fresh_outcome = AUTH_RECOVERY_OUTCOME_BASELINE["fresh_challenge"]
    if fresh_outcome.verify_outcome != "verify_allowed":
        errors.append("fresh_challenge: verify_outcome must be verify_allowed")

    required_signaling_flags = {
        "missed_pubsub_allowed": True,
        "stale_session_rejected": True,
        "phantom_presence_not_authoritative": True,
        "reconnect_reconciliation_required": True,
        "exact_transient_state_restoration_required": False,
    }
    if SIGNALING_RECOVERY_SEMANTICS_BASELINE != required_signaling_flags:
        errors.append("SIGNALING_RECOVERY_SEMANTICS_BASELINE must match required signaling flags")

    if set(STARTUP_RECONCILIATION_ASSUMPTIONS.keys()) != {
        "redis_state_may_be_empty",
        "redis_state_may_be_partial",
        "redis_state_may_be_stale",
    }:
        errors.append("STARTUP_RECONCILIATION_ASSUMPTIONS must contain empty/partial/stale keys")
    elif not all(STARTUP_RECONCILIATION_ASSUMPTIONS.values()):
        errors.append("STARTUP_RECONCILIATION_ASSUMPTIONS values must be true")

    if EXPECTED_CONVERGENCE_PATH != (
        "reconnect",
        "re-auth_if_needed",
        "startup_reconciliation",
    ):
        errors.append("EXPECTED_CONVERGENCE_PATH must be reconnect -> re-auth_if_needed -> startup_reconciliation")

    return errors

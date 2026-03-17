from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DurableSignalingEventModelSpec:
    event_name: str
    event_id_required: bool
    stream_entry_id_required: bool
    schema_version_required: bool
    ordering_scope: str
    write_dedup_required: bool
    apply_dedup_required: bool
    replay_required: bool
    replay_source: str
    reconciliation_role: str
    retention_policy: str
    retention_window_hours: int


ORDERING_SCOPES = {"call_id", "participant_id", "service"}

REPLAY_SOURCES = {"authoritative_durable_stream"}

RECONCILIATION_ROLES = {
    "authoritative_coordination_transition",
    "authoritative_session_lifecycle_transition",
}

RETENTION_POLICIES = {
    "bounded_coordination_window",
    "bounded_session_window",
}

DURABLE_EVENT_IDENTITY_CONTRACT = {
    "event_id_required": True,
    "event_id_semantics": "domain_stable_idempotency_identity",
    "stream_entry_id_required": True,
    "stream_entry_semantics": "durable_log_position",
    "schema_version_required": True,
    "issued_at_source": "backend_clock",
}

ORDERING_CONTRACT = {
    "ordering_scope_required": True,
    "ordering_scoped_only": True,
    "cross_scope_global_order_guaranteed": False,
}

DEDUP_CONTRACT = {
    "write_side_dedup_required": True,
    "apply_side_dedup_required": True,
    "idempotent_apply_by_event_id": True,
}

RETENTION_CONTRACT = {
    "bounded_retention_required": True,
    "trim_strategy": "maxlen_or_time_window_policy",
    "minimum_reconciliation_window_hours": 24,
    "trim_must_preserve_reconciliation_window": True,
}

REPLAY_CONTRACT = {
    "replay_source": "authoritative_durable_stream",
    "replay_boundary_required": True,
    "replay_boundary_fields": (
        "last_applied_event_id",
        "last_acknowledged_stream_entry_id",
    ),
    "replay_must_be_idempotent": True,
    "pubsub_hints_not_replay_source": True,
}

RECONCILIATION_CONTRACT = {
    "startup_reconciliation_uses_authoritative_durable_events": True,
    "reconnect_reconciliation_uses_authoritative_durable_events": True,
    "discard_stale_local_assumptions": True,
    "projection_state_rebuildable_from_authoritative_durable_events": True,
    "ephemeral_hints_not_required_for_correctness": True,
}

DURABLE_EVENT_MODEL_INVARIANTS = {
    "authoritative_events_have_dual_identity": True,
    "scoped_ordering_only": True,
    "authoritative_apply_idempotent": True,
    "authoritative_stream_replay_required": True,
    "bounded_retention_reconciliation_safe": True,
    "projection_not_source_of_truth": True,
    "pubsub_not_correctness_critical": True,
    "production_path_switch_allowed": False,
}


DURABLE_AUTHORITATIVE_EVENT_MODEL_BASELINE: dict[str, DurableSignalingEventModelSpec] = {
    "session.created": DurableSignalingEventModelSpec(
        event_name="session.created",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_session_lifecycle_transition",
        retention_policy="bounded_session_window",
        retention_window_hours=72,
    ),
    "session.join-requested": DurableSignalingEventModelSpec(
        event_name="session.join-requested",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_session_lifecycle_transition",
        retention_policy="bounded_session_window",
        retention_window_hours=72,
    ),
    "session.join-accepted": DurableSignalingEventModelSpec(
        event_name="session.join-accepted",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_session_lifecycle_transition",
        retention_policy="bounded_session_window",
        retention_window_hours=72,
    ),
    "session.member-added": DurableSignalingEventModelSpec(
        event_name="session.member-added",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_session_lifecycle_transition",
        retention_policy="bounded_session_window",
        retention_window_hours=72,
    ),
    "session.member-removed": DurableSignalingEventModelSpec(
        event_name="session.member-removed",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_session_lifecycle_transition",
        retention_policy="bounded_session_window",
        retention_window_hours=72,
    ),
    "negotiation.offer-created": DurableSignalingEventModelSpec(
        event_name="negotiation.offer-created",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_coordination_transition",
        retention_policy="bounded_coordination_window",
        retention_window_hours=48,
    ),
    "negotiation.offer-rolled-back": DurableSignalingEventModelSpec(
        event_name="negotiation.offer-rolled-back",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_coordination_transition",
        retention_policy="bounded_coordination_window",
        retention_window_hours=48,
    ),
    "negotiation.answer-committed": DurableSignalingEventModelSpec(
        event_name="negotiation.answer-committed",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_coordination_transition",
        retention_policy="bounded_coordination_window",
        retention_window_hours=48,
    ),
    "negotiation.ice-epoch-started": DurableSignalingEventModelSpec(
        event_name="negotiation.ice-epoch-started",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_coordination_transition",
        retention_policy="bounded_coordination_window",
        retention_window_hours=48,
    ),
    "call.terminated": DurableSignalingEventModelSpec(
        event_name="call.terminated",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_session_lifecycle_transition",
        retention_policy="bounded_session_window",
        retention_window_hours=72,
    ),
    "session.authoritative-state-changed": DurableSignalingEventModelSpec(
        event_name="session.authoritative-state-changed",
        event_id_required=True,
        stream_entry_id_required=True,
        schema_version_required=True,
        ordering_scope="call_id",
        write_dedup_required=True,
        apply_dedup_required=True,
        replay_required=True,
        replay_source="authoritative_durable_stream",
        reconciliation_role="authoritative_session_lifecycle_transition",
        retention_policy="bounded_session_window",
        retention_window_hours=72,
    ),
}


def validate_signaling_durable_event_model_baseline_contract() -> list[str]:
    errors: list[str] = []

    from app.signaling_event_inventory_baseline import SIGNALING_EVENT_INVENTORY_BASELINE

    required_identity_contract = {
        "event_id_required": True,
        "event_id_semantics": "domain_stable_idempotency_identity",
        "stream_entry_id_required": True,
        "stream_entry_semantics": "durable_log_position",
        "schema_version_required": True,
        "issued_at_source": "backend_clock",
    }
    if DURABLE_EVENT_IDENTITY_CONTRACT != required_identity_contract:
        errors.append("DURABLE_EVENT_IDENTITY_CONTRACT must match baseline identity contract")

    required_ordering_contract = {
        "ordering_scope_required": True,
        "ordering_scoped_only": True,
        "cross_scope_global_order_guaranteed": False,
    }
    if ORDERING_CONTRACT != required_ordering_contract:
        errors.append("ORDERING_CONTRACT must match baseline ordering contract")

    required_dedup_contract = {
        "write_side_dedup_required": True,
        "apply_side_dedup_required": True,
        "idempotent_apply_by_event_id": True,
    }
    if DEDUP_CONTRACT != required_dedup_contract:
        errors.append("DEDUP_CONTRACT must match baseline dedup contract")

    required_retention_contract = {
        "bounded_retention_required": True,
        "trim_strategy": "maxlen_or_time_window_policy",
        "minimum_reconciliation_window_hours": 24,
        "trim_must_preserve_reconciliation_window": True,
    }
    if RETENTION_CONTRACT != required_retention_contract:
        errors.append("RETENTION_CONTRACT must match baseline retention contract")

    required_replay_contract = {
        "replay_source": "authoritative_durable_stream",
        "replay_boundary_required": True,
        "replay_boundary_fields": (
            "last_applied_event_id",
            "last_acknowledged_stream_entry_id",
        ),
        "replay_must_be_idempotent": True,
        "pubsub_hints_not_replay_source": True,
    }
    if REPLAY_CONTRACT != required_replay_contract:
        errors.append("REPLAY_CONTRACT must match baseline replay contract")

    required_reconciliation_contract = {
        "startup_reconciliation_uses_authoritative_durable_events": True,
        "reconnect_reconciliation_uses_authoritative_durable_events": True,
        "discard_stale_local_assumptions": True,
        "projection_state_rebuildable_from_authoritative_durable_events": True,
        "ephemeral_hints_not_required_for_correctness": True,
    }
    if RECONCILIATION_CONTRACT != required_reconciliation_contract:
        errors.append("RECONCILIATION_CONTRACT must match baseline reconciliation contract")

    required_invariants = {
        "authoritative_events_have_dual_identity": True,
        "scoped_ordering_only": True,
        "authoritative_apply_idempotent": True,
        "authoritative_stream_replay_required": True,
        "bounded_retention_reconciliation_safe": True,
        "projection_not_source_of_truth": True,
        "pubsub_not_correctness_critical": True,
        "production_path_switch_allowed": False,
    }
    if DURABLE_EVENT_MODEL_INVARIANTS != required_invariants:
        errors.append("DURABLE_EVENT_MODEL_INVARIANTS must match baseline invariant set")

    authoritative_inventory_events = {
        event_name
        for event_name, event_spec in SIGNALING_EVENT_INVENTORY_BASELINE.items()
        if event_spec.event_class == "authoritative_durable_coordination_events"
    }
    durable_model_events = set(DURABLE_AUTHORITATIVE_EVENT_MODEL_BASELINE.keys())
    if durable_model_events != authoritative_inventory_events:
        errors.append("DURABLE_AUTHORITATIVE_EVENT_MODEL_BASELINE must cover all authoritative inventory events from Step 22.2")

    min_reconciliation_hours = RETENTION_CONTRACT["minimum_reconciliation_window_hours"]
    for event_name, model in DURABLE_AUTHORITATIVE_EVENT_MODEL_BASELINE.items():
        if model.event_name != event_name:
            errors.append(f"{event_name}: event_name field must match dictionary key")

        if model.ordering_scope not in ORDERING_SCOPES:
            errors.append(f"{event_name}: unsupported ordering_scope: {model.ordering_scope}")

        if model.replay_source not in REPLAY_SOURCES:
            errors.append(f"{event_name}: unsupported replay_source: {model.replay_source}")

        if model.reconciliation_role not in RECONCILIATION_ROLES:
            errors.append(f"{event_name}: unsupported reconciliation_role: {model.reconciliation_role}")

        if model.retention_policy not in RETENTION_POLICIES:
            errors.append(f"{event_name}: unsupported retention_policy: {model.retention_policy}")

        if not model.event_id_required:
            errors.append(f"{event_name}: event_id_required must be true")
        if not model.stream_entry_id_required:
            errors.append(f"{event_name}: stream_entry_id_required must be true")
        if not model.schema_version_required:
            errors.append(f"{event_name}: schema_version_required must be true")
        if not model.write_dedup_required:
            errors.append(f"{event_name}: write_dedup_required must be true")
        if not model.apply_dedup_required:
            errors.append(f"{event_name}: apply_dedup_required must be true")
        if not model.replay_required:
            errors.append(f"{event_name}: replay_required must be true")
        if model.retention_window_hours < min_reconciliation_hours:
            errors.append(
                f"{event_name}: retention_window_hours must be >= minimum reconciliation window ({min_reconciliation_hours})"
            )

        inventory_spec = SIGNALING_EVENT_INVENTORY_BASELINE[event_name]
        if inventory_spec.ordering_scope != model.ordering_scope:
            errors.append(
                f"{event_name}: ordering_scope must match Step 22.2 inventory ({inventory_spec.ordering_scope})"
            )
        if inventory_spec.event_class != "authoritative_durable_coordination_events":
            errors.append(f"{event_name}: Step 22.2 class must remain authoritative durable")

    return errors

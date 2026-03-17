from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalingEventInventorySpec:
    event_name: str
    event_class: str
    owner: str
    ordering_scope: str
    source_of_truth_relation: str
    loss_tolerance: str
    replay_required: bool
    dedup_required: bool
    negotiation_critical: bool


EVENT_CLASSES = {
    "authoritative_durable_coordination_events",
    "ephemeral_fanout_hints",
    "derived_projection_events",
}

ORDERING_SCOPES = {"call_id", "participant_id", "service"}

SOURCE_OF_TRUTH_RELATIONS = {
    "canonical_coordination_event",
    "fanout_acceleration_hint",
    "derived_from_authoritative_state",
}

LOSS_TOLERANCE_LEVELS = {
    "loss_breaks_correctness",
    "loss_tolerated_convergence_required",
    "loss_tolerated_recomputable",
}


SIGNALING_EVENT_INVENTORY_BASELINE: dict[str, SignalingEventInventorySpec] = {
    "session.created": SignalingEventInventorySpec(
        event_name="session.created",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=False,
    ),
    "session.join-requested": SignalingEventInventorySpec(
        event_name="session.join-requested",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=False,
    ),
    "session.join-accepted": SignalingEventInventorySpec(
        event_name="session.join-accepted",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=False,
    ),
    "session.member-added": SignalingEventInventorySpec(
        event_name="session.member-added",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=False,
    ),
    "session.member-removed": SignalingEventInventorySpec(
        event_name="session.member-removed",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=False,
    ),
    "negotiation.offer-created": SignalingEventInventorySpec(
        event_name="negotiation.offer-created",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=True,
    ),
    "negotiation.offer-rolled-back": SignalingEventInventorySpec(
        event_name="negotiation.offer-rolled-back",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=True,
    ),
    "negotiation.answer-committed": SignalingEventInventorySpec(
        event_name="negotiation.answer-committed",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=True,
    ),
    "negotiation.ice-epoch-started": SignalingEventInventorySpec(
        event_name="negotiation.ice-epoch-started",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=True,
    ),
    "call.terminated": SignalingEventInventorySpec(
        event_name="call.terminated",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=False,
    ),
    "session.authoritative-state-changed": SignalingEventInventorySpec(
        event_name="session.authoritative-state-changed",
        event_class="authoritative_durable_coordination_events",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="canonical_coordination_event",
        loss_tolerance="loss_breaks_correctness",
        replay_required=True,
        dedup_required=True,
        negotiation_critical=False,
    ),
    "hint.new-authoritative-event": SignalingEventInventorySpec(
        event_name="hint.new-authoritative-event",
        event_class="ephemeral_fanout_hints",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="fanout_acceleration_hint",
        loss_tolerance="loss_tolerated_convergence_required",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "hint.peer-resync": SignalingEventInventorySpec(
        event_name="hint.peer-resync",
        event_class="ephemeral_fanout_hints",
        owner="signaling_runtime",
        ordering_scope="participant_id",
        source_of_truth_relation="fanout_acceleration_hint",
        loss_tolerance="loss_tolerated_convergence_required",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "hint.presence-ping": SignalingEventInventorySpec(
        event_name="hint.presence-ping",
        event_class="ephemeral_fanout_hints",
        owner="presence_runtime",
        ordering_scope="participant_id",
        source_of_truth_relation="fanout_acceleration_hint",
        loss_tolerance="loss_tolerated_convergence_required",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "hint.instance-sync-nudge": SignalingEventInventorySpec(
        event_name="hint.instance-sync-nudge",
        event_class="ephemeral_fanout_hints",
        owner="runtime_coordination",
        ordering_scope="service",
        source_of_truth_relation="fanout_acceleration_hint",
        loss_tolerance="loss_tolerated_convergence_required",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "hint.candidate-available": SignalingEventInventorySpec(
        event_name="hint.candidate-available",
        event_class="ephemeral_fanout_hints",
        owner="signaling_runtime",
        ordering_scope="call_id",
        source_of_truth_relation="fanout_acceleration_hint",
        loss_tolerance="loss_tolerated_convergence_required",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "projection.presence-changed": SignalingEventInventorySpec(
        event_name="projection.presence-changed",
        event_class="derived_projection_events",
        owner="presence_projection",
        ordering_scope="participant_id",
        source_of_truth_relation="derived_from_authoritative_state",
        loss_tolerance="loss_tolerated_recomputable",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "projection.session-changed": SignalingEventInventorySpec(
        event_name="projection.session-changed",
        event_class="derived_projection_events",
        owner="signaling_projection",
        ordering_scope="call_id",
        source_of_truth_relation="derived_from_authoritative_state",
        loss_tolerance="loss_tolerated_recomputable",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "projection.active-call-changed": SignalingEventInventorySpec(
        event_name="projection.active-call-changed",
        event_class="derived_projection_events",
        owner="signaling_projection",
        ordering_scope="call_id",
        source_of_truth_relation="derived_from_authoritative_state",
        loss_tolerance="loss_tolerated_recomputable",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
    "projection.observability-emitted": SignalingEventInventorySpec(
        event_name="projection.observability-emitted",
        event_class="derived_projection_events",
        owner="observability_projection",
        ordering_scope="service",
        source_of_truth_relation="derived_from_authoritative_state",
        loss_tolerance="loss_tolerated_recomputable",
        replay_required=False,
        dedup_required=False,
        negotiation_critical=False,
    ),
}

NEGOTIATION_CRITICAL_EVENTS = {
    "negotiation.offer-created",
    "negotiation.offer-rolled-back",
    "negotiation.answer-committed",
    "negotiation.ice-epoch-started",
}

INVENTORY_CLASSIFICATION_QUESTIONS = (
    "loss_breaks_correctness",
    "requires_replay_after_restart",
    "recomputable_from_canonical_state",
    "is_low_latency_hint_only",
)

SIGNALING_EVENT_INVENTORY_INVARIANTS = {
    "each_event_exactly_one_class": True,
    "no_authoritative_ephemeral_overlap": True,
    "negotiation_critical_events_are_authoritative_durable": True,
    "derived_events_not_source_of_truth": True,
    "ephemeral_hints_not_required_for_correctness": True,
    "pubsub_not_authoritative_for_critical_transitions": True,
    "production_path_switch_allowed": False,
}


def validate_signaling_event_inventory_baseline_contract() -> list[str]:
    errors: list[str] = []

    expected_classes = {
        "authoritative_durable_coordination_events",
        "ephemeral_fanout_hints",
        "derived_projection_events",
    }
    if EVENT_CLASSES != expected_classes:
        errors.append("EVENT_CLASSES must match baseline class set")

    expected_questions = (
        "loss_breaks_correctness",
        "requires_replay_after_restart",
        "recomputable_from_canonical_state",
        "is_low_latency_hint_only",
    )
    if INVENTORY_CLASSIFICATION_QUESTIONS != expected_questions:
        errors.append("INVENTORY_CLASSIFICATION_QUESTIONS must match baseline question set")

    class_counts = {event_class: 0 for event_class in EVENT_CLASSES}

    for event_name, event_spec in SIGNALING_EVENT_INVENTORY_BASELINE.items():
        if event_spec.event_name != event_name:
            errors.append(f"{event_name}: event_name field must match dictionary key")

        if event_spec.event_class not in EVENT_CLASSES:
            errors.append(f"{event_name}: unsupported event_class: {event_spec.event_class}")
            continue

        class_counts[event_spec.event_class] += 1

        if event_spec.ordering_scope not in ORDERING_SCOPES:
            errors.append(f"{event_name}: unsupported ordering_scope: {event_spec.ordering_scope}")

        if event_spec.source_of_truth_relation not in SOURCE_OF_TRUTH_RELATIONS:
            errors.append(
                f"{event_name}: unsupported source_of_truth_relation: {event_spec.source_of_truth_relation}"
            )

        if event_spec.loss_tolerance not in LOSS_TOLERANCE_LEVELS:
            errors.append(f"{event_name}: unsupported loss_tolerance: {event_spec.loss_tolerance}")

        if event_spec.event_class == "authoritative_durable_coordination_events":
            if event_spec.source_of_truth_relation != "canonical_coordination_event":
                errors.append(f"{event_name}: authoritative event must be canonical_coordination_event")
            if event_spec.loss_tolerance != "loss_breaks_correctness":
                errors.append(f"{event_name}: authoritative event must use loss_breaks_correctness")
            if not event_spec.replay_required:
                errors.append(f"{event_name}: authoritative event must require replay")
            if not event_spec.dedup_required:
                errors.append(f"{event_name}: authoritative event must require dedup")

        if event_spec.event_class == "ephemeral_fanout_hints":
            if event_spec.source_of_truth_relation != "fanout_acceleration_hint":
                errors.append(f"{event_name}: hint must use fanout_acceleration_hint relation")
            if event_spec.loss_tolerance != "loss_tolerated_convergence_required":
                errors.append(f"{event_name}: hint must use loss_tolerated_convergence_required")
            if event_spec.replay_required:
                errors.append(f"{event_name}: hint must not require replay")

        if event_spec.event_class == "derived_projection_events":
            if event_spec.source_of_truth_relation != "derived_from_authoritative_state":
                errors.append(f"{event_name}: projection must be derived_from_authoritative_state")
            if event_spec.loss_tolerance != "loss_tolerated_recomputable":
                errors.append(f"{event_name}: projection must use loss_tolerated_recomputable")
            if event_spec.replay_required:
                errors.append(f"{event_name}: projection must not require replay")
            if event_spec.dedup_required:
                errors.append(f"{event_name}: projection must not require dedup")

    for event_class, count in class_counts.items():
        if count == 0:
            errors.append(f"{event_class}: class must contain at least one inventory event")

    for event_name in NEGOTIATION_CRITICAL_EVENTS:
        event_spec = SIGNALING_EVENT_INVENTORY_BASELINE.get(event_name)
        if event_spec is None:
            errors.append(f"{event_name}: missing negotiation-critical event from inventory")
            continue
        if event_spec.event_class != "authoritative_durable_coordination_events":
            errors.append(f"{event_name}: negotiation-critical event must be authoritative durable")
        if not event_spec.negotiation_critical:
            errors.append(f"{event_name}: negotiation-critical flag must be true")

    for event_name, event_spec in SIGNALING_EVENT_INVENTORY_BASELINE.items():
        if event_spec.negotiation_critical and event_name not in NEGOTIATION_CRITICAL_EVENTS:
            errors.append(
                f"{event_name}: negotiation_critical=true only allowed for NEGOTIATION_CRITICAL_EVENTS members"
            )

    expected_invariants = {
        "each_event_exactly_one_class": True,
        "no_authoritative_ephemeral_overlap": True,
        "negotiation_critical_events_are_authoritative_durable": True,
        "derived_events_not_source_of_truth": True,
        "ephemeral_hints_not_required_for_correctness": True,
        "pubsub_not_authoritative_for_critical_transitions": True,
        "production_path_switch_allowed": False,
    }
    if SIGNALING_EVENT_INVENTORY_INVARIANTS != expected_invariants:
        errors.append("SIGNALING_EVENT_INVENTORY_INVARIANTS must match baseline invariant set")

    return errors

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalingDeliveryEventSpec:
    event_name: str
    event_class: str
    authoritative: bool
    replay_required: bool
    ordering_scope: str
    dedup_required: bool
    retention_class: str


EVENT_CLASSES = {
    "authoritative_durable_coordination_events",
    "ephemeral_fanout_hints",
    "derived_projection_events",
}

ORDERING_SCOPES = {"call_id", "nickname", "service"}
RETENTION_CLASSES = {"short", "medium", "derived"}

DURABLE_TRANSPORT_BASELINE = {
    "preferred_model": "redis_streams_or_equivalent_append_only_log",
    "pubsub_role": "best_effort_fanout_hint",
    "production_cutover_in_step_22_1": False,
}

SIGNALING_DELIVERY_EVENT_INVENTORY_BASELINE: dict[str, SignalingDeliveryEventSpec] = {
    "call.invite": SignalingDeliveryEventSpec(
        event_name="call.invite",
        event_class="authoritative_durable_coordination_events",
        authoritative=True,
        replay_required=True,
        ordering_scope="call_id",
        dedup_required=True,
        retention_class="medium",
    ),
    "call.accept": SignalingDeliveryEventSpec(
        event_name="call.accept",
        event_class="authoritative_durable_coordination_events",
        authoritative=True,
        replay_required=True,
        ordering_scope="call_id",
        dedup_required=True,
        retention_class="medium",
    ),
    "call.reject": SignalingDeliveryEventSpec(
        event_name="call.reject",
        event_class="authoritative_durable_coordination_events",
        authoritative=True,
        replay_required=True,
        ordering_scope="call_id",
        dedup_required=True,
        retention_class="medium",
    ),
    "call.cancel": SignalingDeliveryEventSpec(
        event_name="call.cancel",
        event_class="authoritative_durable_coordination_events",
        authoritative=True,
        replay_required=True,
        ordering_scope="call_id",
        dedup_required=True,
        retention_class="medium",
    ),
    "call.hangup": SignalingDeliveryEventSpec(
        event_name="call.hangup",
        event_class="authoritative_durable_coordination_events",
        authoritative=True,
        replay_required=True,
        ordering_scope="call_id",
        dedup_required=True,
        retention_class="medium",
    ),
    "call.ringing": SignalingDeliveryEventSpec(
        event_name="call.ringing",
        event_class="ephemeral_fanout_hints",
        authoritative=False,
        replay_required=False,
        ordering_scope="call_id",
        dedup_required=False,
        retention_class="short",
    ),
    "webrtc.offer": SignalingDeliveryEventSpec(
        event_name="webrtc.offer",
        event_class="ephemeral_fanout_hints",
        authoritative=False,
        replay_required=False,
        ordering_scope="call_id",
        dedup_required=False,
        retention_class="short",
    ),
    "webrtc.answer": SignalingDeliveryEventSpec(
        event_name="webrtc.answer",
        event_class="ephemeral_fanout_hints",
        authoritative=False,
        replay_required=False,
        ordering_scope="call_id",
        dedup_required=False,
        retention_class="short",
    ),
    "webrtc.ice-candidate": SignalingDeliveryEventSpec(
        event_name="webrtc.ice-candidate",
        event_class="ephemeral_fanout_hints",
        authoritative=False,
        replay_required=False,
        ordering_scope="call_id",
        dedup_required=False,
        retention_class="short",
    ),
    "webrtc.ice-restart": SignalingDeliveryEventSpec(
        event_name="webrtc.ice-restart",
        event_class="ephemeral_fanout_hints",
        authoritative=False,
        replay_required=False,
        ordering_scope="call_id",
        dedup_required=False,
        retention_class="short",
    ),
    "presence.snapshot": SignalingDeliveryEventSpec(
        event_name="presence.snapshot",
        event_class="derived_projection_events",
        authoritative=False,
        replay_required=False,
        ordering_scope="nickname",
        dedup_required=False,
        retention_class="derived",
    ),
    "session.snapshot": SignalingDeliveryEventSpec(
        event_name="session.snapshot",
        event_class="derived_projection_events",
        authoritative=False,
        replay_required=False,
        ordering_scope="call_id",
        dedup_required=False,
        retention_class="derived",
    ),
}

SIGNALING_DELIVERY_HARDENING_INVARIANTS = {
    "no_correctness_dependency_on_pubsub_only": True,
    "critical_events_replayable_or_reconstructable": True,
    "reconnect_reconciliation_valid_if_fanout_lost": True,
    "presence_is_derived_not_canonical": True,
    "retention_is_bounded": True,
    "production_path_switch_allowed": False,
}

STAGE22_SUBSTEP_DRAFT = {
    "22.1": "baseline_definition",
    "22.2": "event_inventory_boundary",
    "22.3": "durable_event_model",
    "22.4": "sandbox_durable_signaling_smoke",
    "22.5": "ci_durable_signaling_simulation_gate",
}


def validate_signaling_delivery_hardening_baseline_contract() -> list[str]:
    errors: list[str] = []

    if set(EVENT_CLASSES) != {
        "authoritative_durable_coordination_events",
        "ephemeral_fanout_hints",
        "derived_projection_events",
    }:
        errors.append("EVENT_CLASSES must match baseline class set")

    if DURABLE_TRANSPORT_BASELINE.get("preferred_model") != "redis_streams_or_equivalent_append_only_log":
        errors.append("DURABLE_TRANSPORT_BASELINE.preferred_model must target append-only durable log model")

    if DURABLE_TRANSPORT_BASELINE.get("pubsub_role") != "best_effort_fanout_hint":
        errors.append("DURABLE_TRANSPORT_BASELINE.pubsub_role must be best_effort_fanout_hint")

    if DURABLE_TRANSPORT_BASELINE.get("production_cutover_in_step_22_1") is not False:
        errors.append("Step 22.1 must not enable production cutover")

    expected_inventory_events = {
        "call.invite",
        "call.accept",
        "call.reject",
        "call.cancel",
        "call.hangup",
        "call.ringing",
        "webrtc.offer",
        "webrtc.answer",
        "webrtc.ice-candidate",
        "webrtc.ice-restart",
        "presence.snapshot",
        "session.snapshot",
    }
    if set(SIGNALING_DELIVERY_EVENT_INVENTORY_BASELINE.keys()) != expected_inventory_events:
        errors.append("SIGNALING_DELIVERY_EVENT_INVENTORY_BASELINE must contain complete event inventory")

    for event_name, event_spec in SIGNALING_DELIVERY_EVENT_INVENTORY_BASELINE.items():
        if event_spec.event_name != event_name:
            errors.append(f"{event_name}: event_name field must match dictionary key")
        if event_spec.event_class not in EVENT_CLASSES:
            errors.append(f"{event_name}: unsupported event_class: {event_spec.event_class}")
        if event_spec.ordering_scope not in ORDERING_SCOPES:
            errors.append(f"{event_name}: unsupported ordering_scope: {event_spec.ordering_scope}")
        if event_spec.retention_class not in RETENTION_CLASSES:
            errors.append(f"{event_name}: unsupported retention_class: {event_spec.retention_class}")

        if event_spec.event_class == "authoritative_durable_coordination_events":
            if not event_spec.authoritative:
                errors.append(f"{event_name}: authoritative durable event must be authoritative=true")
            if not event_spec.replay_required:
                errors.append(f"{event_name}: authoritative durable event must require replay")
            if not event_spec.dedup_required:
                errors.append(f"{event_name}: authoritative durable event must require dedup")

        if event_spec.event_class == "ephemeral_fanout_hints":
            if event_spec.authoritative:
                errors.append(f"{event_name}: ephemeral fan-out hint must be authoritative=false")
            if event_spec.replay_required:
                errors.append(f"{event_name}: ephemeral fan-out hint must not require replay")

        if event_spec.event_class == "derived_projection_events":
            if event_spec.authoritative:
                errors.append(f"{event_name}: derived projection must be authoritative=false")
            if event_spec.replay_required:
                errors.append(f"{event_name}: derived projection must not require replay")
            if event_spec.retention_class != "derived":
                errors.append(f"{event_name}: derived projection must use retention_class=derived")

    required_invariants = {
        "no_correctness_dependency_on_pubsub_only": True,
        "critical_events_replayable_or_reconstructable": True,
        "reconnect_reconciliation_valid_if_fanout_lost": True,
        "presence_is_derived_not_canonical": True,
        "retention_is_bounded": True,
        "production_path_switch_allowed": False,
    }
    if SIGNALING_DELIVERY_HARDENING_INVARIANTS != required_invariants:
        errors.append("SIGNALING_DELIVERY_HARDENING_INVARIANTS must match baseline invariant set")

    expected_stage_draft = {
        "22.1": "baseline_definition",
        "22.2": "event_inventory_boundary",
        "22.3": "durable_event_model",
        "22.4": "sandbox_durable_signaling_smoke",
        "22.5": "ci_durable_signaling_simulation_gate",
    }
    if STAGE22_SUBSTEP_DRAFT != expected_stage_draft:
        errors.append("STAGE22_SUBSTEP_DRAFT must match baseline stage draft")

    return errors

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthoritativeRuntimeTransitionSpec:
    transition_id: str
    event_name: str
    event_class: str
    scope: str
    producer: str
    apply_owner: str
    legacy_delivery_path: str
    target_delivery_path: str
    lost_live_delivery_allowed: bool
    replay_required: bool
    dedup_required: bool
    rollback_allowed_until: str
    projection_dependency: str
    reconciliation_role: str


@dataclass(frozen=True)
class TransitionModeMatrixSpec:
    mode_name: str
    writer_path: str
    reader_path: str
    shadow_read_equivalence_required: bool
    rollback_target_mode: str | None


VALID_SCOPES = {"call_id", "participant_id", "service"}
VALID_PRODUCERS = {
    "ws_signaling_handler",
    "session_lifecycle_handler",
    "runtime_reconciliation_worker",
}
VALID_APPLY_OWNERS = {"authoritative_state_machine"}
VALID_DELIVERY_PATHS = {
    "pubsub_live_only",
    "pubsub_live_plus_stream_shadow",
    "durable_stream_primary",
    "durable_stream_primary_with_pubsub_hint",
}
VALID_ROLLBACK_BOUNDARIES = {
    "before_shadow_read_equivalence",
    "before_durable_primary_activation",
}
VALID_PROJECTION_DEPENDENCIES = {"required_after_authoritative_apply"}
VALID_RECONCILIATION_ROLES = {
    "startup_reconciliation",
    "reconnect_reconciliation",
}
ROLLOUT_MODES = ("pubsub_legacy", "dual_write_shadow", "durable_authoritative")

READ_WRITE_OWNERSHIP_BOUNDARIES = {
    "authoritative_append_owner": "authoritative_transition_writer",
    "authoritative_stream_read_owner": "authoritative_transition_reader",
    "authoritative_apply_owner": "authoritative_state_machine",
    "pubsub_hint_owner": "fanout_hint_dispatcher",
    "projection_owner": "projection_builder",
}

CUTOVER_SAFETY_RULES = {
    "durable_authoritative_requires_step22_3_contract": True,
    "dual_write_requires_shadow_read_equivalence": True,
    "rollback_must_preserve_committed_authoritative_state": True,
    "per_transition_feature_flag_deterministic": True,
    "build_check_no_production_secret_dependency": True,
}

RUNTIME_PATH_INVENTORY_INVARIANTS = {
    "authoritative_transitions_replay_required": True,
    "authoritative_transitions_dedup_required": True,
    "lost_live_delivery_allowed_with_replay_path": True,
    "non_authoritative_excluded_from_authoritative_matrix": True,
    "step23_1_mode_consistency_required": True,
    "production_runtime_cutover_allowed": False,
}


def _producer_for_event(event_name: str) -> str:
    if event_name.startswith("negotiation."):
        return "ws_signaling_handler"
    if event_name.startswith("session.") or event_name.startswith("call."):
        return "session_lifecycle_handler"
    return "runtime_reconciliation_worker"


def _reconciliation_role_for_event(event_name: str) -> str:
    if event_name.startswith("negotiation."):
        return "reconnect_reconciliation"
    return "startup_reconciliation"


def _build_authoritative_transition_inventory() -> dict[str, AuthoritativeRuntimeTransitionSpec]:
    from app.signaling_event_inventory_baseline import SIGNALING_EVENT_INVENTORY_BASELINE

    inventory: dict[str, AuthoritativeRuntimeTransitionSpec] = {}
    for event_name, event_spec in SIGNALING_EVENT_INVENTORY_BASELINE.items():
        if event_spec.event_class != "authoritative_durable_coordination_events":
            continue
        transition_id = f"transition.{event_name}"
        inventory[transition_id] = AuthoritativeRuntimeTransitionSpec(
            transition_id=transition_id,
            event_name=event_name,
            event_class=event_spec.event_class,
            scope=event_spec.ordering_scope,
            producer=_producer_for_event(event_name),
            apply_owner="authoritative_state_machine",
            legacy_delivery_path="pubsub_live_only",
            target_delivery_path="durable_stream_primary_with_pubsub_hint",
            lost_live_delivery_allowed=True,
            replay_required=True,
            dedup_required=True,
            rollback_allowed_until=(
                "before_durable_primary_activation"
                if event_name.startswith("negotiation.")
                else "before_shadow_read_equivalence"
            ),
            projection_dependency="required_after_authoritative_apply",
            reconciliation_role=_reconciliation_role_for_event(event_name),
        )
    return inventory


def _build_transition_mode_matrix() -> dict[str, dict[str, TransitionModeMatrixSpec]]:
    matrix: dict[str, dict[str, TransitionModeMatrixSpec]] = {}
    for transition_id in AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE.keys():
        matrix[transition_id] = {
            "pubsub_legacy": TransitionModeMatrixSpec(
                mode_name="pubsub_legacy",
                writer_path="pubsub_live_only",
                reader_path="pubsub_live_only",
                shadow_read_equivalence_required=False,
                rollback_target_mode=None,
            ),
            "dual_write_shadow": TransitionModeMatrixSpec(
                mode_name="dual_write_shadow",
                writer_path="pubsub_live_plus_stream_shadow",
                reader_path="pubsub_live_only",
                shadow_read_equivalence_required=True,
                rollback_target_mode="pubsub_legacy",
            ),
            "durable_authoritative": TransitionModeMatrixSpec(
                mode_name="durable_authoritative",
                writer_path="durable_stream_primary",
                reader_path="durable_stream_primary_with_pubsub_hint",
                shadow_read_equivalence_required=False,
                rollback_target_mode="dual_write_shadow",
            ),
        }
    return matrix


AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE = _build_authoritative_transition_inventory()
TRANSITION_MIGRATION_MATRIX_BASELINE = _build_transition_mode_matrix()


def validate_durable_signaling_runtime_path_inventory_contract() -> list[str]:
    errors: list[str] = []

    from app.durable_signaling_runtime_cutover_baseline import (
        EVENT_MIGRATION_MATRIX_BASELINE,
        RUNTIME_CUTOVER_MODE_CONTRACT,
    )
    from app.signaling_event_inventory_baseline import SIGNALING_EVENT_INVENTORY_BASELINE

    authoritative_events = {
        event_name
        for event_name, event_spec in SIGNALING_EVENT_INVENTORY_BASELINE.items()
        if event_spec.event_class == "authoritative_durable_coordination_events"
    }
    expected_transition_ids = {f"transition.{event_name}" for event_name in authoritative_events}
    if set(AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE.keys()) != expected_transition_ids:
        errors.append("AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE must cover all authoritative events")

    if set(TRANSITION_MIGRATION_MATRIX_BASELINE.keys()) != expected_transition_ids:
        errors.append("TRANSITION_MIGRATION_MATRIX_BASELINE must cover all authoritative transitions")

    for transition_id, transition in AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE.items():
        event_name = transition.event_name
        inventory_event = SIGNALING_EVENT_INVENTORY_BASELINE.get(event_name)
        if inventory_event is None:
            errors.append(f"{transition_id}: event_name not found in Step 22.2 inventory")
            continue
        if transition.transition_id != transition_id:
            errors.append(f"{transition_id}: transition_id field must match dictionary key")
        if transition.event_class != "authoritative_durable_coordination_events":
            errors.append(f"{transition_id}: event_class must be authoritative_durable_coordination_events")
        if transition.scope not in VALID_SCOPES:
            errors.append(f"{transition_id}: unsupported scope: {transition.scope}")
        if transition.scope != inventory_event.ordering_scope:
            errors.append(
                f"{transition_id}: scope must match Step 22.2 ordering_scope ({inventory_event.ordering_scope})"
            )
        if transition.producer not in VALID_PRODUCERS:
            errors.append(f"{transition_id}: unsupported producer: {transition.producer}")
        if transition.apply_owner not in VALID_APPLY_OWNERS:
            errors.append(f"{transition_id}: unsupported apply_owner: {transition.apply_owner}")
        if transition.legacy_delivery_path not in VALID_DELIVERY_PATHS:
            errors.append(
                f"{transition_id}: unsupported legacy_delivery_path: {transition.legacy_delivery_path}"
            )
        if transition.target_delivery_path not in VALID_DELIVERY_PATHS:
            errors.append(
                f"{transition_id}: unsupported target_delivery_path: {transition.target_delivery_path}"
            )
        if transition.rollback_allowed_until not in VALID_ROLLBACK_BOUNDARIES:
            errors.append(
                f"{transition_id}: unsupported rollback_allowed_until: {transition.rollback_allowed_until}"
            )
        if transition.projection_dependency not in VALID_PROJECTION_DEPENDENCIES:
            errors.append(
                f"{transition_id}: unsupported projection_dependency: {transition.projection_dependency}"
            )
        if transition.reconciliation_role not in VALID_RECONCILIATION_ROLES:
            errors.append(
                f"{transition_id}: unsupported reconciliation_role: {transition.reconciliation_role}"
            )
        if not transition.lost_live_delivery_allowed:
            errors.append(f"{transition_id}: lost_live_delivery_allowed must be true")
        if not transition.replay_required:
            errors.append(f"{transition_id}: replay_required must be true")
        if not transition.dedup_required:
            errors.append(f"{transition_id}: dedup_required must be true")

        mode_matrix = TRANSITION_MIGRATION_MATRIX_BASELINE.get(transition_id)
        if mode_matrix is None:
            errors.append(f"{transition_id}: missing mode matrix")
            continue
        if set(mode_matrix.keys()) != set(ROLLOUT_MODES):
            errors.append(f"{transition_id}: mode matrix must contain pubsub_legacy/dual_write_shadow/durable_authoritative")
            continue

        for mode_name, mode_spec in mode_matrix.items():
            if mode_spec.mode_name != mode_name:
                errors.append(f"{transition_id}:{mode_name}: mode_name field must match dictionary key")

        legacy_mode = mode_matrix["pubsub_legacy"]
        if legacy_mode.writer_path != "pubsub_live_only" or legacy_mode.reader_path != "pubsub_live_only":
            errors.append(f"{transition_id}: pubsub_legacy mode paths must be pubsub_live_only")
        if legacy_mode.shadow_read_equivalence_required:
            errors.append(f"{transition_id}: pubsub_legacy must not require shadow_read_equivalence")
        if legacy_mode.rollback_target_mode is not None:
            errors.append(f"{transition_id}: pubsub_legacy rollback_target_mode must be null")

        shadow_mode = mode_matrix["dual_write_shadow"]
        if shadow_mode.writer_path != "pubsub_live_plus_stream_shadow":
            errors.append(f"{transition_id}: dual_write_shadow writer_path must be pubsub_live_plus_stream_shadow")
        if shadow_mode.reader_path != "pubsub_live_only":
            errors.append(f"{transition_id}: dual_write_shadow reader_path must remain pubsub_live_only")
        if not shadow_mode.shadow_read_equivalence_required:
            errors.append(f"{transition_id}: dual_write_shadow must require shadow_read_equivalence")
        if shadow_mode.rollback_target_mode != "pubsub_legacy":
            errors.append(f"{transition_id}: dual_write_shadow rollback_target_mode must be pubsub_legacy")

        durable_mode = mode_matrix["durable_authoritative"]
        if durable_mode.writer_path != "durable_stream_primary":
            errors.append(f"{transition_id}: durable_authoritative writer_path must be durable_stream_primary")
        if durable_mode.reader_path != "durable_stream_primary_with_pubsub_hint":
            errors.append(
                f"{transition_id}: durable_authoritative reader_path must be durable_stream_primary_with_pubsub_hint"
            )
        if durable_mode.shadow_read_equivalence_required:
            errors.append(f"{transition_id}: durable_authoritative must not require shadow_read_equivalence")
        if durable_mode.rollback_target_mode != "dual_write_shadow":
            errors.append(f"{transition_id}: durable_authoritative rollback_target_mode must be dual_write_shadow")

        step23_1_migration = EVENT_MIGRATION_MATRIX_BASELINE.get(event_name)
        if step23_1_migration is None:
            errors.append(f"{transition_id}: missing Step 23.1 migration mapping for event")
        else:
            if step23_1_migration.target_mode != "durable_authoritative":
                errors.append(f"{transition_id}: Step 23.1 target_mode must be durable_authoritative")
            if not step23_1_migration.dual_write_shadow_required:
                errors.append(f"{transition_id}: Step 23.1 dual_write_shadow_required must be true")
            if step23_1_migration.rollback_mode != "dual_write_shadow":
                errors.append(f"{transition_id}: Step 23.1 rollback_mode must be dual_write_shadow")

    required_ownership = {
        "authoritative_append_owner": "authoritative_transition_writer",
        "authoritative_stream_read_owner": "authoritative_transition_reader",
        "authoritative_apply_owner": "authoritative_state_machine",
        "pubsub_hint_owner": "fanout_hint_dispatcher",
        "projection_owner": "projection_builder",
    }
    if READ_WRITE_OWNERSHIP_BOUNDARIES != required_ownership:
        errors.append("READ_WRITE_OWNERSHIP_BOUNDARIES must match baseline ownership contract")

    required_safety = {
        "durable_authoritative_requires_step22_3_contract": True,
        "dual_write_requires_shadow_read_equivalence": True,
        "rollback_must_preserve_committed_authoritative_state": True,
        "per_transition_feature_flag_deterministic": True,
        "build_check_no_production_secret_dependency": True,
    }
    if CUTOVER_SAFETY_RULES != required_safety:
        errors.append("CUTOVER_SAFETY_RULES must match baseline safety set")

    required_invariants = {
        "authoritative_transitions_replay_required": True,
        "authoritative_transitions_dedup_required": True,
        "lost_live_delivery_allowed_with_replay_path": True,
        "non_authoritative_excluded_from_authoritative_matrix": True,
        "step23_1_mode_consistency_required": True,
        "production_runtime_cutover_allowed": False,
    }
    if RUNTIME_PATH_INVENTORY_INVARIANTS != required_invariants:
        errors.append("RUNTIME_PATH_INVENTORY_INVARIANTS must match baseline invariant set")

    if set(RUNTIME_CUTOVER_MODE_CONTRACT.keys()) != set(ROLLOUT_MODES):
        errors.append("Step 23.1 rollout modes must remain consistent with Step 23.2")

    return errors

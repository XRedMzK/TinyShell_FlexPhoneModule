from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DualWriteShadowTransitionContractSpec:
    transition_id: str
    event_name: str
    mode_name: str
    write_order: tuple[str, str]
    primary_truth_source: str
    shadow_read_role: str
    success_requires_legacy_publish: bool
    success_requires_durable_append: bool
    equivalence_dimensions: tuple[str, ...]
    mismatch_blocking_classes: tuple[str, ...]
    promotion_gate_required: bool


DUAL_WRITE_MODE_NAME = "dual_write_shadow"
WRITE_ORDER_CANONICAL = ("durable_stream_append", "legacy_pubsub_publish")
WRITE_ORDER_STEPS = set(WRITE_ORDER_CANONICAL)
PRIMARY_TRUTH_SOURCES = {"legacy_primary_apply_path"}
SHADOW_READ_ROLES = {"observer_non_authoritative"}

EQUIVALENCE_DIMENSIONS = (
    "event_identity",
    "ordering_within_scope",
    "apply_terminal_state",
    "dedup_result",
    "reconnect_replay_outcome",
)

MISMATCH_CLASS_ORDER = (
    "legacy_ok_durable_append_fail",
    "durable_ok_legacy_publish_fail",
    "legacy_ok_durable_read_mismatch",
    "legacy_ok_durable_apply_duplicate_mismatch",
    "legacy_ok_shadow_read_timeout",
    "legacy_and_durable_divergent_terminal_state",
)

MISMATCH_CLASS_ACTION_BASELINE = {
    "legacy_ok_durable_append_fail": "block_cutover_progression",
    "durable_ok_legacy_publish_fail": "block_cutover_progression",
    "legacy_ok_durable_read_mismatch": "block_cutover_progression",
    "legacy_ok_durable_apply_duplicate_mismatch": "block_cutover_progression",
    "legacy_ok_shadow_read_timeout": "block_promotion_wait_for_recovery",
    "legacy_and_durable_divergent_terminal_state": "rollback_to_pubsub_legacy",
}

PROMOTION_RULES = {
    "shadow_equivalence_required": True,
    "no_unresolved_mismatch_blockers_required": True,
    "pending_recovery_pass_required": True,
    "replay_reconciliation_pass_required": True,
    "durable_append_success_required": True,
}

ROLLBACK_RULES = {
    "rollback_allowed_from_mode": "dual_write_shadow",
    "rollback_target_mode": "pubsub_legacy",
    "rollback_on_divergent_terminal_state": True,
    "rollback_preserves_committed_authoritative_state": True,
}

DUAL_WRITE_SHADOW_CONTRACT_INVARIANTS = {
    "dual_write_mode_runtime_outcome_primary_source_is_legacy": True,
    "legacy_publish_not_sufficient_without_durable_append": True,
    "shadow_read_observer_only_non_authoritative": True,
    "promotion_requires_semantic_equivalence": True,
    "pubsub_not_authoritative_for_correctness": True,
    "production_path_switch_allowed": False,
}


def _build_dual_write_shadow_transition_contract() -> dict[str, DualWriteShadowTransitionContractSpec]:
    from app.durable_signaling_runtime_path_inventory import (
        AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE,
    )

    contracts: dict[str, DualWriteShadowTransitionContractSpec] = {}
    for transition_id, transition in AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE.items():
        contracts[transition_id] = DualWriteShadowTransitionContractSpec(
            transition_id=transition_id,
            event_name=transition.event_name,
            mode_name=DUAL_WRITE_MODE_NAME,
            write_order=WRITE_ORDER_CANONICAL,
            primary_truth_source="legacy_primary_apply_path",
            shadow_read_role="observer_non_authoritative",
            success_requires_legacy_publish=True,
            success_requires_durable_append=True,
            equivalence_dimensions=EQUIVALENCE_DIMENSIONS,
            mismatch_blocking_classes=MISMATCH_CLASS_ORDER,
            promotion_gate_required=True,
        )
    return contracts


DUAL_WRITE_SHADOW_TRANSITION_CONTRACT_BASELINE = _build_dual_write_shadow_transition_contract()


def validate_durable_signaling_dual_write_shadow_read_contract() -> list[str]:
    errors: list[str] = []

    from app.durable_signaling_runtime_cutover_baseline import EVENT_MIGRATION_MATRIX_BASELINE
    from app.durable_signaling_runtime_path_inventory import (
        AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE,
        TRANSITION_MIGRATION_MATRIX_BASELINE,
    )
    from app.signaling_durable_event_model_baseline import (
        DURABLE_AUTHORITATIVE_EVENT_MODEL_BASELINE,
    )

    expected_transition_ids = set(AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE.keys())
    if set(DUAL_WRITE_SHADOW_TRANSITION_CONTRACT_BASELINE.keys()) != expected_transition_ids:
        errors.append(
            "DUAL_WRITE_SHADOW_TRANSITION_CONTRACT_BASELINE must cover all authoritative runtime transitions"
        )

    for transition_id, contract in DUAL_WRITE_SHADOW_TRANSITION_CONTRACT_BASELINE.items():
        transition = AUTHORITATIVE_RUNTIME_TRANSITION_INVENTORY_BASELINE.get(transition_id)
        if transition is None:
            errors.append(f"{transition_id}: missing Step 23.2 transition inventory mapping")
            continue

        if contract.transition_id != transition_id:
            errors.append(f"{transition_id}: transition_id field must match dictionary key")
        if contract.event_name != transition.event_name:
            errors.append(f"{transition_id}: event_name must match Step 23.2 event_name")
        if contract.mode_name != DUAL_WRITE_MODE_NAME:
            errors.append(f"{transition_id}: mode_name must be dual_write_shadow")
        if contract.write_order != WRITE_ORDER_CANONICAL:
            errors.append(f"{transition_id}: write_order must be {WRITE_ORDER_CANONICAL}")
        if set(contract.write_order) != WRITE_ORDER_STEPS:
            errors.append(f"{transition_id}: write_order must include canonical dual-write steps")
        if contract.primary_truth_source not in PRIMARY_TRUTH_SOURCES:
            errors.append(
                f"{transition_id}: unsupported primary_truth_source: {contract.primary_truth_source}"
            )
        if contract.shadow_read_role not in SHADOW_READ_ROLES:
            errors.append(f"{transition_id}: unsupported shadow_read_role: {contract.shadow_read_role}")
        if not contract.success_requires_legacy_publish:
            errors.append(f"{transition_id}: success_requires_legacy_publish must be true")
        if not contract.success_requires_durable_append:
            errors.append(f"{transition_id}: success_requires_durable_append must be true")
        if contract.equivalence_dimensions != EQUIVALENCE_DIMENSIONS:
            errors.append(f"{transition_id}: equivalence_dimensions must match canonical proof dimensions")
        if contract.mismatch_blocking_classes != MISMATCH_CLASS_ORDER:
            errors.append(f"{transition_id}: mismatch_blocking_classes must match canonical mismatch class order")
        if not contract.promotion_gate_required:
            errors.append(f"{transition_id}: promotion_gate_required must be true")

        mode_matrix = TRANSITION_MIGRATION_MATRIX_BASELINE.get(transition_id)
        if mode_matrix is None:
            errors.append(f"{transition_id}: missing Step 23.2 mode matrix")
            continue
        mode_spec = mode_matrix.get("dual_write_shadow")
        if mode_spec is None:
            errors.append(f"{transition_id}: missing dual_write_shadow mode in Step 23.2 matrix")
            continue
        if mode_spec.writer_path != "pubsub_live_plus_stream_shadow":
            errors.append(f"{transition_id}: Step 23.2 dual_write writer_path must remain pubsub_live_plus_stream_shadow")
        if mode_spec.reader_path != "pubsub_live_only":
            errors.append(f"{transition_id}: Step 23.2 dual_write reader_path must remain pubsub_live_only")
        if not mode_spec.shadow_read_equivalence_required:
            errors.append(f"{transition_id}: Step 23.2 dual_write must require shadow_read_equivalence")
        if mode_spec.rollback_target_mode != "pubsub_legacy":
            errors.append(f"{transition_id}: Step 23.2 dual_write rollback target must be pubsub_legacy")

        event_migration = EVENT_MIGRATION_MATRIX_BASELINE.get(contract.event_name)
        if event_migration is None:
            errors.append(f"{transition_id}: missing Step 23.1 event migration mapping")
            continue
        if event_migration.target_mode != "durable_authoritative":
            errors.append(f"{transition_id}: Step 23.1 target_mode must be durable_authoritative")
        if not event_migration.dual_write_shadow_required:
            errors.append(f"{transition_id}: Step 23.1 dual_write_shadow_required must be true")
        if event_migration.rollback_mode != "dual_write_shadow":
            errors.append(f"{transition_id}: Step 23.1 rollback_mode must be dual_write_shadow")

        durable_model = DURABLE_AUTHORITATIVE_EVENT_MODEL_BASELINE.get(contract.event_name)
        if durable_model is None:
            errors.append(f"{transition_id}: missing Step 22.3 durable event model")
            continue
        if not durable_model.replay_required:
            errors.append(f"{transition_id}: Step 22.3 durable model must require replay")
        if not durable_model.apply_dedup_required:
            errors.append(f"{transition_id}: Step 22.3 durable model must require apply dedup")
        if not durable_model.write_dedup_required:
            errors.append(f"{transition_id}: Step 22.3 durable model must require write dedup")

    required_mismatch_actions = {
        "legacy_ok_durable_append_fail": "block_cutover_progression",
        "durable_ok_legacy_publish_fail": "block_cutover_progression",
        "legacy_ok_durable_read_mismatch": "block_cutover_progression",
        "legacy_ok_durable_apply_duplicate_mismatch": "block_cutover_progression",
        "legacy_ok_shadow_read_timeout": "block_promotion_wait_for_recovery",
        "legacy_and_durable_divergent_terminal_state": "rollback_to_pubsub_legacy",
    }
    if MISMATCH_CLASS_ACTION_BASELINE != required_mismatch_actions:
        errors.append("MISMATCH_CLASS_ACTION_BASELINE must match canonical mismatch action mapping")

    required_promotion_rules = {
        "shadow_equivalence_required": True,
        "no_unresolved_mismatch_blockers_required": True,
        "pending_recovery_pass_required": True,
        "replay_reconciliation_pass_required": True,
        "durable_append_success_required": True,
    }
    if PROMOTION_RULES != required_promotion_rules:
        errors.append("PROMOTION_RULES must match canonical promotion gate rules")

    required_rollback_rules = {
        "rollback_allowed_from_mode": "dual_write_shadow",
        "rollback_target_mode": "pubsub_legacy",
        "rollback_on_divergent_terminal_state": True,
        "rollback_preserves_committed_authoritative_state": True,
    }
    if ROLLBACK_RULES != required_rollback_rules:
        errors.append("ROLLBACK_RULES must match canonical rollback rules")

    required_invariants = {
        "dual_write_mode_runtime_outcome_primary_source_is_legacy": True,
        "legacy_publish_not_sufficient_without_durable_append": True,
        "shadow_read_observer_only_non_authoritative": True,
        "promotion_requires_semantic_equivalence": True,
        "pubsub_not_authoritative_for_correctness": True,
        "production_path_switch_allowed": False,
    }
    if DUAL_WRITE_SHADOW_CONTRACT_INVARIANTS != required_invariants:
        errors.append("DUAL_WRITE_SHADOW_CONTRACT_INVARIANTS must match canonical invariant set")

    return errors

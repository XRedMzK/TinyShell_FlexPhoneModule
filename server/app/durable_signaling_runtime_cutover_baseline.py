from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeCutoverModeSpec:
    mode_name: str
    authoritative_delivery_path: str
    pubsub_role: str
    stream_write_required: bool
    stream_read_required: bool
    dual_write_enabled: bool
    rollback_target_mode: str | None
    production_runtime_default: bool


@dataclass(frozen=True)
class EventMigrationSpec:
    event_name: str
    event_class: str
    source_mode: str
    target_mode: str
    dual_write_shadow_required: bool
    rollback_mode: str


ROLLOUT_MODES = (
    "pubsub_legacy",
    "dual_write_shadow",
    "durable_authoritative",
)

DEFAULT_ROLLOUT_MODE = "pubsub_legacy"
FEATURE_FLAG_KEY = "FLEXPHONE_SIGNALING_DELIVERY_MODE"

RUNTIME_SWITCH_BOUNDARY = {
    "step_23_1_contract_only": True,
    "production_cutover_in_step_23_1": False,
    "feature_flag_gated": True,
}

RUNTIME_CUTOVER_MODE_CONTRACT: dict[str, RuntimeCutoverModeSpec] = {
    "pubsub_legacy": RuntimeCutoverModeSpec(
        mode_name="pubsub_legacy",
        authoritative_delivery_path="pubsub_legacy",
        pubsub_role="primary_delivery",
        stream_write_required=False,
        stream_read_required=False,
        dual_write_enabled=False,
        rollback_target_mode=None,
        production_runtime_default=True,
    ),
    "dual_write_shadow": RuntimeCutoverModeSpec(
        mode_name="dual_write_shadow",
        authoritative_delivery_path="pubsub_legacy_with_durable_shadow",
        pubsub_role="primary_delivery_plus_shadow_validation",
        stream_write_required=True,
        stream_read_required=False,
        dual_write_enabled=True,
        rollback_target_mode="pubsub_legacy",
        production_runtime_default=False,
    ),
    "durable_authoritative": RuntimeCutoverModeSpec(
        mode_name="durable_authoritative",
        authoritative_delivery_path="durable_stream_primary",
        pubsub_role="best_effort_fanout_hint",
        stream_write_required=True,
        stream_read_required=True,
        dual_write_enabled=False,
        rollback_target_mode="dual_write_shadow",
        production_runtime_default=False,
    ),
}

ROLLBACK_BOUNDARIES = {
    "allowed_rollbacks": (
        ("durable_authoritative", "dual_write_shadow"),
        ("dual_write_shadow", "pubsub_legacy"),
    ),
    "direct_durable_to_legacy_allowed": False,
    "abort_conditions": (
        "durable_append_failure_budget_exceeded",
        "replay_or_apply_idempotency_violation",
        "ordering_scope_violation",
        "pending_recovery_regression",
        "readiness_or_correctness_degradation",
    ),
}

CUTOVER_INVARIANTS = {
    "no_authoritative_correctness_dependency_on_pubsub_only": True,
    "feature_flag_gated_rollout": True,
    "rollout_reversible": True,
    "idempotent_apply_mandatory": True,
    "ordering_scoped_and_deterministic": True,
    "dual_write_does_not_change_canonical_outcome": True,
    "production_path_switch_allowed": False,
}

STAGE23_SUBSTEP_DRAFT = {
    "23.1": "runtime_cutover_baseline_definition",
    "23.2": "authoritative_runtime_path_inventory_and_migration_matrix",
    "23.3": "dual_write_shadow_read_contract",
    "23.4": "runtime_cutover_sandbox_smoke",
    "23.5": "ci_runtime_cutover_gate",
    "23.6": "production_readiness_and_rollback_contract",
}


def _build_event_migration_matrix() -> dict[str, EventMigrationSpec]:
    from app.signaling_event_inventory_baseline import SIGNALING_EVENT_INVENTORY_BASELINE

    matrix: dict[str, EventMigrationSpec] = {}
    for event_name, event_spec in SIGNALING_EVENT_INVENTORY_BASELINE.items():
        if event_spec.event_class == "authoritative_durable_coordination_events":
            matrix[event_name] = EventMigrationSpec(
                event_name=event_name,
                event_class=event_spec.event_class,
                source_mode="pubsub_legacy",
                target_mode="durable_authoritative",
                dual_write_shadow_required=True,
                rollback_mode="dual_write_shadow",
            )
        elif event_spec.event_class == "ephemeral_fanout_hints":
            matrix[event_name] = EventMigrationSpec(
                event_name=event_name,
                event_class=event_spec.event_class,
                source_mode="pubsub_legacy",
                target_mode="pubsub_legacy",
                dual_write_shadow_required=False,
                rollback_mode="pubsub_legacy",
            )
        else:
            matrix[event_name] = EventMigrationSpec(
                event_name=event_name,
                event_class=event_spec.event_class,
                source_mode="pubsub_legacy",
                target_mode="pubsub_legacy",
                dual_write_shadow_required=False,
                rollback_mode="pubsub_legacy",
            )
    return matrix


EVENT_MIGRATION_MATRIX_BASELINE = _build_event_migration_matrix()


def validate_durable_signaling_runtime_cutover_baseline_contract() -> list[str]:
    errors: list[str] = []

    from app.signaling_event_inventory_baseline import SIGNALING_EVENT_INVENTORY_BASELINE

    if ROLLOUT_MODES != ("pubsub_legacy", "dual_write_shadow", "durable_authoritative"):
        errors.append("ROLLOUT_MODES must match canonical cutover modes")

    if DEFAULT_ROLLOUT_MODE != "pubsub_legacy":
        errors.append("DEFAULT_ROLLOUT_MODE must be pubsub_legacy")

    if FEATURE_FLAG_KEY != "FLEXPHONE_SIGNALING_DELIVERY_MODE":
        errors.append("FEATURE_FLAG_KEY must be FLEXPHONE_SIGNALING_DELIVERY_MODE")

    required_switch_boundary = {
        "step_23_1_contract_only": True,
        "production_cutover_in_step_23_1": False,
        "feature_flag_gated": True,
    }
    if RUNTIME_SWITCH_BOUNDARY != required_switch_boundary:
        errors.append("RUNTIME_SWITCH_BOUNDARY must match Step 23.1 contract-only boundary")

    if set(RUNTIME_CUTOVER_MODE_CONTRACT.keys()) != set(ROLLOUT_MODES):
        errors.append("RUNTIME_CUTOVER_MODE_CONTRACT must define all rollout modes")

    for mode_name, mode_spec in RUNTIME_CUTOVER_MODE_CONTRACT.items():
        if mode_spec.mode_name != mode_name:
            errors.append(f"{mode_name}: mode_name field must match dictionary key")
        if mode_spec.rollback_target_mode is not None and mode_spec.rollback_target_mode not in ROLLOUT_MODES:
            errors.append(f"{mode_name}: rollback_target_mode must be null or valid rollout mode")

    pubsub_legacy = RUNTIME_CUTOVER_MODE_CONTRACT["pubsub_legacy"]
    if not pubsub_legacy.production_runtime_default:
        errors.append("pubsub_legacy must remain production_runtime_default in Step 23.1")
    if pubsub_legacy.stream_read_required or pubsub_legacy.stream_write_required:
        errors.append("pubsub_legacy must not require durable stream read/write")

    dual_write_shadow = RUNTIME_CUTOVER_MODE_CONTRACT["dual_write_shadow"]
    if not dual_write_shadow.stream_write_required or dual_write_shadow.stream_read_required:
        errors.append("dual_write_shadow must require stream write and keep stream read disabled")
    if not dual_write_shadow.dual_write_enabled:
        errors.append("dual_write_shadow must have dual_write_enabled=true")
    if dual_write_shadow.rollback_target_mode != "pubsub_legacy":
        errors.append("dual_write_shadow rollback target must be pubsub_legacy")

    durable_authoritative = RUNTIME_CUTOVER_MODE_CONTRACT["durable_authoritative"]
    if not durable_authoritative.stream_write_required or not durable_authoritative.stream_read_required:
        errors.append("durable_authoritative must require stream write and stream read")
    if durable_authoritative.dual_write_enabled:
        errors.append("durable_authoritative must have dual_write_enabled=false")
    if durable_authoritative.rollback_target_mode != "dual_write_shadow":
        errors.append("durable_authoritative rollback target must be dual_write_shadow")
    if durable_authoritative.pubsub_role != "best_effort_fanout_hint":
        errors.append("durable_authoritative pubsub_role must be best_effort_fanout_hint")

    required_rollbacks = {
        ("durable_authoritative", "dual_write_shadow"),
        ("dual_write_shadow", "pubsub_legacy"),
    }
    if set(ROLLBACK_BOUNDARIES.get("allowed_rollbacks", ())) != required_rollbacks:
        errors.append("ROLLBACK_BOUNDARIES.allowed_rollbacks must match canonical rollback set")
    if ROLLBACK_BOUNDARIES.get("direct_durable_to_legacy_allowed") is not False:
        errors.append("ROLLBACK_BOUNDARIES.direct_durable_to_legacy_allowed must be false")
    if len(ROLLBACK_BOUNDARIES.get("abort_conditions", ())) < 5:
        errors.append("ROLLBACK_BOUNDARIES.abort_conditions must define baseline abort set")

    if set(EVENT_MIGRATION_MATRIX_BASELINE.keys()) != set(SIGNALING_EVENT_INVENTORY_BASELINE.keys()):
        errors.append("EVENT_MIGRATION_MATRIX_BASELINE must cover full Step 22 event inventory")

    for event_name, migration in EVENT_MIGRATION_MATRIX_BASELINE.items():
        inventory = SIGNALING_EVENT_INVENTORY_BASELINE[event_name]
        if migration.event_name != event_name:
            errors.append(f"{event_name}: migration event_name field must match dictionary key")
        if migration.event_class != inventory.event_class:
            errors.append(f"{event_name}: migration event_class must match Step 22 inventory class")
        if migration.source_mode != "pubsub_legacy":
            errors.append(f"{event_name}: migration source_mode must be pubsub_legacy")

        if inventory.event_class == "authoritative_durable_coordination_events":
            if migration.target_mode != "durable_authoritative":
                errors.append(f"{event_name}: authoritative event target_mode must be durable_authoritative")
            if not migration.dual_write_shadow_required:
                errors.append(f"{event_name}: authoritative event must require dual_write_shadow phase")
            if migration.rollback_mode != "dual_write_shadow":
                errors.append(f"{event_name}: authoritative event rollback_mode must be dual_write_shadow")
        else:
            if migration.target_mode != "pubsub_legacy":
                errors.append(f"{event_name}: non-authoritative event target_mode must remain pubsub_legacy")
            if migration.dual_write_shadow_required:
                errors.append(f"{event_name}: non-authoritative event must not require dual_write_shadow")
            if migration.rollback_mode != "pubsub_legacy":
                errors.append(f"{event_name}: non-authoritative event rollback_mode must be pubsub_legacy")

    required_invariants = {
        "no_authoritative_correctness_dependency_on_pubsub_only": True,
        "feature_flag_gated_rollout": True,
        "rollout_reversible": True,
        "idempotent_apply_mandatory": True,
        "ordering_scoped_and_deterministic": True,
        "dual_write_does_not_change_canonical_outcome": True,
        "production_path_switch_allowed": False,
    }
    if CUTOVER_INVARIANTS != required_invariants:
        errors.append("CUTOVER_INVARIANTS must match Step 23.1 invariant set")

    required_stage_draft = {
        "23.1": "runtime_cutover_baseline_definition",
        "23.2": "authoritative_runtime_path_inventory_and_migration_matrix",
        "23.3": "dual_write_shadow_read_contract",
        "23.4": "runtime_cutover_sandbox_smoke",
        "23.5": "ci_runtime_cutover_gate",
        "23.6": "production_readiness_and_rollback_contract",
    }
    if STAGE23_SUBSTEP_DRAFT != required_stage_draft:
        errors.append("STAGE23_SUBSTEP_DRAFT must match baseline stage draft")

    return errors

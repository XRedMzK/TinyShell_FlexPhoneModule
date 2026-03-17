from __future__ import annotations


CI_GATE_MODES = ("pubsub_legacy", "dual_write_shadow", "durable_authoritative")

CI_GATE_REQUIRED_PROOF_KEYS = {
    "pubsub_legacy": ("pubsub_legacy", "rollback_dual_to_legacy"),
    "dual_write_shadow": ("dual_write_shadow",),
    "durable_authoritative": ("durable_authoritative", "rollback_durable_to_shadow"),
}

CI_GATE_FAIL_CONDITIONS = (
    "mode_contract_violation",
    "ownership_boundary_violation",
    "shadow_equivalence_violation",
    "unexpected_promotion_or_rollback_behavior",
    "replay_or_pending_recovery_invariant_violation",
    "proof_payload_incomplete_or_nondeterministic",
)

CI_GATE_INVARIANTS = {
    "ci_gate_is_contract_semantic_not_startup_only": True,
    "redis_service_container_isolated": True,
    "contract_breach_must_fail_nonzero": True,
    "production_runtime_path_unchanged": True,
}

WORKFLOW_BASELINE = {
    "workflow_path": ".github/workflows/runtime-cutover-ci.yml",
    "job_name": "runtime-cutover-mode-gate",
    "matrix_modes": CI_GATE_MODES,
    "runner_script": "server/tools/run_runtime_cutover_ci_simulation.py",
}


def validate_runtime_cutover_ci_gate_baseline() -> list[str]:
    errors: list[str] = []

    from app.durable_signaling_runtime_cutover_baseline import ROLLOUT_MODES
    from app.durable_signaling_runtime_path_inventory import ROLLOUT_MODES as INVENTORY_ROLLOUT_MODES
    from app.durable_signaling_dual_write_shadow_read_contract import (
        DUAL_WRITE_MODE_NAME,
        MISMATCH_CLASS_ACTION_BASELINE,
    )

    if CI_GATE_MODES != ROLLOUT_MODES:
        errors.append("CI_GATE_MODES must match Step 23.1 rollout modes")
    if CI_GATE_MODES != INVENTORY_ROLLOUT_MODES:
        errors.append("CI_GATE_MODES must match Step 23.2 rollout modes")

    if DUAL_WRITE_MODE_NAME != "dual_write_shadow":
        errors.append("Step 23.3 dual-write mode name must remain dual_write_shadow")

    if "legacy_ok_durable_append_fail" not in MISMATCH_CLASS_ACTION_BASELINE:
        errors.append("Step 23.3 mismatch baseline must include legacy_ok_durable_append_fail")
    elif MISMATCH_CLASS_ACTION_BASELINE["legacy_ok_durable_append_fail"] != "block_cutover_progression":
        errors.append("legacy_ok_durable_append_fail action must remain block_cutover_progression")

    if set(CI_GATE_REQUIRED_PROOF_KEYS.keys()) != set(CI_GATE_MODES):
        errors.append("CI_GATE_REQUIRED_PROOF_KEYS must define all CI gate modes")

    required_invariants = {
        "ci_gate_is_contract_semantic_not_startup_only": True,
        "redis_service_container_isolated": True,
        "contract_breach_must_fail_nonzero": True,
        "production_runtime_path_unchanged": True,
    }
    if CI_GATE_INVARIANTS != required_invariants:
        errors.append("CI_GATE_INVARIANTS must match baseline invariants")

    required_workflow_baseline = {
        "workflow_path": ".github/workflows/runtime-cutover-ci.yml",
        "job_name": "runtime-cutover-mode-gate",
        "matrix_modes": CI_GATE_MODES,
        "runner_script": "server/tools/run_runtime_cutover_ci_simulation.py",
    }
    if WORKFLOW_BASELINE != required_workflow_baseline:
        errors.append("WORKFLOW_BASELINE must match CI gate workflow baseline")

    if len(CI_GATE_FAIL_CONDITIONS) < 6:
        errors.append("CI_GATE_FAIL_CONDITIONS must include full baseline failure classes")

    return errors

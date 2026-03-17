from __future__ import annotations


PRODUCTION_PROMOTION_READINESS = {
    "dual_write_shadow": {
        "required_completed_steps": ("23.1", "23.2"),
        "required_signals": (
            "readiness_green_with_required_redis",
            "runtime_cutover_inventory_consistent",
            "feature_flag_boundary_defined",
        ),
        "no_go_conditions": (
            "readiness_signaling_redis_degraded",
            "ownership_boundary_ambiguous",
        ),
    },
    "durable_authoritative": {
        "required_completed_steps": ("23.1", "23.2", "23.3", "23.4", "23.5"),
        "required_signals": (
            "dual_write_shadow_no_blocking_mismatch",
            "reconnect_replay_pending_recovery_stable",
            "ci_cutover_mode_matrix_green",
            "rollback_path_preverified",
            "observability_signals_present",
        ),
        "no_go_conditions": (
            "blocking_shadow_mismatch_present",
            "pending_recovery_invariant_breach",
            "nondeterministic_mode_behavior",
            "protected_deployment_controls_unavailable",
        ),
    },
}

ROLLBACK_SEVERITY_CLASSES = {
    "R1": {
        "name": "observe_only",
        "rollback_required": False,
        "promotion_freeze": False,
        "target_mode": None,
    },
    "R2": {
        "name": "freeze_promotion",
        "rollback_required": False,
        "promotion_freeze": True,
        "target_mode": None,
    },
    "R3": {
        "name": "immediate_mode_rollback",
        "rollback_required": True,
        "promotion_freeze": True,
        "target_mode": "previous_safe_mode",
    },
    "R4": {
        "name": "emergency_rollback_incident",
        "rollback_required": True,
        "promotion_freeze": True,
        "target_mode": "pubsub_legacy",
    },
}

ROLLBACK_TRIGGER_POLICY = {
    "sustained_shadow_read_mismatch": {"severity": "R3", "rollback_to": "pubsub_legacy"},
    "authoritative_ownership_boundary_breach": {"severity": "R4", "rollback_to": "pubsub_legacy"},
    "reconnect_replay_invariant_breach": {"severity": "R3", "rollback_to": "dual_write_shadow"},
    "pending_recovery_threshold_breach": {"severity": "R3", "rollback_to": "dual_write_shadow"},
    "readiness_signaling_redis_degraded": {"severity": "R3", "rollback_to": "dual_write_shadow"},
    "nondeterministic_mode_behavior": {"severity": "R4", "rollback_to": "pubsub_legacy"},
    "durable_path_unpredictable_recovery": {"severity": "R4", "rollback_to": "pubsub_legacy"},
}

ROLLBACK_EXECUTION_CONTRACT = {
    "initiator_role": "oncall_or_release_operator",
    "mode_switch_is_feature_flag_controlled": True,
    "inflight_session_policy": "allow_reconnect_reauth_reconciliation",
    "post_rollback_checks": (
        "health_ready_checks",
        "signaling_control_plane_smoke",
        "websocket_reconnect_validation",
        "mismatch_counter_stability_check",
    ),
    "incident_evidence_retention_required": True,
}

PROTECTED_DEPLOYMENT_BOUNDARIES = {
    "github_environment_required": True,
    "manual_approval_required": True,
    "branch_restrictions_required": True,
    "wait_timer_or_custom_protection_allowed": True,
    "unprotected_direct_promotion_allowed": False,
}

PRODUCTION_EVIDENCE_BASELINE = {
    "required_checkers": (
        "tools/check_durable_signaling_runtime_path_inventory.py",
        "tools/check_durable_signaling_dual_write_shadow_read_contract.py",
        "tools/check_runtime_cutover_ci_gate_baseline.py",
        "tools/check_runtime_cutover_production_readiness_rollback_contract.py",
    ),
    "required_docs": (
        "docs/step23-durable-signaling-runtime-cutover-baseline.md",
        "docs/step23-authoritative-runtime-path-inventory-migration-matrix.md",
        "docs/step23-dual-write-shadow-read-runtime-contract-baseline.md",
        "docs/step23-runtime-cutover-sandbox-smoke-baseline.md",
        "docs/step23-ci-runtime-cutover-mode-gate-baseline.md",
        "docs/step23-production-readiness-rollback-contract-baseline.md",
    ),
    "required_workflow": ".github/workflows/runtime-cutover-ci.yml",
}

PRODUCTION_READINESS_ROLLBACK_INVARIANTS = {
    "promotion_requires_explicit_go_no_go": True,
    "rollback_triggered_by_contract_breach_not_operator_guess": True,
    "rollback_targets_predeclared": True,
    "production_cutover_without_protection_forbidden": True,
    "readiness_fail_closed_dependency_guard_preserved": True,
    "pubsub_at_most_once_risk_accounted_for": True,
}


def validate_runtime_cutover_production_readiness_rollback_contract() -> list[str]:
    errors: list[str] = []

    from app.durable_signaling_runtime_cutover_baseline import ROLLBACK_BOUNDARIES, ROLLOUT_MODES
    from app.durable_signaling_dual_write_shadow_read_contract import (
        MISMATCH_CLASS_ACTION_BASELINE,
        PROMOTION_RULES,
        ROLLBACK_RULES,
    )
    from app.runtime_cutover_ci_gate_baseline import CI_GATE_MODES

    if CI_GATE_MODES != ROLLOUT_MODES:
        errors.append("CI gate modes must stay aligned with rollout modes for production readiness")

    required_promotion_keys = {"dual_write_shadow", "durable_authoritative"}
    if set(PRODUCTION_PROMOTION_READINESS.keys()) != required_promotion_keys:
        errors.append("PRODUCTION_PROMOTION_READINESS must define dual_write_shadow and durable_authoritative")

    durable_promotion = PRODUCTION_PROMOTION_READINESS["durable_authoritative"]
    required_steps = ("23.1", "23.2", "23.3", "23.4", "23.5")
    if durable_promotion.get("required_completed_steps") != required_steps:
        errors.append("durable_authoritative required_completed_steps must include 23.1..23.5")

    if PROMOTION_RULES.get("shadow_equivalence_required") is not True:
        errors.append("Step 23.3 promotion rules must require shadow equivalence")
    if "dual_write_shadow_no_blocking_mismatch" not in durable_promotion.get("required_signals", ()):
        errors.append("durable_authoritative promotion requires no blocking shadow mismatch")
    if MISMATCH_CLASS_ACTION_BASELINE.get("legacy_ok_durable_append_fail") != "block_cutover_progression":
        errors.append("blocking mismatch action must remain block_cutover_progression")

    expected_severity_classes = {"R1", "R2", "R3", "R4"}
    if set(ROLLBACK_SEVERITY_CLASSES.keys()) != expected_severity_classes:
        errors.append("ROLLBACK_SEVERITY_CLASSES must define R1/R2/R3/R4")

    for trigger, policy in ROLLBACK_TRIGGER_POLICY.items():
        severity = policy.get("severity")
        target = policy.get("rollback_to")
        if severity not in expected_severity_classes:
            errors.append(f"{trigger}: rollback severity must be one of R1..R4")
        if target not in {"pubsub_legacy", "dual_write_shadow"}:
            errors.append(f"{trigger}: rollback_to must be pubsub_legacy or dual_write_shadow")

    allowed_rollbacks = set(ROLLBACK_BOUNDARIES.get("allowed_rollbacks", ()))
    if ("durable_authoritative", "dual_write_shadow") not in allowed_rollbacks:
        errors.append("Step 23.1 rollback boundary durable_authoritative->dual_write_shadow must be allowed")
    if ("dual_write_shadow", "pubsub_legacy") not in allowed_rollbacks:
        errors.append("Step 23.1 rollback boundary dual_write_shadow->pubsub_legacy must be allowed")

    if ROLLBACK_RULES.get("rollback_target_mode") != "pubsub_legacy":
        errors.append("Step 23.3 rollback target mode must remain pubsub_legacy in dual_write mode")

    required_boundaries = {
        "github_environment_required": True,
        "manual_approval_required": True,
        "branch_restrictions_required": True,
        "wait_timer_or_custom_protection_allowed": True,
        "unprotected_direct_promotion_allowed": False,
    }
    if PROTECTED_DEPLOYMENT_BOUNDARIES != required_boundaries:
        errors.append("PROTECTED_DEPLOYMENT_BOUNDARIES must match baseline protected deployment contract")

    required_invariants = {
        "promotion_requires_explicit_go_no_go": True,
        "rollback_triggered_by_contract_breach_not_operator_guess": True,
        "rollback_targets_predeclared": True,
        "production_cutover_without_protection_forbidden": True,
        "readiness_fail_closed_dependency_guard_preserved": True,
        "pubsub_at_most_once_risk_accounted_for": True,
    }
    if PRODUCTION_READINESS_ROLLBACK_INVARIANTS != required_invariants:
        errors.append("PRODUCTION_READINESS_ROLLBACK_INVARIANTS must match baseline invariant set")

    workflow_path = PRODUCTION_EVIDENCE_BASELINE.get("required_workflow")
    if workflow_path != ".github/workflows/runtime-cutover-ci.yml":
        errors.append("PRODUCTION_EVIDENCE_BASELINE.required_workflow must target runtime-cutover-ci workflow")

    if len(PRODUCTION_EVIDENCE_BASELINE.get("required_checkers", ())) < 4:
        errors.append("PRODUCTION_EVIDENCE_BASELINE.required_checkers must include cutover baseline checks")
    if len(PRODUCTION_EVIDENCE_BASELINE.get("required_docs", ())) < 6:
        errors.append("PRODUCTION_EVIDENCE_BASELINE.required_docs must include full Step 23 baseline set")

    return errors

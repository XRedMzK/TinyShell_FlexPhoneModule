from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoverySourceSpec:
    source_id: str
    category: str
    source_of_truth: str
    recoverability: str
    restore_owner: str


@dataclass(frozen=True)
class RecoverySubstepSpec:
    step_id: str
    description: str
    verification_type: str


VALID_VERIFICATION_TYPES = {
    "build check",
    "manual runtime check",
    "API check",
    "desktop e2e manual",
    "automated test",
}

RECOVERY_SOURCE_OF_TRUTH_BASELINE: dict[str, RecoverySourceSpec] = {
    "policy_mapping": RecoverySourceSpec(
        source_id="policy_mapping",
        category="git_tracked_mapping",
        source_of_truth="server/app/reliability_alert_policy_export_baseline.py",
        recoverability="rebuild_from_git",
        restore_owner="platform_backend",
    ),
    "render_artifact_registry": RecoverySourceSpec(
        source_id="render_artifact_registry",
        category="git_tracked_mapping",
        source_of_truth="server/app/reliability_alert_provisioning_artifacts_baseline.py",
        recoverability="rebuild_from_git",
        restore_owner="platform_backend",
    ),
    "rendered_provisioning_artifacts": RecoverySourceSpec(
        source_id="rendered_provisioning_artifacts",
        category="git_tracked_derived_artifacts",
        source_of_truth="server/generated/*.rendered.yml",
        recoverability="re_render_from_mapping",
        restore_owner="platform_backend",
    ),
    "runtime_env_and_secrets": RecoverySourceSpec(
        source_id="runtime_env_and_secrets",
        category="external_runtime_input",
        source_of_truth="runtime_env_or_secret_store",
        recoverability="restore_from_secret_management",
        restore_owner="ops",
    ),
    "redis_auth_signaling_state": RecoverySourceSpec(
        source_id="redis_auth_signaling_state",
        category="transient_runtime_state",
        source_of_truth="redis_runtime_state",
        recoverability="bounded_loss_convergence",
        restore_owner="runtime_system",
    ),
}

STAGE21_SUBSTEP_BASELINE: dict[str, RecoverySubstepSpec] = {
    "21.1": RecoverySubstepSpec(
        step_id="21.1",
        description="Recovery/restore stage definition baseline",
        verification_type="build check",
    ),
    "21.2": RecoverySubstepSpec(
        step_id="21.2",
        description="Source-of-truth and backup-restore inventory baseline",
        verification_type="build check",
    ),
    "21.3": RecoverySubstepSpec(
        step_id="21.3",
        description="Redis loss/restart recovery semantics baseline",
        verification_type="build check",
    ),
    "21.4": RecoverySubstepSpec(
        step_id="21.4",
        description="Post-restore runtime validation checklist baseline",
        verification_type="manual runtime check",
    ),
    "21.5": RecoverySubstepSpec(
        step_id="21.5",
        description="Sandbox restore smoke/runbook baseline",
        verification_type="manual runtime check",
    ),
    "21.6": RecoverySubstepSpec(
        step_id="21.6",
        description="CI-friendly restore simulation gate baseline",
        verification_type="build check",
    ),
}

BOUNDED_LOSS_BASELINE = {
    "redis_auth_signaling_state": {
        "loss_mode": "store_loss_or_restart",
        "expected_convergence": "reconnect/re-auth/startup_reconciliation",
        "resurrection_mode": "not_required",
    }
}

POST_RESTORE_ACCEPTANCE_CHECKLIST_BASELINE = (
    "health",
    "ready",
    "auth_challenge",
    "auth_verify",
    "ws_signaling",
    "provisioning_acceptance",
    "observability_signals",
)


def validate_recovery_restore_baseline_contract() -> list[str]:
    errors: list[str] = []

    expected_source_ids = {
        "policy_mapping",
        "render_artifact_registry",
        "rendered_provisioning_artifacts",
        "runtime_env_and_secrets",
        "redis_auth_signaling_state",
    }
    if set(RECOVERY_SOURCE_OF_TRUTH_BASELINE.keys()) != expected_source_ids:
        errors.append("RECOVERY_SOURCE_OF_TRUTH_BASELINE keys must match expected source ids")

    for source_id, spec in RECOVERY_SOURCE_OF_TRUTH_BASELINE.items():
        if spec.source_id != source_id:
            errors.append(f"{source_id}: source_id field must match dictionary key")
        if not spec.source_of_truth:
            errors.append(f"{source_id}: source_of_truth must not be empty")
        if not spec.recoverability:
            errors.append(f"{source_id}: recoverability must not be empty")

    if RECOVERY_SOURCE_OF_TRUTH_BASELINE["redis_auth_signaling_state"].category != "transient_runtime_state":
        errors.append("redis_auth_signaling_state must be categorized as transient_runtime_state")

    expected_steps = ("21.1", "21.2", "21.3", "21.4", "21.5", "21.6")
    if tuple(STAGE21_SUBSTEP_BASELINE.keys()) != expected_steps:
        errors.append("STAGE21_SUBSTEP_BASELINE keys must be ordered as 21.1..21.6")

    for step_id, step_spec in STAGE21_SUBSTEP_BASELINE.items():
        if step_spec.step_id != step_id:
            errors.append(f"{step_id}: step_id field must match dictionary key")
        if step_spec.verification_type not in VALID_VERIFICATION_TYPES:
            errors.append(
                f"{step_id}: verification_type is not supported: {step_spec.verification_type}"
            )

    redis_loss_spec = BOUNDED_LOSS_BASELINE.get("redis_auth_signaling_state")
    if not redis_loss_spec:
        errors.append("BOUNDED_LOSS_BASELINE must define redis_auth_signaling_state")
    else:
        if redis_loss_spec.get("expected_convergence") != "reconnect/re-auth/startup_reconciliation":
            errors.append(
                "redis_auth_signaling_state expected_convergence must be reconnect/re-auth/startup_reconciliation"
            )

    required_post_restore_checks = {
        "health",
        "ready",
        "auth_challenge",
        "auth_verify",
        "ws_signaling",
        "provisioning_acceptance",
        "observability_signals",
    }
    if set(POST_RESTORE_ACCEPTANCE_CHECKLIST_BASELINE) != required_post_restore_checks:
        errors.append("POST_RESTORE_ACCEPTANCE_CHECKLIST_BASELINE must contain required checks")

    return errors

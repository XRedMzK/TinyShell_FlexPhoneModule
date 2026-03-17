from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryInventoryClassSpec:
    class_id: str
    title: str
    source_of_truth: str
    backup_requirement: str
    restore_method: str
    owner_domain: str


@dataclass(frozen=True)
class RecoveryInventoryItemSpec:
    item_id: str
    inventory_class: str
    examples: tuple[str, ...]
    notes: str


RECOVERY_INVENTORY_CLASS_BASELINE: dict[str, RecoveryInventoryClassSpec] = {
    "git_canonical": RecoveryInventoryClassSpec(
        class_id="git_canonical",
        title="Git-Managed Canonical State",
        source_of_truth="git_repository",
        backup_requirement="required_repo_remote",
        restore_method="checkout_and_render_check",
        owner_domain="repo/build",
    ),
    "env_secrets_external": RecoveryInventoryClassSpec(
        class_id="env_secrets_external",
        title="External Env/Secrets State",
        source_of_truth="external_config_secret_system",
        backup_requirement="required_external",
        restore_method="operator_reinjection",
        owner_domain="ops/secrets",
    ),
    "persistent_operational_conditional": RecoveryInventoryClassSpec(
        class_id="persistent_operational_conditional",
        title="Persistent Operational State (Conditional)",
        source_of_truth="service_persistent_storage",
        backup_requirement="conditional",
        restore_method="service_data_restore_before_startup",
        owner_domain="ops/runtime",
    ),
    "transient_runtime_bounded_loss": RecoveryInventoryClassSpec(
        class_id="transient_runtime_bounded_loss",
        title="Transient Bounded-Loss Runtime State",
        source_of_truth="none",
        backup_requirement="out_of_scope",
        restore_method="convergence_via_restart_reauth_reconnect",
        owner_domain="app/runtime",
    ),
}

RECOVERY_INVENTORY_MATRIX_BASELINE: dict[str, RecoveryInventoryItemSpec] = {
    "repo_assets": RecoveryInventoryItemSpec(
        item_id="repo_assets",
        inventory_class="git_canonical",
        examples=(
            "application_code",
            "docs_contracts_runbooks",
            "mapping_baseline_modules",
            "ci_workflows",
            "rendered_deterministic_provisioning_artifacts",
        ),
        notes="Rendered artifacts remain derived; mapping modules remain semantic authority.",
    ),
    "runtime_env_secrets": RecoveryInventoryItemSpec(
        item_id="runtime_env_secrets",
        inventory_class="env_secrets_external",
        examples=(
            "redis_urls",
            "jwt_signing_material",
            "webhook_credentials",
            "smtp_credentials",
            "grafana_admin_credentials",
        ),
        notes="Not repository-managed restore targets.",
    ),
    "grafana_persistent_data": RecoveryInventoryItemSpec(
        item_id="grafana_persistent_data",
        inventory_class="persistent_operational_conditional",
        examples=(
            "grafana_db",
            "grafana_plugin_data",
            "non_provisioned_resources",
        ),
        notes="Restore target only when runtime depends on non-provisioned resources.",
    ),
    "redis_transient_runtime": RecoveryInventoryItemSpec(
        item_id="redis_transient_runtime",
        inventory_class="transient_runtime_bounded_loss",
        examples=(
            "auth_challenge_keys",
            "signaling_presence_session_keys",
            "pubsub_transient_delivery_state",
            "inflight_ephemeral_sessions",
        ),
        notes="Backup/restore out of scope; correctness by convergence.",
    ),
}

RESTORE_OWNERSHIP_BOUNDARY_BASELINE = {
    "repo/build": (
        "git_canonical_checkout",
        "render_and_contract_checks",
    ),
    "ops/secrets": (
        "external_secret_injection",
        "runtime_env_injection",
    ),
    "ops/runtime": (
        "persistent_service_data_restore",
        "startup_sequence_control",
    ),
    "app/runtime": (
        "bounded_loss_convergence",
        "reconnect_reauth_reconciliation",
    ),
}

NORMATIVE_RECOVERY_STATEMENTS = (
    "git_is_canonical_for_repo_managed_assets",
    "rendered_artifacts_are_derived_mapping_authoritative",
    "env_secrets_are_external_reinjection_targets",
    "redis_auth_signaling_state_out_of_backup_scope",
    "grafana_persistent_data_restore_conditional_on_non_provisioned_usage",
    "alertmanager_restore_requires_valid_config_and_reload_acceptance",
)


def validate_recovery_restore_inventory_baseline_contract() -> list[str]:
    errors: list[str] = []

    expected_classes = (
        "git_canonical",
        "env_secrets_external",
        "persistent_operational_conditional",
        "transient_runtime_bounded_loss",
    )
    if tuple(RECOVERY_INVENTORY_CLASS_BASELINE.keys()) != expected_classes:
        errors.append("RECOVERY_INVENTORY_CLASS_BASELINE keys must be ordered canonical class ids")

    for class_id, class_spec in RECOVERY_INVENTORY_CLASS_BASELINE.items():
        if class_spec.class_id != class_id:
            errors.append(f"{class_id}: class_id field must match dictionary key")
        if not class_spec.restore_method:
            errors.append(f"{class_id}: restore_method must not be empty")
        if class_spec.owner_domain not in RESTORE_OWNERSHIP_BOUNDARY_BASELINE:
            errors.append(f"{class_id}: owner_domain must exist in RESTORE_OWNERSHIP_BOUNDARY_BASELINE")

    expected_items = {
        "repo_assets",
        "runtime_env_secrets",
        "grafana_persistent_data",
        "redis_transient_runtime",
    }
    if set(RECOVERY_INVENTORY_MATRIX_BASELINE.keys()) != expected_items:
        errors.append("RECOVERY_INVENTORY_MATRIX_BASELINE must contain required inventory items")

    for item_id, item_spec in RECOVERY_INVENTORY_MATRIX_BASELINE.items():
        if item_spec.item_id != item_id:
            errors.append(f"{item_id}: item_id field must match dictionary key")
        if item_spec.inventory_class not in RECOVERY_INVENTORY_CLASS_BASELINE:
            errors.append(f"{item_id}: unknown inventory_class: {item_spec.inventory_class}")
        if not item_spec.examples:
            errors.append(f"{item_id}: examples must not be empty")

    transient_class = RECOVERY_INVENTORY_CLASS_BASELINE["transient_runtime_bounded_loss"]
    if transient_class.backup_requirement != "out_of_scope":
        errors.append("transient_runtime_bounded_loss backup_requirement must be out_of_scope")
    if transient_class.restore_method != "convergence_via_restart_reauth_reconnect":
        errors.append(
            "transient_runtime_bounded_loss restore_method must be convergence_via_restart_reauth_reconnect"
        )

    env_class = RECOVERY_INVENTORY_CLASS_BASELINE["env_secrets_external"]
    if env_class.source_of_truth != "external_config_secret_system":
        errors.append("env_secrets_external source_of_truth must be external_config_secret_system")

    repo_item = RECOVERY_INVENTORY_MATRIX_BASELINE["repo_assets"]
    if "rendered_deterministic_provisioning_artifacts" not in repo_item.examples:
        errors.append("repo_assets examples must include rendered_deterministic_provisioning_artifacts")

    redis_item = RECOVERY_INVENTORY_MATRIX_BASELINE["redis_transient_runtime"]
    if "pubsub_transient_delivery_state" not in redis_item.examples:
        errors.append("redis_transient_runtime examples must include pubsub_transient_delivery_state")

    required_statements = {
        "git_is_canonical_for_repo_managed_assets",
        "rendered_artifacts_are_derived_mapping_authoritative",
        "env_secrets_are_external_reinjection_targets",
        "redis_auth_signaling_state_out_of_backup_scope",
        "grafana_persistent_data_restore_conditional_on_non_provisioned_usage",
        "alertmanager_restore_requires_valid_config_and_reload_acceptance",
    }
    if set(NORMATIVE_RECOVERY_STATEMENTS) != required_statements:
        errors.append("NORMATIVE_RECOVERY_STATEMENTS must match required baseline statements")

    return errors

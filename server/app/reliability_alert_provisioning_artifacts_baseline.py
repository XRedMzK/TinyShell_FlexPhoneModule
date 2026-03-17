from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderedProvisioningArtifactSpec:
    artifact_id: str
    platform: str
    resource_kind: str
    relative_path: str
    source_mapping: str
    file_format: str = "yaml"


RENDERED_PROVISIONING_ARTIFACTS_BASELINE: dict[str, RenderedProvisioningArtifactSpec] = {
    "alertmanager_config": RenderedProvisioningArtifactSpec(
        artifact_id="alertmanager_config",
        platform="alertmanager",
        resource_kind="config",
        relative_path="generated/alertmanager/alertmanager.rendered.yml",
        source_mapping="ALERTMANAGER_EXPORT_BASELINE",
    ),
    "grafana_contact_points": RenderedProvisioningArtifactSpec(
        artifact_id="grafana_contact_points",
        platform="grafana",
        resource_kind="contact_points",
        relative_path="generated/grafana/provisioning/alerting/contact-points.rendered.yml",
        source_mapping="GRAFANA_CONTACT_POINT_EXPORT_BASELINE",
    ),
    "grafana_policies": RenderedProvisioningArtifactSpec(
        artifact_id="grafana_policies",
        platform="grafana",
        resource_kind="notification_policies",
        relative_path="generated/grafana/provisioning/alerting/policies.rendered.yml",
        source_mapping="GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE",
    ),
    "grafana_mute_timings": RenderedProvisioningArtifactSpec(
        artifact_id="grafana_mute_timings",
        platform="grafana",
        resource_kind="mute_timings",
        relative_path="generated/grafana/provisioning/alerting/mute-timings.rendered.yml",
        source_mapping="GRAFANA_MUTE_TIMING_EXPORT_BASELINE",
    ),
    "grafana_templates": RenderedProvisioningArtifactSpec(
        artifact_id="grafana_templates",
        platform="grafana",
        resource_kind="notification_templates",
        relative_path="generated/grafana/provisioning/alerting/templates.rendered.yml",
        source_mapping="GRAFANA_TEMPLATE_EXPORT_BASELINE",
    ),
}

RENDERED_PROVISIONING_ARTIFACT_ORDER = (
    "alertmanager_config",
    "grafana_contact_points",
    "grafana_policies",
    "grafana_mute_timings",
    "grafana_templates",
)


def validate_reliability_alert_provisioning_artifacts_baseline_contract() -> list[str]:
    errors: list[str] = []

    if tuple(RENDERED_PROVISIONING_ARTIFACTS_BASELINE.keys()) != RENDERED_PROVISIONING_ARTIFACT_ORDER:
        errors.append(
            "RENDERED_PROVISIONING_ARTIFACTS_BASELINE keys must match RENDERED_PROVISIONING_ARTIFACT_ORDER"
        )

    seen_paths: set[str] = set()
    for artifact_id in RENDERED_PROVISIONING_ARTIFACT_ORDER:
        spec = RENDERED_PROVISIONING_ARTIFACTS_BASELINE.get(artifact_id)
        if spec is None:
            errors.append(f"{artifact_id}: missing artifact spec")
            continue

        if spec.artifact_id != artifact_id:
            errors.append(f"{artifact_id}: artifact_id field must match dictionary key")

        if spec.platform not in {"alertmanager", "grafana"}:
            errors.append(f"{artifact_id}: unsupported platform: {spec.platform}")

        if not spec.relative_path.startswith("generated/"):
            errors.append(f"{artifact_id}: relative_path must start with generated/: {spec.relative_path}")
        if not spec.relative_path.endswith(".rendered.yml"):
            errors.append(f"{artifact_id}: relative_path must end with .rendered.yml: {spec.relative_path}")
        if spec.relative_path in seen_paths:
            errors.append(f"{artifact_id}: relative_path must be unique: {spec.relative_path}")
        seen_paths.add(spec.relative_path)

        if spec.file_format != "yaml":
            errors.append(f"{artifact_id}: file_format must be yaml")
        if not spec.source_mapping.endswith("_BASELINE"):
            errors.append(f"{artifact_id}: source_mapping must reference a *_BASELINE constant")

    return errors

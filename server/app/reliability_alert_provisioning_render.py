from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any

from .reliability_alert_policy_export_baseline import (
    ALERTMANAGER_EXPORT_BASELINE,
    ALERTMANAGER_INHIBIT_EXPORT_BASELINE,
    ALERTMANAGER_RECEIVER_EXPORT_BASELINE,
    ALERTMANAGER_ROUTE_EXPORT_BASELINE,
    ALERTMANAGER_TEMPLATE_EXPORT_BASELINE,
    GRAFANA_CONTACT_POINT_EXPORT_BASELINE,
    GRAFANA_MUTE_TIMING_EXPORT_BASELINE,
    GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE,
    GRAFANA_TEMPLATE_EXPORT_BASELINE,
)
from .reliability_alert_provisioning_artifacts_baseline import (
    RENDERED_PROVISIONING_ARTIFACT_ORDER,
    RENDERED_PROVISIONING_ARTIFACTS_BASELINE,
)
from .reliability_alert_routing_baseline import ALERT_NOTIFICATION_TARGET_BASELINE


def _stable_primitive(value: Any) -> Any:
    if is_dataclass(value):
        return _stable_primitive(asdict(value))
    if isinstance(value, dict):
        return {str(key): _stable_primitive(value[key]) for key in sorted(value.keys(), key=str)}
    if isinstance(value, tuple):
        return [_stable_primitive(item) for item in value]
    if isinstance(value, list):
        return [_stable_primitive(item) for item in value]
    if isinstance(value, set):
        return [_stable_primitive(item) for item in sorted(value)]
    return value


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)


def _emit_yaml_lines(value: Any, *, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        if not value:
            return [f"{prefix}{{}}"]
        lines: list[str] = []
        for key in sorted(value.keys()):
            item = value[key]
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_emit_yaml_lines(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_emit_yaml_lines(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines

    return [f"{prefix}{_yaml_scalar(value)}"]


def _render_yaml(data: dict[str, Any]) -> str:
    stable = _stable_primitive(data)
    return "\n".join(_emit_yaml_lines(stable)) + "\n"


def _matcher_expressions(matchers: dict[str, str]) -> list[str]:
    return [f'{key}="{value}"' for key, value in sorted(matchers.items())]


def _object_matchers(matchers: dict[str, str]) -> list[list[str]]:
    return [[key, "=", value] for key, value in sorted(matchers.items())]


def _alertmanager_receiver_url(channel: str) -> str:
    return f"http://alerts.local/{channel}"


def _build_alertmanager_payload() -> dict[str, Any]:
    routes = []
    for _, route_spec in sorted(ALERTMANAGER_ROUTE_EXPORT_BASELINE.items()):
        routes.append(
            {
                "receiver": route_spec.receiver,
                "continue": False,
                "group_by": list(route_spec.group_by),
                "group_wait": route_spec.group_wait,
                "group_interval": route_spec.group_interval,
                "repeat_interval": route_spec.repeat_interval,
                "matchers": _matcher_expressions(route_spec.matchers),
            }
        )

    receivers = []
    for receiver_id, receiver_spec in sorted(ALERTMANAGER_RECEIVER_EXPORT_BASELINE.items()):
        target_spec = ALERT_NOTIFICATION_TARGET_BASELINE[receiver_id]
        receivers.append(
            {
                "name": receiver_id,
                "webhook_configs": [
                    {
                        "url": _alertmanager_receiver_url(target_spec.channel),
                        "send_resolved": True,
                    }
                ],
            }
        )

    inhibit_rules = []
    for _, rule_spec in sorted(ALERTMANAGER_INHIBIT_EXPORT_BASELINE.items()):
        inhibit_rules.append(
            {
                "source_matchers": _matcher_expressions(rule_spec.source_matchers),
                "target_matchers": _matcher_expressions(rule_spec.target_matchers),
                "equal": list(rule_spec.equal_labels),
            }
        )

    template_paths = [
        f"templates/{template_id}.tmpl"
        for template_id in sorted(ALERTMANAGER_TEMPLATE_EXPORT_BASELINE.keys())
    ]

    return {
        "global": {"resolve_timeout": "5m"},
        "route": {
            "receiver": ALERTMANAGER_EXPORT_BASELINE["root_receiver"],
            "group_by": ["service", "severity"],
            "group_wait": "30s",
            "group_interval": "5m",
            "repeat_interval": "4h",
            "routes": routes,
        },
        "receivers": receivers,
        "inhibit_rules": inhibit_rules,
        "templates": template_paths,
    }


def _grafana_receiver_type(endpoint_ref: str) -> str:
    return endpoint_ref


def _grafana_receiver_settings(channel: str, receiver_type: str) -> dict[str, str]:
    if receiver_type == "slack":
        return {"url": _alertmanager_receiver_url(channel)}
    if receiver_type == "email":
        return {"addresses": "ops@example.local"}
    return {"url": _alertmanager_receiver_url(channel)}


def _build_grafana_contact_points_payload() -> dict[str, Any]:
    contact_points = []
    for contact_point_id, spec in sorted(GRAFANA_CONTACT_POINT_EXPORT_BASELINE.items()):
        target_spec = ALERT_NOTIFICATION_TARGET_BASELINE[contact_point_id]
        template_spec = GRAFANA_TEMPLATE_EXPORT_BASELINE[spec.template_ref]
        receiver_type = _grafana_receiver_type(spec.endpoint_ref)
        contact_points.append(
            {
                "orgId": 1,
                "name": contact_point_id,
                "receivers": [
                    {
                        "uid": contact_point_id,
                        "type": receiver_type,
                        "settings": _grafana_receiver_settings(target_spec.channel, receiver_type),
                        "disableResolveMessage": False,
                        "title": template_spec.title_template,
                        "text": template_spec.body_template,
                    }
                ],
            }
        )
    return {"apiVersion": 1, "contactPoints": contact_points}


def _build_grafana_policy_routes(parent_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    children = [
        node
        for _, node in sorted(GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE.items())
        if node.parent_policy_id == parent_id
    ]
    for child in children:
        route_node: dict[str, Any] = {
            "receiver": child.contact_point_ref,
            "group_by": list(child.group_by),
            "group_wait": child.group_wait,
            "group_interval": child.group_interval,
            "repeat_interval": child.repeat_interval,
            "continue": child.continue_routing,
            "object_matchers": _object_matchers(child.matchers),
            "routes": _build_grafana_policy_routes(child.policy_id),
        }

        severity = child.matchers.get("severity")
        if severity is not None:
            mute_ids = [
                timing_id
                for timing_id, timing_spec in sorted(GRAFANA_MUTE_TIMING_EXPORT_BASELINE.items())
                if severity in set(timing_spec.allowed_severities)
            ]
            if mute_ids:
                route_node["mute_time_intervals"] = mute_ids

        out.append(route_node)
    return out


def _build_grafana_policies_payload() -> dict[str, Any]:
    root = GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE["root"]
    policies = [
        {
            "orgId": 1,
            "receiver": root.contact_point_ref,
            "group_by": list(root.group_by),
            "group_wait": root.group_wait,
            "group_interval": root.group_interval,
            "repeat_interval": root.repeat_interval,
            "routes": _build_grafana_policy_routes("root"),
        }
    ]
    return {"apiVersion": 1, "policies": policies}


def _build_grafana_mute_timings_payload() -> dict[str, Any]:
    mute_times = []
    for timing_id, timing_spec in sorted(GRAFANA_MUTE_TIMING_EXPORT_BASELINE.items()):
        mute_times.append(
            {
                "name": timing_id,
                "time_intervals": [
                    {
                        "times": [
                            {
                                "start_time": "00:00",
                                "end_time": "06:00",
                            }
                        ],
                        # Grafana provisioning expects weekday ranges in canonical order.
                        # sunday:saturday represents full-week mute interval.
                        "weekdays": ["sunday:saturday"],
                        "location": timing_spec.timezone,
                    }
                ],
            }
        )
    return {"apiVersion": 1, "muteTimes": mute_times}


def _build_grafana_templates_payload() -> dict[str, Any]:
    templates = []
    for template_id, template_spec in sorted(GRAFANA_TEMPLATE_EXPORT_BASELINE.items()):
        templates.append(
            {
                "orgId": 1,
                "name": template_id,
                "template": (
                    f'{{{{ define "{template_id}.title" }}}}{template_spec.title_template}{{{{ end }}}}\n'
                    f'{{{{ define "{template_id}.body" }}}}{template_spec.body_template}{{{{ end }}}}'
                ),
            }
        )
    return {"apiVersion": 1, "templates": templates}


_ARTIFACT_BUILDERS = {
    "alertmanager_config": _build_alertmanager_payload,
    "grafana_contact_points": _build_grafana_contact_points_payload,
    "grafana_policies": _build_grafana_policies_payload,
    "grafana_mute_timings": _build_grafana_mute_timings_payload,
    "grafana_templates": _build_grafana_templates_payload,
}


def render_reliability_alert_provisioning_artifacts() -> dict[str, str]:
    rendered: dict[str, str] = {}
    for artifact_id in RENDERED_PROVISIONING_ARTIFACT_ORDER:
        spec = RENDERED_PROVISIONING_ARTIFACTS_BASELINE[artifact_id]
        builder = _ARTIFACT_BUILDERS[artifact_id]
        payload = builder()
        rendered[spec.relative_path] = _render_yaml(payload)
    return rendered


def write_reliability_alert_provisioning_artifacts(base_dir: Path) -> list[Path]:
    rendered = render_reliability_alert_provisioning_artifacts()
    written_paths: list[Path] = []
    for relative_path, payload in rendered.items():
        file_path = base_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(payload, encoding="utf-8")
        written_paths.append(file_path)
    return written_paths


def validate_reliability_alert_provisioning_render_contract() -> list[str]:
    errors: list[str] = []

    expected_artifact_ids = set(RENDERED_PROVISIONING_ARTIFACT_ORDER)
    if set(_ARTIFACT_BUILDERS.keys()) != expected_artifact_ids:
        errors.append("_ARTIFACT_BUILDERS keys must match RENDERED_PROVISIONING_ARTIFACT_ORDER")

    root_nodes = [
        node
        for node in GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE.values()
        if node.parent_policy_id is None
    ]
    if len(root_nodes) != 1:
        errors.append("Grafana policy tree must have exactly one root node")

    receiver_ids = set(ALERTMANAGER_RECEIVER_EXPORT_BASELINE.keys())
    for alert_alias, route_spec in ALERTMANAGER_ROUTE_EXPORT_BASELINE.items():
        if route_spec.receiver not in receiver_ids:
            errors.append(
                f"{alert_alias}: Alertmanager route receiver does not exist: {route_spec.receiver}"
            )

    contact_point_ids = set(GRAFANA_CONTACT_POINT_EXPORT_BASELINE.keys())
    for policy_id, node in GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE.items():
        if node.contact_point_ref not in contact_point_ids:
            errors.append(
                f"{policy_id}: Grafana policy node references unknown contact point: {node.contact_point_ref}"
            )
        if policy_id != "root":
            if node.parent_policy_id is None:
                errors.append(f"{policy_id}: non-root policy node must define parent_policy_id")
            elif node.parent_policy_id not in GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE:
                errors.append(
                    f"{policy_id}: parent policy does not exist: {node.parent_policy_id}"
                )

    rendered_once = render_reliability_alert_provisioning_artifacts()
    rendered_twice = render_reliability_alert_provisioning_artifacts()
    if rendered_once != rendered_twice:
        errors.append("Rendered provisioning artifacts must be deterministic for identical input")

    expected_relative_paths = {
        spec.relative_path for spec in RENDERED_PROVISIONING_ARTIFACTS_BASELINE.values()
    }
    if set(rendered_once.keys()) != expected_relative_paths:
        errors.append("Rendered provisioning artifact paths must match baseline relative paths")

    return errors

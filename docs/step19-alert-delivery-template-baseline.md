# Step 19.5 - Alert Delivery Template Baseline

## Goal
Define deploy-ready alert delivery template baseline so notifications carry stable operational context (summary/description/runbook/ownership) without changing runtime-path behavior.

## Annotation & Label Schema Baseline
Delivery schema baseline is defined in:
- `server/app/reliability_alert_delivery_template_baseline.py`
  - `ALERT_DELIVERY_SCHEMA_BASELINE`
  - `REQUIRED_ALERT_LABELS`
  - `REQUIRED_ALERT_ANNOTATIONS`

Required annotations:
- `summary`
- `description`
- `runbook_ref`
- `runbook_url`

Required labels:
- `alertname`
- `severity`
- `service`
- `component`
- `alert_class`
- `owner_team`

## Contact-Point Template Variable Contract
Template variable baseline is defined in:
- `ALERT_TEMPLATE_VARIABLE_BASELINE`

Group-level contract:
- `group.receiver`
- `group.status`
- `group.group_labels`
- `group.common_labels`
- `group.common_annotations`
- `group.external_url`

Per-alert contract:
- `alert.status`
- `alert.labels`
- `alert.annotations`
- `alert.starts_at`
- `alert.ends_at`
- `alert.generator_url`
- `alert.fingerprint`
- `alert.summary`
- `alert.description`
- `alert.runbook_url`

## Grouped Notification Rendering Rules
Delivery templates render grouped notifications by design:
- group-level header fields use `Data.*` scope;
- per-alert section iterates individual alerts in the group;
- contract remains consistent with Step 19.4 grouping baseline.

## Runbook Link Formatting Baseline
Runbook link policy is defined in:
- `ALERT_RUNBOOK_LINK_FORMAT_BASELINE`

Baseline rule:
- prefer `runbook_url` annotation;
- fallback to deterministic URL from `runbook_ref` using canonical template;
- `page` and `ticket` severities require runbook link fields.

## Contact-Point Payload Baseline
Contact-point payload baseline is defined in:
- `ALERT_CONTACT_POINT_PAYLOAD_BASELINE`

Baseline contact-point families:
- `slack`
- `email`
- `webhook`

## Invariants
- Template layer renders canonical labels/annotations and does not invent new source-of-truth fields.
- Step 19.5 extends Step 19.4 suppression/grouping contract and does not change runtime instrumentation.
- Delivery schema must stay integration-agnostic across contact points.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Validation includes:
- Step 19.5 doc presence and required sections,
- per-alert required label/annotation schema checks,
- contact-point variable mapping checks (group vs per-alert),
- runbook link requirement checks for page/ticket severity,
- grouped notification payload consistency and doc-to-mapping alignment.

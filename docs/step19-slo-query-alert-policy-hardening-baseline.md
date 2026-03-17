# Step 19.2 - SLO Query Alias & Alert Policy Hardening Baseline

## Goal
Define deploy-ready SLO query alias and burn-rate alert policy mapping that can be transferred to Prometheus/Grafana/Cloud Monitoring stacks without changing runtime-path behavior.

## Recording Rule Alias Baseline
Canonical recording-rule aliases are defined in:
- `server/app/reliability_alert_policy_mapping.py`
  - `SLO_RECORDING_RULE_ALIAS_BASELINE`

Naming contract uses Prometheus-style recording alias shape:
- `level:metric:operations`

Required windows per SLI derive from burn-rate policy windows:
- `5m`, `30m`, `1h`, `6h`, `3d`

## Alert Rule Alias Baseline
Canonical alert aliases are defined in:
- `server/app/reliability_alert_policy_mapping.py`
  - `SLO_ALERT_RULE_ALIAS_BASELINE`
  - `SLO_ALERT_QUERY_MAPPING`

Alert alias shape baseline:
- `slo:<sli_key>:burn_<policy_id>`

Each `sli_key` x `policy_id` combination is required.

## Severity/Action Mapping
Policy-to-action baseline is defined in:
- `SLO_ALERT_SEVERITY_ACTION_BASELINE`

Policy set (from Step 19.1):
- `fast_page` -> `severity=page`, `action=page_on_call`
- `slow_page` -> `severity=page`, `action=page_on_call`
- `budget_ticket` -> `severity=ticket`, `action=open_ticket`

## Runbook Linkage
Each alert alias must include:
- `runbook_ref`
- `summary`

Baseline runbook reference namespace:
- `docs/runbooks/slo/<sli_key>.md`

## Invariants
- `19.2` does not change runtime instrumentation or request/WS/reconcile behavior.
- Security-invalid paths remain excluded from reliability SLI error accounting (as defined in `19.1`).
- Query/alert aliases remain aligned with Step 19.1 SLI/SLO/burn-rate policy contract.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Validation includes:
- Step 19.2 doc presence and required sections,
- recording alias naming and required windows,
- alert alias completeness (`sli_key` x `policy_id`),
- threshold/severity/action consistency with Step 19.1 policy,
- runbook linkage and query-template consistency,
- doc-to-mapping contract alignment.

# Step 18.4 - Dashboard/Alert Mapping Baseline

## Goal
Define dashboard-ready query and alert mapping on top of canonical observability contracts without changing runtime behavior.

## Constraints
- No runtime-path changes (`health/ready/auth/ws/reconcile` behavior is unchanged).
- Mapping must align with:
  - `server/app/observability_contract.py`
  - `server/app/observability_triage.py`
  - `server/app/observability_dashboard_mapping.py`

## Dashboard Query Baseline
Canonical query registry is defined in:
- `server/app/observability_dashboard_mapping.py` -> `DASHBOARD_QUERY_BASELINE`

Coverage includes:
- `readiness` (dependency degradations)
- `auth` (security reject trends)
- `ws` (security rejects / operational disconnects)
- `reconcile` (cleanup activity)
- logs/traces correlation views by `reason_class`

## Alert Mapping Baseline
Canonical alert registry is defined in:
- `server/app/observability_dashboard_mapping.py` -> `ALERT_RULE_BASELINE`

Required alignment:
- `reason_class` must be one of `operational|security|dependency`
- `primary_event` must exist in canonical event registry
- `query_ref` must point to an existing dashboard query
- `dashboard_id` must align with triage mapping by event domain

## Recording Rule Naming Baseline
Prometheus-style alias mapping is defined in:
- `server/app/observability_dashboard_mapping.py` -> `PROM_COUNTER_ALIAS_BASELINE`

Naming constraints:
- aliases use Prometheus counter naming style (`*_total`)
- alias keys are canonical counter keys from runtime observability surface
- dynamic dimensions stay in labels/query filters, not metric names

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Validation includes:
- presence and structure of 18.4 baseline artifacts,
- dashboard/alert registry consistency checks,
- prom-style alias naming checks,
- cross-contract compatibility with 18.1 and 18.3.

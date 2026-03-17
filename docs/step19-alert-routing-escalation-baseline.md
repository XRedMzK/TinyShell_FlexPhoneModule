# Step 19.3 - Alert Routing & Escalation Baseline

## Goal
Define deploy-ready alert routing and escalation policy baseline on top of Step 19.2 aliases without changing runtime-path behavior.

## Routing Label Contract
Canonical routing labels are defined in:
- `server/app/reliability_alert_routing_baseline.py`
  - `ALERT_ROUTING_LABEL_BASELINE`
  - `ROUTING_REQUIRED_LABEL_KEYS`

Required label set:
- `service`
- `component`
- `severity`
- `alert_class`
- `routing_key`
- `runbook_ref`
- `owner_team`

## Notification Target Classes
Notification target baseline is defined in:
- `ALERT_NOTIFICATION_TARGET_BASELINE`

Target classes:
- `pager`
- `ticket`
- `dashboard`

Canonical targets:
- `primary_oncall`
- `secondary_oncall`
- `ops_ticket_queue`
- `dashboard_only`

## Escalation Policy Baseline
Escalation mapping is defined in:
- `ALERT_ESCALATION_POLICY_BASELINE`

Policy invariants:
- `severity=page` must define `primary_target` and `escalation_target`.
- `severity=ticket` must route to non-pager target and must not escalate by default.
- Routing baseline extends Step 19.2 policy and keeps runtime-path unchanged.

## Runbook Ownership Baseline
Runbook ownership mapping is defined in:
- `ALERT_RUNBOOK_OWNERSHIP_BASELINE`

Each alert alias must define:
- `runbook_ref`
- `owner_team`
- escalation ownership context (`escalation_target` for page-class alerts)

## Invariants
- Step 19.3 does not add runtime instrumentation and does not change request/WS/reconcile behavior.
- Routing/escalation policy must remain consistent with Step 19.2 severity/action baseline.
- Every alert alias must have complete routing and ownership records.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Validation includes:
- Step 19.3 doc presence and required sections,
- alert alias routing coverage and required labels,
- severity -> target class consistency (`page` vs `ticket`),
- mandatory runbook ownership and escalation mapping,
- doc-to-mapping contract alignment.

# Step 21.1 - Recovery & Restore Baseline Definition

## Goal
Define Stage 21 recovery/restore baseline as a contract-definition step: recovery scope, source-of-truth boundaries, bounded-loss assumptions, closure criteria, and verification type without runtime-path changes.

## Recovery Scope
Stage 21 baseline scope includes:
- source-of-truth inventory for recoverable configuration surfaces;
- bounded-loss semantics for Redis-backed auth/signaling transient state;
- post-restore validation checklist for runtime and alerting provisioning acceptance;
- sandbox restore smoke and CI-friendly restore simulation as later substeps.

## Source-of-Truth Inventory Boundaries
Canonical source classes:
- Git-tracked mapping/contracts:
  - `server/app/reliability_alert_policy_export_baseline.py`
  - `server/app/reliability_alert_provisioning_artifacts_baseline.py`
  - `server/app/reliability_alert_provisioning_render.py`
- Git-tracked rendered artifacts (derived, not primary truth):
  - `server/generated/alertmanager/*.rendered.yml`
  - `server/generated/grafana/provisioning/alerting/*.rendered.yml`
- External runtime inputs:
  - runtime env/secrets (`FLEXPHONE_*`, JWT signing material)
- Transient runtime state:
  - Redis auth/signaling challenge/session/presence state

Boundary invariant:
- policy logic remains mapping-driven;
- rendered YAML remains derived artifacts;
- transient Redis state is not treated as durable business source-of-truth.

## Bounded-Loss Assumptions
Bounded-loss assumptions for Stage 21:
- Redis-backed auth/signaling state can be lost on store-loss/restart;
- expected convergence path remains `reconnect/re-auth/startup reconciliation`;
- restore acceptance focuses on converged correctness, not full resurrection of transient sessions/challenges.

## Invariants
- Step 21.1 does not change production runtime-path.
- Step 21.1 does not change auth/ws/reconcile behavior or failure semantics.
- Recovery contract must keep file-provisioning compatibility path for Grafana and config/reload compatibility path for Alertmanager.
- Restore validation must be deterministic enough for runbook/checklist usage.

## Closure Criteria
Step 21.1 is closed when:
- baseline doc and mapping module are present;
- Stage 21 substep contract (`21.1`-`21.6`) is defined;
- source-of-truth inventory, bounded-loss assumptions, and verification types are explicit;
- build-level checker validates contract presence and consistency.

## Verification Type
- `build check`

## Stage 21 Substep Contract
- `21.1` — stage definition (scope/invariants/closure criteria/verification type). `[check: build check]`
- `21.2` — source-of-truth / backup-restore inventory baseline. `[check: build check]`
- `21.3` — Redis loss/restart recovery semantics baseline. `[check: build check]`
- `21.4` — post-restore runtime validation checklist baseline. `[check: manual runtime check]`
- `21.5` — sandbox restore smoke/runbook baseline. `[check: manual runtime check]`
- `21.6` — CI-friendly restore simulation gate baseline. `[check: build check]`

## Non-Goals
- no production failover orchestration in 21.1;
- no HA-cluster semantics implementation for Grafana/Alertmanager in 21.1;
- no runtime mutation of provisioning ownership boundaries in 21.1.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_recovery_restore_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- Step 21.1 doc required sections;
- recovery source-of-truth registry contract;
- bounded-loss/convergence contract fields;
- Stage 21 substep verification-type mapping completeness.

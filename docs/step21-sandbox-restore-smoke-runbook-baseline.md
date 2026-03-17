# Step 21.5 - Sandbox Restore Smoke / Runbook Baseline

## Goal
Validate recovery as an isolated sandbox rehearsal of the documented procedure, without introducing or enabling any restore path in production runtime.

## Scope
Step 21.5 validates that recovery procedure is reproducible from canonical inputs:
- Git-managed code/contracts/mapping/rendered artifacts;
- operator-injected sandbox env/secrets;
- sandbox startup/lifespan admission;
- provisioning acceptance;
- post-restore runtime proof set;
- Redis bounded-loss convergence after sandbox restart/loss.

## Non-Goals
- no activation of restore logic in production runtime-path;
- no exact resurrection requirement for transient Redis keys/Pub/Sub history;
- no substitution of Grafana file provisioning with HTTP provisioning API semantics;
- no use of production secrets/endpoints/network targets.

## Recovery Rehearsal Phases

### 1) Sandbox Preparation
- isolated disposable sandbox only;
- dedicated Redis/container/runtime paths;
- sandbox env/secrets only.

### 2) Canonical Input Materialization
- Git checkout state as baseline source;
- deterministic rendered artifacts validated against mapping/drift contract.

### 3) Service Startup / Admission
- app startup/lifespan completes;
- readiness stays contract-compatible (green only with dependencies, fail-closed otherwise).

### 4) Provisioning Acceptance
- Grafana alerting accepted via file provisioning path;
- Alertmanager config validated and accepted via startup/reload path.

### 5) Post-Restore Runtime Validation
- execute Step 21.4 runtime proof set (`health/ready/auth/ws/observability/provisioning`).

### 6) Redis Bounded-Loss Rehearsal
- sandbox Redis restart/loss simulation;
- stale challenge fail-closed;
- fresh challenge + re-auth + ws reconnect convergence succeeds.

## Invariants
- Step 21.5 does not change production runtime-path.
- Sandbox restore smoke is isolated and disposable.
- Recovery success means runtime contract convergence, not replay of every transient Redis event/key.
- File provisioning and Alertmanager reload semantics remain canonical acceptance paths.

## Closure Criteria
Step 21.5 is closed when manual sandbox rehearsal confirms:
- canonical-input restore rehearsal is executable end-to-end;
- provisioning acceptance remains valid through canonical path;
- Step 21.4 runtime checklist remains green after restore rehearsal;
- Redis restart/loss rehearsal yields fail-closed stale-state rejection and successful fresh re-auth/reconnect convergence.

## Verification Type
- `manual runtime check`

## Runbook Harness
Primary harness:
- `server/tools/run_recovery_restore_sandbox_smoke.py`

Harness composition:
- uses `server/tools/check_alert_provisioning_artifacts.py` (canonical input + drift contract)
- uses `server/tools/run_post_restore_runtime_validation_smoke.py` (Step 21.4 runtime proof)
- includes Redis restart/loss bounded-loss convergence rehearsal.

## Runtime Command
Run from server directory with Docker group context:

```bash
cd server
sg docker -c '.venv_tmpcheck/bin/python tools/run_recovery_restore_sandbox_smoke.py'
```

Expected success markers include:
- `Canonical input checks: OK`
- `Post-restore runtime proof set (21.4): OK`
- `Redis bounded-loss convergence rehearsal: OK`
- `Sandbox restore smoke rehearsal: OK`

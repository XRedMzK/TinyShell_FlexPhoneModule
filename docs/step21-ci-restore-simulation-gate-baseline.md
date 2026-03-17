# Step 21.6 - CI Restore Simulation Gate Baseline

## Goal
Make recovery/restore rehearsal from Steps 21.1-21.5 mandatory in CI through an isolated simulation gate that validates recoverability contract, not exact restoration of all transient runtime artifacts.

## CI Gate Scope
Step 21.6 introduces a dedicated CI job that validates:
- baseline/build contracts from Steps 21.1-21.3;
- canonical input materialization and drift-safe artifact surface;
- post-restore runtime proof set from Step 21.4;
- sandbox restore rehearsal and Redis bounded-loss convergence from Step 21.5.

No production runtime-path changes are introduced by this step.

## Workflow Baseline
Workflow file:
- `.github/workflows/recovery-restore-ci.yml`

Job baseline:
- isolated Linux runner;
- server-directory execution;
- canonical script-based checks only;
- disposable sandbox containers/state for simulation.

## Required CI Checks
Gate runs, in order:
1. `python -m compileall app tools`
2. `python tools/check_recovery_restore_baseline.py`
3. `python tools/check_recovery_restore_inventory_baseline.py`
4. `python tools/check_recovery_restore_redis_semantics_baseline.py`
5. `python tools/run_recovery_restore_sandbox_smoke.py`

Acceptance criteria:
- all commands pass;
- any contract drift, provisioning incompatibility, runtime proof failure, or convergence regression fails the pipeline.

## Isolation Invariant
- gate runs only in disposable CI sandbox;
- no production secrets/endpoints/runtime resources;
- no mutation of production restore/runtime mode.

## Recoverability Contract Invariant
- gate validates recoverability contract via canonical provisioning + runtime revalidation + bounded-loss convergence;
- gate does not require replay or exact resurrection of every transient Redis key/Pub/Sub event.

## Platform Compatibility Notes
- Grafana acceptance is validated through file provisioning semantics.
- Alertmanager acceptance includes config validation and startup/reload path compatibility.
- Redis disruption checks validate bounded-loss convergence semantics, not event replay completeness.

## Invariants
- Step 21.6 extends Steps 21.1-21.5 and preserves runtime-path neutrality.
- CI simulation remains deterministic for the same repository state and checker set.
- Canonical source-of-truth boundaries from Step 21.2 remain unchanged.

## Build-Level Verification
Step 21.6 verification includes:
- workflow presence and required command surface;
- local checker/compile compatibility;
- CI-equivalent sandbox restore simulation proof.

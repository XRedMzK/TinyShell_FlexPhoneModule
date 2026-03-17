# Step 21.3 - Redis Loss/Restart Recovery Semantics Baseline

## Goal
Define Redis loss/restart recovery semantics for auth/signaling transient state so correctness is recovered by convergence (`reconnect -> re-auth if needed -> startup reconciliation`), not by exact transient-state resurrection.

## Redis State Classification
Redis-backed auth/signaling state is classified as:
- transient runtime coordination state;
- bounded-loss by contract;
- non-durable restore target for application correctness.

## Recovery Event Baseline
Recovery events covered by the baseline:
- `redis_loss`
- `redis_restart`
- `pubsub_gap`
- `instance_restart`

## Auth Challenge Recovery Semantics
- Challenge keys are ephemeral TTL-bound objects.
- Missing/expired/inconsistent challenge state after Redis loss/restart must fail closed.
- Allowed outcomes:
  - `missing_challenge -> verify_fail_closed`
  - `expired_challenge -> verify_fail_closed`
  - `fresh_challenge -> reauth_path`

## Signaling Recovery Semantics
- `missed_pubsub_allowed = true`
- `stale_session_rejected = true`
- `phantom_presence_not_authoritative = true`
- `reconnect_reconciliation_required = true`
- exact transient-state restoration is not required for correctness.

## Startup Reconciliation Assumptions
Startup reconciliation must treat Redis signaling/session state as potentially:
- empty;
- partial;
- stale.

Runtime-visible truth is rebuilt only from currently valid state.

## Expected Convergence Path
Ordered convergence path:
1. `reconnect`
2. `re-auth_if_needed`
3. `startup_reconciliation`

## Invariants
- Step 21.3 does not change production runtime-path.
- Verify path stays fail-closed on missing/expired/inconsistent challenge state.
- Pub/Sub is treated as at-most-once bounded-loss fan-out.
- Recovery success is defined as convergence of valid clients and rejection of stale/invalid state.

## Closure Criteria
Step 21.3 is closed when:
- Redis recovery events and auth/signaling outcomes are explicit and checker-validated;
- fail-closed auth outcomes are explicit;
- convergence path is explicit and checker-validated;
- startup reconciliation assumptions are explicit.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_recovery_restore_redis_semantics_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- Step 21.3 doc required sections;
- recovery event coverage and allowed outcomes;
- signaling invariants and fail-closed auth constraints;
- convergence path and startup assumptions completeness.

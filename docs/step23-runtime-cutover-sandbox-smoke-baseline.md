# Step 23.4 - Runtime Cutover Sandbox Smoke Baseline

## Goal
Validate that runtime cutover modes (`pubsub_legacy`, `dual_write_shadow`, `durable_authoritative`) behave deterministically in isolated sandbox runtime, including mismatch handling and rollback boundaries.

## Scope
Step 23.4 validates runtime behavior for signaling control-plane only:
- mode switching sequence and mode-local behavior;
- primary-truth boundary in `dual_write_shadow`;
- mismatch detection/classification/action visibility;
- rollback reversibility after degradation;
- reconnect/replay/pending-recovery behavior in durable path.

Step 23.4 is a manual runtime check in isolated sandbox and does not activate production cutover.

## Sandbox Topology
- isolated backend + isolated Redis sandbox;
- two authenticated signaling clients per phase;
- runtime mode passed via `FLEXPHONE_SIGNALING_DELIVERY_MODE`;
- durable stream + consumer group used for shadow-read and replay proof.

## Scenario Matrix
- A: `pubsub_legacy` happy-path signaling flow (`invite/cancel`) and reconnect-safe baseline.
- B: `dual_write_shadow` flow with durable append + shadow-read equivalence check.
- C: forced mismatch in `dual_write_shadow` (`legacy_ok_durable_append_fail`) with deterministic action (`block_cutover_progression`) and promotion block.
- D: rollback `dual_write_shadow -> pubsub_legacy` and legacy flow re-validation.
- E: `durable_authoritative` flow using durable append/live delivery, reconnect replay, pending recovery, dedup proof.
- F: rollback boundary `durable_authoritative -> dual_write_shadow` and post-rollback signaling flow re-validation.

## Acceptance Criteria
- each mode passes at least one signaling happy-path flow;
- `dual_write_shadow` keeps legacy apply path as primary truth;
- forced mismatch is classified deterministically and blocks promotion;
- durable path proves reconnect replay + pending recovery + dedup behavior;
- rollback boundaries are executable without manual state surgery;
- proof output is deterministic enough for manual runtime verification.

## Expected Observable Outcomes
- mode labels in smoke proof sequence;
- mismatch class/action fields for forced mismatch scenario;
- durable scenario proof for append/replay/pending/dedup;
- rollback reason and rollback mode transitions visible in proof output.

## Closure Criteria
Step 23.4 is closed when:
- doc and runner are present;
- isolated sandbox smoke executes all scenario classes A-F;
- manual runtime check reports pass and proof output is captured in verification log.

## Verification Type
- `manual runtime check`

## Manual Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_runtime_cutover_sandbox_smoke.py
```

Success marker:
- `Runtime cutover sandbox smoke: OK`

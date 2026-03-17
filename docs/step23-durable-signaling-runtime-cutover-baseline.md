# Step 23.1 - Durable Signaling Runtime Cutover Baseline

## Goal
Define runtime cutover baseline from Pub/Sub-bounded-loss signaling path to durable authoritative signaling coordination path, without enabling production cutover in Step 23.1.

## Scope
Step 23.1 defines:
- cutover scope for authoritative vs ephemeral signaling delivery roles;
- rollout modes and transition boundaries;
- event migration matrix baseline;
- rollback/abort boundaries;
- closure criteria and verification type.

Step 23.1 is contract-definition only and does not switch production runtime-path.

## Rollout Modes
Canonical rollout modes:
- `pubsub_legacy`
- `dual_write_shadow`
- `durable_authoritative`

Mode intent:
- `pubsub_legacy`: current runtime path; Pub/Sub carries signaling delivery path.
- `dual_write_shadow`: authoritative candidates are dual-written to durable stream while legacy path remains active for runtime behavior parity checks.
- `durable_authoritative`: authoritative events read/apply from durable stream path; Pub/Sub remains acceleration/hint channel.

## Feature Flag and Runtime Switch Boundary
Runtime mode key:
- `FLEXPHONE_SIGNALING_DELIVERY_MODE`

Step 23.1 boundary:
- defines allowed modes and transitions only;
- does not activate mode switch in production runtime.

## Event Migration Matrix Baseline
Migration rule by event class:
- `authoritative_durable_coordination_events`:
  `pubsub_legacy -> dual_write_shadow -> durable_authoritative`
- `ephemeral_fanout_hints`:
  remain Pub/Sub hints in all rollout modes
- `derived_projection_events`:
  remain derived/runtime projection layer and never become source-of-truth

Authoritative transition invariant:
- negotiation-critical transitions are migrated to durable authoritative path;
- reconnect/replay semantics must preserve correctness without requiring missed Pub/Sub replay.

## Rollback and Abort Boundaries
Allowed rollback boundaries:
- `durable_authoritative -> dual_write_shadow` (immediate rollback path)
- `dual_write_shadow -> pubsub_legacy` (full fallback)

Direct `durable_authoritative -> pubsub_legacy` is out of baseline fast-path and must pass through `dual_write_shadow`.

Abort conditions (baseline):
- durable append failures beyond tolerance;
- replay/apply idempotency violations;
- ordering scope violation;
- unresolved pending recovery regressions;
- readiness/correctness-path degradation under cutover mode.

## Invariants
- authoritative correctness must not depend on Pub/Sub-only delivery;
- rollout remains feature-flag-gated and reversible;
- idempotent apply remains mandatory during and after cutover;
- ordering remains scoped and deterministic;
- dual-write mode cannot change canonical correctness semantics;
- production-path switch is out of scope for Step 23.1.

## Closure Criteria
Step 23.1 is closed when:
- doc, module, and checker are present;
- rollout mode contract is explicit and validated;
- event migration matrix baseline is explicit and validated against Step 22 inventory;
- rollback/abort boundaries are explicit and checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_durable_signaling_runtime_cutover_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- required Step 23.1 doc sections;
- rollout mode contract and feature-flag boundary;
- event migration matrix coverage and class-to-mode rules;
- rollback/abort boundary completeness and invariant consistency.

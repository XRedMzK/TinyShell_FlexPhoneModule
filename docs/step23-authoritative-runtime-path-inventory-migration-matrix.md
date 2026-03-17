# Step 23.2 - Authoritative Runtime Path Inventory + Migration Matrix

## Goal
Detail authoritative runtime transitions and migration matrix for durable signaling runtime cutover, so writer/read/apply ownership and mode behavior are explicit per transition.

## Scope
Step 23.2 defines:
- authoritative runtime transition inventory for correctness-critical signaling transitions;
- migration matrix per rollout mode (`pubsub_legacy`, `dual_write_shadow`, `durable_authoritative`);
- read/write/apply ownership boundaries;
- cutover safety rules and rollback constraints per transition.

Step 23.2 is contract-definition only and does not perform production runtime cutover.

## Authoritative Runtime Transition Inventory
Each authoritative runtime transition includes:
- `transition_id`
- `event_name`
- `scope`
- `producer`
- `apply_owner`
- `legacy_delivery_path`
- `target_delivery_path`
- `lost_live_delivery_allowed`
- `replay_required`
- `dedup_required`
- `rollback_allowed_until`
- `projection_dependency`

Authoritative transition inventory is derived from Step 22.2 class `authoritative_durable_coordination_events` and excludes ephemeral/projection classes.

## Migration Matrix by Rollout Mode
Per authoritative transition, mode behavior is fixed:

- `pubsub_legacy`:
  writer/read path uses `pubsub_live_only`; no stream shadow read.

- `dual_write_shadow`:
  writer path uses `pubsub_live_plus_stream_shadow`;
  read/apply remains legacy path for runtime parity checks;
  shadow-read equivalence is required.

- `durable_authoritative`:
  writer/read/apply path uses durable stream primary (`durable_stream_primary*`);
  Pub/Sub remains best-effort fan-out hint only.

Rollback boundaries:
- `durable_authoritative -> dual_write_shadow`
- `dual_write_shadow -> pubsub_legacy`

## Read/Write Ownership Boundaries
Ownership baseline:
- authoritative append owner: `authoritative_transition_writer`
- authoritative stream read owner: `authoritative_transition_reader`
- authoritative apply owner: `authoritative_state_machine`
- pubsub hint owner: `fanout_hint_dispatcher`
- projection owner: `projection_builder`

Ownership invariant:
- projection/presence layers never become authoritative source-of-truth.

## Cutover Safety Rules
- transition may enter `durable_authoritative` only with completed identity/order/dedup/replay contract from Step 22.3;
- `dual_write_shadow` is not successful until shadow-read equivalence is confirmed;
- rollback path must preserve already committed authoritative state;
- rollout remains feature-flag gated and deterministic per transition;
- build-level validation must not require production secrets/endpoints.

## Invariants
- all authoritative transitions are replay-required and dedup-required;
- lost live fan-out is tolerated only with durable replay path available;
- non-authoritative classes remain outside authoritative migration matrix;
- rollout semantics stay consistent with Step 23.1 mode contract;
- production runtime cutover is out of scope for Step 23.2.

## Closure Criteria
Step 23.2 is closed when:
- doc, module, and checker are present;
- authoritative transition inventory is complete and unambiguous;
- migration matrix per transition/mode is explicit and checker-enforced;
- read/write/apply ownership boundaries are explicit and checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_durable_signaling_runtime_path_inventory.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- required Step 23.2 doc sections;
- authoritative transition inventory coverage from Step 22.2;
- per-mode migration matrix consistency with Step 23.1;
- ownership/safety-rule invariant consistency.

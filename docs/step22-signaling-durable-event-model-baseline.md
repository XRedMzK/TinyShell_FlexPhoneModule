# Step 22.3 - Signaling Durable Event Model Baseline

## Goal
Define a strict durable event contract for authoritative signaling coordination events: identity, scoped ordering, dedup, bounded retention, replay boundaries, and reconciliation semantics.

## Authoritative Event Model Inventory
Durable model applies only to `authoritative_durable_coordination_events` from Step 22.2 inventory baseline.

Each authoritative event must define:
- domain-stable identity (`event_id`);
- durable stream identity (`stream_entry_id`);
- mandatory ordering scope;
- write/apply dedup expectations;
- replay/reconciliation behavior;
- bounded retention window.

## Durable Event Identity Contract
Identity requirements:
- `event_id` is mandatory and domain-stable for idempotent processing;
- `stream_entry_id` is mandatory as durable log position;
- `schema_version` is mandatory for contract evolution;
- backend clock is source of truth for `issued_at`.

Identity separation rule:
- `event_id` defines domain idempotency identity;
- `stream_entry_id` defines transport/log position identity.

## Ordering Contract
Ordering requirements:
- ordering is guaranteed only within `ordering_scope`;
- `ordering_scope` is mandatory for every authoritative durable event;
- no cross-scope global ordering guarantees are part of the baseline contract.

Ordering scopes remain constrained to canonical domains (`call_id`, `participant_id`, `service`).

## Dedup Contract
Dedup requirements:
- write-side dedup is required for authoritative durable events;
- consume/apply dedup is required and must be idempotent by `event_id`;
- repeated apply for same `event_id` is no-op at domain level.

## Retention Contract
Retention requirements:
- retention is bounded and policy-driven;
- trim strategy may use stream length/time-window policies;
- retention must preserve minimum reconciliation window;
- retention cannot remove events required for active reconnect/recovery window.

## Replay Contract
Replay requirements:
- replay source is authoritative durable stream only;
- replay boundary is explicit (`last_applied_event_id`, `last_acknowledged_stream_entry_id`);
- replay must be idempotent;
- Pub/Sub hints are not replay source.

## Reconciliation Contract
Reconciliation requirements:
- startup/reconnect reconciliation must rebuild coordination truth from authoritative durable events;
- stale local assumptions must be discarded;
- projection state remains derived and rebuildable from authoritative durable source;
- correctness must not depend on delivery of ephemeral fan-out hints.

## Invariants
- every authoritative durable event has `event_id` and `stream_entry_id`;
- ordering scope is explicit and scoped-only;
- idempotent apply is mandatory for authoritative events;
- replay and reconciliation are authoritative-stream-based;
- retention is bounded and reconciliation-safe;
- projection state is never source of truth;
- Pub/Sub remains optional acceleration channel only;
- production runtime-path switch is out of scope for Step 22.3.

## Closure Criteria
Step 22.3 is closed when:
- doc, module, and checker are present;
- durable event model is complete for all authoritative events from Step 22.2;
- identity/order/dedup/retention/replay/reconciliation contracts are explicit and validated;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_signaling_durable_event_model_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- required Step 22.3 doc sections;
- full authoritative-event model coverage from Step 22.2 inventory;
- durable identity/order/dedup/retention/replay/reconciliation invariants;
- no contract conflicts between Step 22.2 and Step 22.3 baselines.

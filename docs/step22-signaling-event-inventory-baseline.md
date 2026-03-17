# Step 22.2 - Signaling Event Inventory Baseline

## Goal
Classify signaling events by correctness role (not transport shape) to make critical coordination transitions explicit and prevent correctness dependency on best-effort Pub/Sub fan-out.

## Classification Principle
Event inventory is classified by impact on correctness:
- if event loss can break coordination correctness, event is authoritative durable;
- if event loss only delays reaction and convergence is still possible, event is ephemeral hint;
- if event can be recomputed from canonical state, event is derived projection.

## Inventory Classes
- `authoritative_durable_coordination_events`
- `ephemeral_fanout_hints`
- `derived_projection_events`

## Classification Questions
For each event class, answer:
1. Does event loss break coordination correctness?
2. Must event be replayable after restart/disconnect?
3. Can event be recomputed from more canonical state?
4. Is event only a low-latency fan-out hint?

## Canonical Event Inventory
### Authoritative Durable Coordination Events
- `session.created`
- `session.join-requested`
- `session.join-accepted`
- `session.member-added`
- `session.member-removed`
- `negotiation.offer-created`
- `negotiation.offer-rolled-back`
- `negotiation.answer-committed`
- `negotiation.ice-epoch-started`
- `call.terminated`
- `session.authoritative-state-changed`

### Ephemeral Fan-out Hints
- `hint.new-authoritative-event`
- `hint.peer-resync`
- `hint.presence-ping`
- `hint.instance-sync-nudge`
- `hint.candidate-available`

### Derived Projection Events
- `projection.presence-changed`
- `projection.session-changed`
- `projection.active-call-changed`
- `projection.observability-emitted`

## Invariants
- every signaling event class must belong to exactly one inventory class;
- no event may be both authoritative durable and ephemeral hint;
- negotiation-critical transitions must be in authoritative durable class;
- derived projection events are never source of truth;
- ephemeral hints may accelerate convergence but are not required for correctness;
- production runtime-path switch is out of scope for Step 22.2.

## Closure Criteria
Step 22.2 is closed when:
- doc, module, and checker are present;
- event inventory is complete and unambiguous across three classes;
- invariants are encoded and checker-enforced;
- negotiation-critical transitions are classified as authoritative durable;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_signaling_event_inventory_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- required doc sections and canonical event lists;
- module-level inventory completeness and invariant enforcement;
- no event-class ambiguity and no authoritative/ephemeral overlap;
- negotiation-critical events classified as authoritative durable.

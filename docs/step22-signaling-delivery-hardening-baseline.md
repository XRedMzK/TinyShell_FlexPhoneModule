# Step 22.1 - Signaling Delivery Hardening Baseline

## Goal
Define Stage 22 baseline for signaling delivery hardening: reduce correctness dependency on best-effort Pub/Sub fan-out by introducing a durable coordination contract for critical signaling events, without changing production runtime-path.

## Scope
Step 22.1 baseline scope includes:
- event-class inventory for signaling delivery;
- authoritative vs ephemeral boundary definitions;
- durable coordination transport baseline (Redis Streams or equivalent append-only log model);
- ordering, dedup, replay/reconciliation assumptions;
- retention and migration boundaries from Pub/Sub-only fan-out.

## Event Class Boundary
Signaling events are split into classes:
- `authoritative_durable_coordination_events`
- `ephemeral_fanout_hints`
- `derived_projection_events`

Boundary rule:
- critical coordination transitions must not rely on best-effort Pub/Sub alone;
- ephemeral hints remain allowed for low-cost fan-out/latency optimization;
- projections (presence/session views) remain derived, not canonical truth.

## Durable Coordination Baseline
Durable coordination baseline requirements:
- critical coordination events are replayable or reconstructable from durable source;
- event identity and dedup semantics are explicit;
- ordering scope is explicit per event domain (`call_id`, `nickname`, or service-level scope);
- retention is bounded and policy-driven.

Preferred baseline transport:
- Redis Streams (or equivalent append-only durable event log abstraction).

## Invariants
- No correctness dependency on Pub/Sub best-effort fan-out alone for critical transitions.
- Reconnect/startup reconciliation remains valid if fan-out hints were missed.
- Event identity and dedup semantics are explicit for authoritative events.
- Presence/session projections remain derived, not canonical.
- No production-path switch in Step 22.1.

## Closure Criteria
Step 22.1 is closed when:
- baseline doc, module, and checker are present;
- event inventory is complete and unambiguous;
- authoritative/ephemeral/projection boundaries are explicit;
- durable transport/replay/ordering/retention assumptions are explicit;
- checker validates contract completeness and invariants.

## Verification Type
- `build check`

## Stage 22 Substep Draft
- `22.1` — signaling delivery hardening baseline definition. `[check: build check]`
- `22.2` — event inventory baseline (`authoritative durable` vs `ephemeral`). `[check: build check]`
- `22.3` — durable event model baseline (IDs/order/dedup/retention/replay). `[check: build check]`
- `22.4` — sandbox durable signaling smoke baseline. `[check: manual runtime check]`
- `22.5` — CI durable signaling simulation gate baseline. `[check: build check]`

## Non-Goals
- no immediate replacement of current Pub/Sub runtime-path in 22.1;
- no production migration cutover in 22.1;
- no requirement to replay every historical transient fan-out event.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_signaling_delivery_hardening_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- Step 22.1 doc required sections;
- event-class inventory coverage and ownership boundaries;
- durable coordination invariants and transport assumptions;
- stage draft and closure criteria presence.

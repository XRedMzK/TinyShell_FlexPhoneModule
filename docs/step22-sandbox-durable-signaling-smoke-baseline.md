# Step 22.4 - Sandbox Durable Signaling Smoke Baseline

## Goal
Validate in isolated sandbox that authoritative durable signaling coordination can survive missed live fan-out via replay/recovery path, without changing production runtime-path.

## Scope
Step 22.4 validates a runtime smoke proof set for authoritative durable events from Step 22.2/22.3:
- durable append before live fan-out;
- reconnect replay after missed live delivery;
- pending recovery (`read_without_ack -> consumer_recovery -> ack`);
- idempotent apply (duplicate delivery attempt does not double-apply).

Step 22.4 is sandbox-only and does not introduce production cutover.

## Scenario Matrix

### A) Durable append + live delivery
- append authoritative event into Redis Stream;
- deliver live signaling message to online peer over WebSocket;
- verify stream entry identity and single apply.

### B) Disconnect before live delivery, then replay
- disconnect peer before live delivery path;
- append authoritative event while peer is offline;
- reconnect peer and consume event via durable replay path.

### C) Read without ack, consumer restart, pending recovery
- read authoritative event via consumer group without `XACK`;
- verify pending state is visible;
- recover with another consumer (`XAUTOCLAIM`) and acknowledge.

### D) Duplicate delivery attempt, idempotent apply
- deliver duplicate authoritative event identity;
- verify apply layer treats duplicate as dedup hit (no second state apply).

## Proof Set
Smoke output must include:
- stream key + consumer group;
- produced `event_id` + `stream_entry_id`;
- live delivery result;
- replay delivery result;
- pending before/after recovery;
- dedup result and apply counts.

## Invariants
- authoritative durable events are append-first and replay-capable;
- replay source is durable stream, not Pub/Sub hint channel;
- WebSocket disconnect/reconnect is treated as expected runtime path;
- duplicate apply by same `event_id` is idempotent no-op;
- readiness/fail-closed semantics remain unchanged;
- sandbox execution is isolated/disposable and does not alter production runtime-path.

## Closure Criteria
Step 22.4 is closed when manual sandbox smoke confirms:
- all four scenarios (A-D) pass;
- proof set is printed with deterministic PASS/FAIL markers;
- stream pending recovery and replay are observed in sandbox;
- idempotent dedup behavior is confirmed;
- script exits non-zero on any scenario failure.

## Verification Type
- `manual runtime check`

## Smoke Harness
Primary harness:
- `server/tools/run_durable_signaling_sandbox_smoke.py`

## Runtime Command
Run from server directory (Docker-enabled shell):

```bash
cd server
sg docker -c '.venv_tmpcheck/bin/python tools/run_durable_signaling_sandbox_smoke.py'
```

Expected success marker:
- `Durable signaling sandbox smoke: OK`

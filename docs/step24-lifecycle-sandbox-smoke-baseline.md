# Step 24.5 - Lifecycle Sandbox Smoke Baseline

## Goal
Validate that Step 24 lifecycle contracts (`24.2-24.4`) hold in deterministic sandbox runtime simulation, including negotiation collisions, reconnect/recovery actions, and terminal handling.

## Scope
Step 24.5 validates scenario-level runtime behavior for peer/session lifecycle:
- happy-path lifecycle transition sequence;
- glare/collision handling via `polite`/`impolite` role actions;
- transient disconnect recovery without premature terminal close;
- failed ICE escalation to restart negotiation path;
- late/stale signaling handling after recovery or close;
- close/terminal behavior during pending recovery.

Step 24.5 is an isolated sandbox smoke and does not change production runtime behavior.

## Scenario Matrix
- A: happy-path lifecycle (`session_new -> ... -> session_closed`).
- B: simultaneous renegotiation glare (`polite` rollback path, `impolite` ignore path).
- C: transient disconnect recovery (`session_connected -> session_degraded -> session_connected`).
- D: failed ICE restart recovery (`session_connected -> session_degraded -> session_recovering -> session_negotiating -> session_connecting -> session_connected`).
- E: late/stale signaling handling after recovery (`late answer` ignored, state unchanged).
- F: close during pending recovery (`session_recovering -> session_failed -> session_closed`, late signal rejected).

## Acceptance Criteria
- each scenario reaches expected deterministic terminal/recovery state;
- glare handling follows Step 24.3 deterministic role policy;
- `disconnected` is treated as recovery-eligible, not immediate terminal failure;
- failed ICE path triggers restart negotiation flow per Step 24.4;
- stale/late signaling cannot mutate closed session ownership;
- runner emits deterministic proof-set and explicit pass/fail markers.

## Expected Proof Set
- `scenario_id`
- `start_state`
- `trigger_sequence`
- `role` (for glare cases)
- `deterministic_action`
- `end_state`
- `status`

Global proof fields:
- `overall_status`
- `scenarios_passed`
- `scenarios_total`

## Closure Criteria
Step 24.5 is closed when:
- doc and sandbox smoke runner are added;
- runner executes scenarios A-F successfully in local sandbox;
- manual runtime check output includes explicit success marker.

## Verification Type
- `manual runtime check`

## Manual Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_sandbox_smoke.py
```

Success marker:
- `WebRTC lifecycle sandbox smoke: OK`

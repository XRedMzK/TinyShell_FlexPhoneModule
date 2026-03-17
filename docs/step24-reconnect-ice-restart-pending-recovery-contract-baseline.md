# Step 24.4 - Reconnect / ICE-Restart / Pending-Recovery Contract Baseline

## Goal
Define deterministic recovery contract for reconnect, ICE restart, and pending-recovery lifecycle over WebRTC peer session state machine.

## Scope
Step 24.4 defines:
- recovery trigger classes mapped to `iceConnectionState` / `connectionState`;
- eligibility rules for reconnect vs ICE restart vs terminal close;
- pending-recovery ownership and lifecycle schema;
- signaling requirements for ICE restart negotiation path;
- timeout/escalation policy;
- deterministic actions for transient disconnect, failed ICE, late recovery, and stale terminal signaling.

Step 24.4 is contract-definition only and does not modify runtime behavior.

## Recovery Trigger Classes
Canonical trigger classes:
- `transient_disconnect`
- `hard_ice_failure`
- `aggregate_connection_failure`
- `late_recovery`
- `abandoned_recovery`
- `terminal_close`

`disconnected` is non-terminal by default; `closed` is terminal.

## Eligibility Rules
- `transient_disconnect`: reconnect-eligible, observe/timeout path first.
- `hard_ice_failure`: ICE restart eligible.
- `aggregate_connection_failure`: restart-or-close escalation.
- `late_recovery`: ignore and log deterministic late-recovery path.
- `abandoned_recovery`: close/recreate path.
- `terminal_close`: reject recovery, new session required.

## Pending-Recovery Ownership and Schema
Pending-recovery schema fields:
- `recovery_id`
- `session_id`
- `peer_id`
- `trigger_class`
- `started_at_ms`
- `deadline_ms`
- `owner`
- `allowed_action_set`
- `escalation_target`
- `status`

Ownership:
- pending recovery owner is client lifecycle;
- metadata owner is signaling session metadata;
- only one active pending-recovery attempt per session.

## ICE-Restart Signaling Requirements
- ICE restart requires negotiation owner;
- restart requires restart-offer + offer/answer cycle;
- restart must follow Step 24.3 glare/collision policy;
- restart for terminal session is rejected.

## Timeout and Escalation Policy
- transient disconnect grace window is bounded;
- recovery attempt timeout is bounded;
- recovery attempts per epoch are bounded;
- timeout escalation path is deterministic (`observe -> restart -> terminal escalation`).

## Deterministic Recovery Actions
Deterministic action matrix includes:
- transient disconnect before timeout;
- transient disconnect timeout escalation;
- failed ICE state restart path;
- late recovery after timeout;
- pending recovery expired;
- signaling received for closed session;
- recovery collision during restart (delegated to Step 24.3 glare policy).

## Invariants
- `disconnected` is recovery-eligible and not terminal by default;
- `failed` is ICE-restart-eligible;
- `closed` is not recoverable;
- one session has at most one active pending-recovery attempt;
- every recovery path ends in deterministic terminal outcome (`connected` / `failed` / `closed`);
- recovery actions must remain consistent with Step 24.3 negotiation/glare contract;
- production runtime switch is out of scope for Step 24.4.

## Closure Criteria
Step 24.4 is closed when:
- doc/module/checker are present;
- trigger/eligibility/escalation contracts are complete and checker-enforced;
- pending-recovery schema/ownership is complete and checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_reconnect_ice_restart_pending_recovery_contract.py
.venv_tmpcheck/bin/python -m compileall app tools
```

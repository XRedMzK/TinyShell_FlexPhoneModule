# Step 24.1 - WebRTC Session Lifecycle Hardening Baseline

## Goal
Define baseline for next roadmap stage `WebRTC Session Lifecycle Hardening` over completed signaling delivery hardening and runtime cutover contracts.

## Scope
Step 24.1 defines:
- lifecycle hardening scope for peer-session state machine over existing signaling contracts;
- invariants for negotiation ownership, glare handling, reconnect/ICE-restart policy, and stale-session cleanup;
- ownership boundaries between signaling layer, lifecycle layer, and media layer;
- closure criteria and verification-type plan for Stage 24 substeps.

Step 24.1 is contract-definition only and does not introduce runtime behavior changes.

## Ownership Boundaries
- signaling layer owns authoritative signaling event delivery, session metadata exchange, and reconciliation input;
- lifecycle layer owns peer connection state transitions, negotiation ownership policy, ICE restart triggers, and stale-session cleanup;
- media layer owns RTP/track transport runtime behavior and quality observation;
- ownership overlap is forbidden.

## Invariants
- single active negotiation owner per peer session;
- deterministic glare resolution is required;
- explicit policy for `disconnected` / `failed` / `closed` states;
- ICE restart trigger policy is explicit and bounded;
- no zombie sessions after reconnect/abandon;
- failed recovery must have clean terminate fallback;
- lifecycle correctness must not depend on at-most-once Pub/Sub delivery;
- production-path switch is out of scope for Step 24.1.

## Closure Criteria
Step 24.1 is closed when:
- baseline doc/module/checker are present;
- scope/invariants/ownership boundaries are explicit;
- Stage 24 closure and verification plan is explicit;
- checker and compileall pass.

## Verification Type
- `build check`

## Stage 24 Draft
- `24.1` baseline definition
- `24.2` peer/session state inventory + transition matrix
- `24.3` negotiation/glare-resolution contract
- `24.4` reconnect/ICE-restart/pending-recovery contract
- `24.5` lifecycle sandbox smoke baseline
- `24.6` lifecycle CI gate baseline

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_session_lifecycle_hardening_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

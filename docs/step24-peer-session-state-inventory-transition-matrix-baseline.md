# Step 24.2 - Peer/Session State Inventory + Transition Matrix Baseline

## Goal
Define canonical peer/session lifecycle states and transition matrix for WebRTC session lifecycle hardening, mapped to `signalingState`, `iceConnectionState`, and `connectionState`.

## Scope
Step 24.2 defines:
- canonical app-level peer/session states;
- mapping from canonical states to browser-native state machines;
- allowed transition matrix with transition groups;
- terminal and recovery-eligible semantics;
- ownership boundaries between client lifecycle and signaling session metadata.

Step 24.2 is contract-definition only and does not change runtime behavior.

## Canonical State Inventory
Canonical states:
- `session_new`
- `session_signaling_ready`
- `session_negotiating`
- `session_connecting`
- `session_connected`
- `session_degraded`
- `session_recovering`
- `session_closing`
- `session_closed`
- `session_failed`

## Mapping to WebRTC Runtime State
Each canonical state defines allowed values for:
- `RTCPeerConnection.signalingState`
- `RTCPeerConnection.iceConnectionState`
- `RTCPeerConnection.connectionState`

`session_closed` is strictly mapped to native `closed` states.

## Allowed Transition Matrix
Transition groups:
- negotiation path;
- glare/rollback path;
- connectivity degradation path;
- ICE restart path;
- terminal path.

Required transition pairs are explicit and checker-enforced.

## Terminal and Recovery Semantics
- terminal states: `session_closed`, `session_failed`;
- `session_closed` has no outgoing transitions;
- `session_failed` may only transition to `session_closed`;
- recovery-eligible states are explicitly listed and bounded.

## Ownership Boundaries
- client lifecycle owns peer state transitions, negotiation owner selection, reconnect and ICE-restart execution, stale-session cleanup;
- signaling metadata owns session metadata and authoritative signaling event metadata;
- ownership overlap is forbidden.

## Invariants
- one peer/session has one canonical lifecycle state at a time;
- every non-terminal state has explicit next-step policy;
- browser-native `closed` cannot map to recoverable canonical state;
- negotiation transitions requiring owner are explicit.

## Closure Criteria
Step 24.2 is closed when:
- doc/module/checker are present;
- inventory and transition matrix are complete and unambiguous;
- terminal/recovery semantics are explicit and checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_peer_session_state_inventory.py
.venv_tmpcheck/bin/python -m compileall app tools
```

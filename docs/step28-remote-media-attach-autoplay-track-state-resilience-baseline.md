# Step 28.1 - Remote Media Attach, Autoplay, and Track-State Resilience Baseline

## Goal
Define baseline for next roadmap stage `Remote Media Attach / Autoplay / Track-State Resilience` after closure of Stage 27 output-route resilience.

## Scope
Step 28.1 defines:
- remote track arrival and attach ownership model driven by `RTCPeerConnection.track`;
- authoritative remote stream binding contract through `HTMLMediaElement.srcObject`;
- autoplay and `HTMLMediaElement.play()` promise handling contract;
- deterministic runtime/UI semantics for remote track `mute` / `unmute` / `ended` branches;
- explicit recovery path for autoplay-block and media-element remount/reattach flows;
- Stage 28 closure and verification draft (`28.2-28.7`);
- explicit boundary excluding capture, output-sink routing, and transport-quality contracts.

Step 28.1 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Remote Media Surfaces
- remote media arrival: `RTCPeerConnection.track` event;
- media-element attach: `HTMLMediaElement.srcObject`;
- playback start gate: `HTMLMediaElement.play()` promise outcome;
- autoplay policy branch: `HTMLMediaElement.autoplay` semantics plus explicit play-result handling;
- remote track state events: `MediaStreamTrack.mute`, `MediaStreamTrack.unmute`, `MediaStreamTrack.ended`;
- `MediaStreamTrack.muted` may be observed but is non-authoritative for contract correctness.

## Remote Track Attach and Ownership Model
- attach trigger is `pc.ontrack` only;
- attach ownership is explicit: event-driven `track/streams` -> dedicated remote media element;
- duplicate attach guard is required to prevent parallel conflicting bindings;
- attach correctness must not rely on implicit side effects from unrelated UI/runtime layers;
- stable binding key uses remote track/receiver identity instead of transient DOM state.

## Autoplay and play() Promise Handling Model
- `play()` must never be treated as fire-and-forget;
- play result is modeled as explicit promise branch (`resolved` vs `rejected`);
- autoplay-block is a dedicated state branch, not “remote media broken”;
- autoplay-block must expose deterministic user-gesture resume path;
- `autoplay=true` does not bypass policy handling; play outcome still requires explicit branching.

## Remote Track-State Resilience Model
- `mute` / `unmute` model temporary remote media interruption/recovery;
- `ended` models terminal branch for the current remote track object;
- temporary mute must not be mapped to call/session terminal state;
- ended track object is not recoverable-in-place and requires reattach path with fresh remote track;
- runtime state machine must keep temporary-vs-terminal branches explicitly separated.

## Element Remount/Reattach Recovery Model
- DOM remount requires explicit `srcObject` rebind;
- remount recovery must replay attach -> play pipeline with policy-aware handling;
- autoplay-block during remount recovery must route to the same explicit user-gesture resume path;
- reattach flow must preserve authoritative remote track identity mapping.

## Scope Boundary
- Stage 28 covers remote media attach/autoplay/track-state resilience only.
- Capture-source resilience remains in Stage 26.
- Output sink routing remains in Stage 27.
- Sender/receiver transport-quality observability remains out of Stage 28 scope.
- Signaling/lifecycle negotiation contracts remain out of Stage 28 scope.

## Invariants
- remote attach source of truth is `ontrack` event path;
- `play()` promise outcome is always handled explicitly;
- autoplay block is modeled as dedicated recoverable branch;
- `mute`/`unmute` and `ended` remain semantically distinct;
- temporary remote mute never implies terminal session end;
- remount/reattach path is deterministic and replayable;
- production runtime-path switch is out of scope for Step 28.1.

## Closure Criteria
Step 28.1 is closed when:
- baseline doc/module/checker are present;
- scope, authoritative surfaces, attach ownership, autoplay/play handling, and track-state semantics are explicit;
- Stage 27 dependency alignment is checker-enforced;
- Stage 28 draft and verification map are explicit;
- checker and compileall pass.

## Verification Type
- `build check`

## Stage 28 Draft
- `28.1` baseline definition
- `28.2` remote track attach and ownership contract
- `28.3` autoplay / play-promise / user-gesture recovery contract
- `28.4` remote track mute/unmute/ended resilience contract
- `28.5` media element remount / reattach recovery contract
- `28.6` remote media resilience sandbox smoke baseline
- `28.7` remote media resilience CI gate baseline

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_output_route_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

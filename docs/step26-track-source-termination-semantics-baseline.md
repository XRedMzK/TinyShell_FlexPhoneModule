# Step 26.3 - Track and Source Termination Semantics Baseline

## Goal
Define deterministic capture-side contract for distinguishing temporary interruption from terminal track termination.

## Scope
Step 26.3 defines:
- authoritative terminal signal for capture-side tracks;
- authoritative temporary interruption signal model;
- terminal cause classes for device capture and display capture;
- direct local `stop()` path semantics vs event-driven terminal path semantics;
- deterministic teardown/reconciliation actions per capture slot;
- explicit exclusion of receiver-side remote media-stop semantics from Stage 26 capture scope.

Step 26.3 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Signal Model
- terminal signal: `MediaStreamTrack.readyState = ended`;
- temporary interruption signal: `MediaStreamTrack.mute` / `MediaStreamTrack.unmute` transitions with non-terminal track object lifecycle;
- `muted` state is not treated as terminal track loss;
- terminal track object is not considered recoverable in-place.

## Terminal Cause Matrix
Capture-side terminal causes in scope:
- `local_stop` (`MediaStreamTrack.stop()`);
- `source_disconnected_or_exhausted`;
- `permission_revoked_or_ua_forced_end` (camera/microphone capture);
- `hardware_removed_or_ejected` (device capture);
- `display_surface_permanently_inaccessible` (display capture).

Out of scope for Step 26.3:
- receiver-side remote peer stop semantics (`remote_stop`).

## Direct Stop vs Event-Driven Terminal Paths
Direct stop path (`track.stop()`):
- synchronous local teardown path;
- immediate `readyState` transition to `ended`;
- `ended` event is not required for this path;
- teardown/reconciliation must start without waiting for `onended`.

Event-driven terminal path (non-`stop()` terminal causes):
- source terminates for external/runtime reason;
- terminal lifecycle culminates in `readyState=ended`;
- `ended` event is authoritative terminal observation surface.

## Temporary Interruption Semantics
Temporary interruption path:
- expressed via `mute` and `unmute` transitions;
- track object remains non-terminal;
- does not imply teardown or slot replacement by itself;
- for display capture, temporary surface inaccessibility remains interruption path (not terminal) until permanent-loss classification is reached.

## Deterministic Teardown and Reconciliation Actions
`mic` / `camera` terminal actions:
1. set slot effective state to `ended`;
2. clear current track as authoritative live source;
3. mark ended track object as non-reusable;
4. trigger inventory reconcile refresh (`enumerateDevices` path from `26.5`);
5. if prior source identity remains available and policy allows, reacquire via fresh acquire flow (new track object);
6. otherwise classify outcome as `missing_source` or `blocked_permission`.

`displayVideo` / `displayAudio` terminal actions:
1. set slot effective state to `ended`;
2. clear current display track as authoritative live source;
3. disable inventory-based source rediscovery assumptions (`enumerateDevices` / `devicechange` do not enumerate display sources);
4. allow only explicit reacquire via fresh `getDisplayMedia()` user-selection flow (`26.4`).

## Capture-Side Scope Boundary
- Step 26.3 covers local capture-side track/source semantics only;
- receiver-side inbound remote media-stop semantics are out of scope;
- output-sink routing remains out of scope under Stage 26 boundary.

## Invariants
- `readyState=ended` is terminal for the current track object;
- `mute/unmute` is temporary interruption semantics and not terminal by itself;
- direct `stop()` path must not require `ended` event delivery;
- non-`stop()` terminal causes use event-driven terminal observation via `ended`;
- ended track objects are not reusable for recovery;
- recovery requires fresh acquire path (new track object), never revival of ended object;
- display-source permanent loss is terminal and requires explicit reacquire;
- Step 26.3 remains capture-side only and excludes `remote_stop`.

## Closure Criteria
Step 26.3 is closed when:
- baseline doc/module/checker are present;
- terminal-vs-temporary signal distinction is explicit;
- direct `stop()` vs event-driven terminal semantics are explicit;
- capture-side terminal cause matrix is explicit and excludes `remote_stop`;
- teardown/reconciliation actions are deterministic per slot class (`device` vs `display`);
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_capture_source_device_permission_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_track_source_termination_semantics_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

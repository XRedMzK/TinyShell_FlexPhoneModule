# Step 26.1 - Capture Source, Device, and Permission Resilience Baseline

## Goal
Define baseline for next roadmap stage `Capture Source / Device / Permission Resilience` over completed Stage 25 media-control and CI gate contracts.

## Scope
Step 26.1 defines:
- local capture acquisition and runtime reconciliation scope for `audioinput`, `videoinput`, and display-capture sources;
- authoritative per-slot capture-state model (`mic`, `camera`, `displayVideo`, optional `displayAudio`);
- failure classes for acquisition/runtime/inventory drift;
- reconciliation surfaces (`getUserMedia`, `getDisplayMedia`, `enumerateDevices`, optional `devicechange`, track lifecycle semantics);
- deterministic fallback rules separated for device capture vs display capture;
- explicit capture-side scope boundary excluding output-sink routing;
- Stage 26 closure and verification draft.

Step 26.1 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Capture-State Model
Capture slots:
- `mic` (`source_class=device`, required)
- `camera` (`source_class=device`, required)
- `displayVideo` (`source_class=display`, required)
- `displayAudio` (`source_class=display`, optional)

Per-slot state dimensions:
- `intent_state`: `idle | acquire_requested | stop_requested`
- `effective_state`: `idle | live | muted_external | ended | failed_acquire | blocked_permission | missing_source`
- identity model:
  - device capture: `kind + deviceId? + groupId?`
  - display capture: opaque capture session identity (non-enumerable source model)

## Reconciliation Surfaces
- acquisition APIs:
  - `MediaDevices.getUserMedia`
  - `MediaDevices.getDisplayMedia`
- inventory API:
  - `MediaDevices.enumerateDevices()`
- advisory event surface:
  - `MediaDevices.devicechange` (optional/best-effort, not correctness-required)
- track lifecycle semantics:
  - `mute`
  - `unmute`
  - `ended`
  - direct local `stop()` (separate from `ended` event delivery)

## Failure Classes
- `acquire_denial_or_policy_block`:
  - permission denial, policy block, insecure-context restrictions
- `acquire_source_absence_or_constraint_mismatch`:
  - missing source, unsatisfied constraints, invalid capture options
- `acquire_runtime_lockout_or_abort`:
  - OS/browser lockout or transient abort on capture start
- `runtime_temporary_interruption`:
  - temporary `mute/unmute` without terminal source loss
- `runtime_terminal_loss`:
  - revoked permission, hardware removal/ejection, permanent display-surface loss, source exhaustion/disconnect, local direct `stop()`
- `inventory_drift`:
  - physical/permission inventory changes requiring reconcile snapshot refresh

Note: Stage 26 failure classes are capture-side only; receiver-side remote media stop semantics are out of this stage scope.

## Deterministic Fallback Rules
Device capture fallback:
- on reconcile trigger (`devicechange` where available, `ended`, acquire failure, explicit refresh), perform fresh `enumerateDevices()` snapshot;
- if prior source identity is still present, reacquire same source path is eligible;
- if prior source is absent, fallback to default same-kind source only when policy allows;
- otherwise transition slot to `missing_source` and require explicit user selection.

Display capture fallback:
- no automatic source switching across display surfaces;
- no inference of display source changes from `enumerateDevices()` / `devicechange`;
- reacquire requires explicit user gesture and new `getDisplayMedia()` flow;
- terminal display-source loss does not silently map to alternate display source.

## Scope Boundary
- Stage 26 covers capture-side resilience only.
- Output-sink routing and speaker selection are out of scope.
- APIs such as `selectAudioOutput` / `setSinkId` are not part of Stage 26 baseline correctness model.

## Invariants
- capture-side scope excludes output-sink routing;
- `enumerateDevices()` is inventory surface, not live-capture truth by itself;
- `devicechange` is advisory and not required for correctness;
- display capture sources are non-enumerable and not modeled via `devicechange` source-change assumptions;
- direct local `stop()` path remains distinct from `ended` event delivery path;
- fallback policies are deterministic and separated for device vs display capture;
- production-path switch is out of scope for Step 26.1.

## Closure Criteria
Step 26.1 is closed when:
- baseline doc/module/checker are present;
- local capture scope, slot model, failure classes, reconciliation surfaces, and fallback rules are explicit;
- Stage 26 closure and verification plan is explicit;
- checker and compileall pass.

## Verification Type
- `build check`

## Stage 26 Draft
- `26.1` baseline definition
- `26.2` media-device inventory + permission-gated visibility contract
- `26.3` track/source termination semantics contract
- `26.4` screen-share capture lifecycle + source-reselection contract
- `26.5` device-change reconciliation contract
- `26.6` capture resilience sandbox smoke baseline
- `26.7` capture resilience CI gate baseline

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_capture_source_device_permission_resilience_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

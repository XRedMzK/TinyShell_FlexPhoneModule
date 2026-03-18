# Step 26.4 - Screen-Share Capture Lifecycle and Source-Reselection Contract Baseline

## Goal
Define deterministic capture-side contract for screen-share lifecycle and source reselection as user-selected capture-session flow.

## Scope
Step 26.4 defines:
- authoritative acquisition surface for screen-share sessions;
- non-enumerable display-source model and inventory boundary;
- source selection and reselection rules;
- temporary interruption vs terminal termination semantics for display tracks;
- direct stop path vs event-driven terminal path semantics for display capture;
- sender handoff boundaries via `RTCRtpSender.replaceTrack` within negotiated envelope.

Step 26.4 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Screen-Share Acquisition Surface
- authoritative acquisition API: `navigator.mediaDevices.getDisplayMedia()`;
- invocation requires transient user activation;
- permission model is user-selection driven and non-persistent for display-capture (`prompt|denied` model);
- resulting stream shape contract:
  - exactly one `displayVideo` track;
  - optional `displayAudio` track;
  - no assumption of enumerable display-source identity.

## Non-Enumerable Display-Source Model
- display sources are not discoverable via `enumerateDevices()`;
- display source selection via `deviceId` inventory model is unsupported;
- `devicechange` is non-authoritative for display-source set changes;
- screen-share source discovery/reselection never reuses capture-side device inventory flow.

## Source Selection and Reselection Semantics
- initial source selection is always user-mediated via user-agent chooser;
- selected display source remains fixed for produced track lifetime unless user explicitly allows source switch through UA flow;
- app-level source reselection is valid only through:
  - fresh user-mediated `getDisplayMedia()` acquire flow; or
  - UA-mediated and user-approved surface-switching path;
- source reselection is never inferred from inventory drift.

## Display Lifecycle Semantics
Temporary interruption semantics:
- temporary display-surface inaccessibility maps to `mute`/`unmute` transitions;
- temporary interruption does not imply terminal teardown;
- returned display stream may initially contain muted tracks;
- `displayVideo` and optional `displayAudio` may mute/unmute independently.

Terminal semantics:
- permanent display-surface inaccessibility maps to terminal end (`readyState=ended`);
- terminal end closes current screen-share capture session for current track object;
- terminal recovery requires fresh user-mediated acquire path.

## Direct Stop vs Event-Driven Terminal Paths
Direct local stop path:
- trigger: local `track.stop()`;
- immediate `readyState=ended`;
- `ended` event is not required for direct-stop path handling;
- teardown/reconciliation starts immediately.

Event-driven terminal path:
- trigger: permanent external/UA display-source loss;
- terminal observation through ended lifecycle path;
- app treats session as irrecoverable without fresh user-mediated selection.

## Sender Handoff Boundaries (`replaceTrack`)
- `RTCRtpSender.replaceTrack` is transport handoff API, not capture acquisition API;
- handoff is same-kind best-effort path within already-negotiated envelope;
- envelope-breaking replacement requires renegotiation or fails closed;
- kind mismatch and out-of-envelope replacement are deterministic rejection paths;
- `replaceTrack` cannot be used to bypass user-mediated display-source selection/permissions.

## Capture-Side Scope Boundary
- Step 26.4 covers display capture-side lifecycle and reselection only;
- output-sink routing remains out of scope;
- receiver-side inbound remote media-stop semantics remain out of scope.

## Invariants
- `getDisplayMedia()` is the only authoritative acquisition surface for new screen-share sessions;
- display-source model is non-enumerable and outside `enumerateDevices`/`devicechange` discovery semantics;
- source reselection requires explicit user mediation (fresh acquire or UA-approved switch);
- temporary display inaccessibility maps to `mute/unmute`, not terminal by default;
- permanent display inaccessibility maps to terminal end;
- direct `stop()` path does not require waiting for `ended` event;
- `replaceTrack` is handoff-only and bounded by negotiated envelope;
- production runtime path switch is out of scope for Step 26.4.

## Closure Criteria
Step 26.4 is closed when:
- baseline doc/module/checker are present;
- authoritative acquisition, non-enumerable model, source-reselection rules, lifecycle semantics, and handoff boundaries are explicit;
- dependency alignment with Steps 26.1-26.3 and 25.3 is checker-enforced;
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
.venv_tmpcheck/bin/python tools/check_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

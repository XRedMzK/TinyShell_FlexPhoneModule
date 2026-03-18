# Step 26.6 - Capture Resilience Sandbox Smoke Baseline

## Goal
Validate that Stage 26 contracts (`26.1-26.5`) hold in isolated manual runtime simulation for capture-side resilience.

## Scope
Step 26.6 validates scenario-level capture resilience behavior for:
- permission drift and hardware/device drift on `mic`/`camera` slots;
- direct-stop vs event-driven terminal handling;
- temporary vs permanent display interruption semantics;
- advisory `devicechange` handling vs authoritative `enumerateDevices()` reconciliation;
- explicit fallback refresh behavior without relying on `devicechange`;
- fresh re-acquire flows for device capture and display capture.

Step 26.6 is isolated manual sandbox smoke and does not change production runtime behavior.

## Scenario Matrix
- A: permission drift for camera/microphone (`live -> terminal`, reconciliation/re-acquire path armed).
- B: hardware/device drift for active camera/microphone (`inventory drift` + fresh snapshot reconciliation).
- C: direct local stop path (`track.stop()` -> `readyState=ended` without required `ended` event wait).
- D: temporary display interruption (`mute/unmute` only, no terminal teardown).
- E: permanent display loss (`ended` + fresh user-mediated `getDisplayMedia()` required).
- F: fallback refresh without trusting `devicechange` (explicit refresh + fresh snapshot path).
- G: device-capture re-acquire after terminal (`fresh getUserMedia()`, new track object required).
- H: display-capture re-acquire after terminal (`fresh getDisplayMedia()` with user mediation).

## Authoritative Observation Surfaces
Per scenario, authoritative surfaces must be explicit:
- `MediaStreamTrack.readyState` for terminal state proof;
- `MediaStreamTrack.mute`/`MediaStreamTrack.unmute` for temporary interruption proof;
- fresh `navigator.mediaDevices.enumerateDevices()` snapshot for device inventory reconciliation;
- explicit non-reliance on `devicechange` as sole truth source;
- fresh acquire results from `getUserMedia()` / `getDisplayMedia()` for re-acquire proof.

## Forbidden Interpretations
- `MediaStreamTrack.enabled=false` is not source failure/terminal loss;
- missing device in one snapshot is not absolute OS-hardware absence;
- display-source loss/reselection is not reconciled through `enumerateDevices()`/`devicechange`;
- direct local `track.stop()` path must not wait for `ended` event delivery.

## Acceptance Criteria
- each scenario reaches deterministic expected outcome;
- terminal vs temporary distinction remains explicit (`ended` vs `mute/unmute`);
- `devicechange` behaves as advisory trigger only;
- authoritative reconciliation uses fresh `enumerateDevices()` snapshot;
- display capture stays outside device-inventory/source-discovery model;
- re-acquire paths use fresh acquire calls and new track objects;
- runner emits deterministic proof set and explicit pass/fail marker.

## Expected Proof Set
Per scenario:
- `scenario_id`
- `trigger`
- `authoritative_surfaces`
- `deterministic_actions`
- `forbidden_interpretations_checked`
- `status`

Global proof fields:
- `overall_status`
- `scenarios_passed`
- `scenarios_total`
- `advisory_devicechange_only`
- `authoritative_reconcile_surface`

## Closure Criteria
Step 26.6 is closed when:
- baseline doc and sandbox smoke runner are present;
- runner executes scenarios A-H successfully in local sandbox;
- manual runtime check output includes explicit success marker.

## Verification Type
- `manual runtime check`

## Manual Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_webrtc_capture_resilience_sandbox_smoke.py
```

Success marker:
- `WebRTC capture resilience sandbox smoke: OK`

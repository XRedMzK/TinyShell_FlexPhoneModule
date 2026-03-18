# Step 29.1 - Remote Video First-Frame, Render-Stall, and Dimension-Change Resilience Baseline

## Goal
Define baseline for next roadmap stage `Remote Video First-Frame / Render-Stall / Dimension-Change Resilience` after closure of Stage 28.

## Scope
Step 29.1 defines:
- remote video first-frame readiness contract scope;
- frame-progress truth model separated from playback intent/attach intent;
- recoverable render-starvation semantics for `waiting`/`stalled`;
- dimension-change reconciliation semantics over `loadedmetadata` and `resize`;
- optional `requestVideoFrameCallback()` branch with deterministic fallback to playback-quality/event surfaces;
- explicit boundary excluding new signaling/transport contracts and non-video subsystem expansion.

Step 29.1 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Remote Video Surfaces
- metadata readiness: `HTMLMediaElement.loadedmetadata`;
- first frame readiness: `HTMLMediaElement.loadeddata`;
- playback started/resumed: `HTMLMediaElement.playing`;
- recoverable starvation events: `HTMLMediaElement.waiting`, `HTMLMediaElement.stalled`;
- dimension change surface: `HTMLVideoElement.resize`;
- optional frame callback surface: `HTMLVideoElement.requestVideoFrameCallback()`;
- fallback frame-progress surface: `HTMLVideoElement.getVideoPlaybackQuality()`.

## First-Frame and Frame-Progress Truth Model
- `play`/autoplay intent never equals first-frame truth by itself;
- first-frame readiness is modeled independently from ongoing frame progress;
- ongoing progress requires dedicated progress surface (`requestVideoFrameCallback` when supported; fallback otherwise);
- render-progress truth is never inferred from attach-only state.

## Waiting/Stalled Recovery Model
- `waiting` and `stalled` are recoverable starvation branches and not terminal track branches by themselves;
- recoverable starvation may still keep last rendered frame visible and must not be misclassified as healthy frame progression;
- resume from starvation requires explicit progress recovery signal and not only unchanged visual placeholder.

## Dimension-Change Reconciliation Model
- initial dimensions become authoritative at metadata readiness;
- `resize` updates dimension truth and triggers deterministic reconciliation;
- dimension change is not terminal branch by itself and must not force track-end semantics;
- runtime dimension model must be updated explicitly and not inferred from stale snapshot.

## Scope Boundary
- Stage 29 covers remote video render-truth and reconciliation semantics only;
- Stage 28 attach/autoplay/track-state/remount contracts remain dependency input and are not redefined;
- new transport/signaling or DataChannel contracts are out of scope for 29.1;
- capture and output-route baselines remain out of scope for 29.1.

## Invariants
- first-frame truth remains separate from play-intent and attach-intent;
- ongoing frame progress remains separate from first-frame readiness;
- `waiting`/`stalled` remain non-terminal recoverable branches;
- terminal end semantics remain distinct from render starvation semantics;
- dimension truth is reconciled via metadata/resize surfaces;
- `requestVideoFrameCallback` is optional with explicit fallback branch;
- production runtime path switch is out of scope for Step 29.1.

## Closure Criteria
Step 29.1 is closed when:
- baseline doc/module/checker are present;
- first-frame/progress/starvation/dimension contracts are explicit;
- Stage 28 dependency alignment is checker-enforced;
- Stage 29 draft and verification map are explicit;
- checker and compileall pass.

## Verification Type
- `build check`

## Stage 29 Draft
- `29.1` baseline definition
- `29.2` remote video first-frame readiness contract
- `29.3` frame-progress and freeze-detection observability contract
- `29.4` waiting/stalled and resume recovery contract
- `29.5` dimension/resize reconciliation contract
- `29.6` remote video resilience sandbox smoke baseline
- `29.7` remote video resilience CI gate baseline

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_remote_media_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

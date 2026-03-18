# Step 29.3 - Frame-Progress and Freeze-Detection Observability Contract Baseline

## Goal
Define deterministic observability contract for ongoing remote-video frame progress and freeze suspicion without collapsing first-frame readiness, playback events, and starvation context.

## Scope
Step 29.3 defines:
- primary frame-progress truth source for supported runtimes;
- fallback frame-progress truth source when primary surface is unavailable;
- context-event boundaries for `playing`/`waiting`/`stalled`;
- deterministic classification branches for observed progress, unproven progress, starvation context, grace window, freeze suspicion, and unsupported runtime;
- explicit grace-window rules after start/resume/remount to avoid premature freeze classification.

Step 29.3 is contract-definition only and does not introduce runtime behavior changes.

## Frame-Progress Observability Surfaces
- primary progress surface: `HTMLVideoElement.requestVideoFrameCallback()`;
- fallback progress surface: `HTMLVideoElement.getVideoPlaybackQuality()`;
- contextual classifier events: `HTMLMediaElement.playing`, `HTMLMediaElement.waiting`, `HTMLMediaElement.stalled`.

## Primary rvfc Progress-Truth Model
- `requestVideoFrameCallback` is the preferred progress-proof surface when supported;
- progress proof is derived from deterministic `presentedFrames` delta growth between samples;
- rvfc support is optional at contract level and must not be hard-required for correctness;
- absence of rvfc support must route into explicit fallback/unsupported branch, never implicit pass.

## Fallback Playback-Quality Progress-Truth Model
- `getVideoPlaybackQuality()` provides fallback progress proof via `totalVideoFrames` delta growth;
- `droppedVideoFrames`, `corruptedVideoFrames`, and `totalFrameDelay` are contextual degradation counters and not standalone freeze-proof;
- fallback evaluation remains delta-based over observation window and never single-sample absolute-value based.

## Context Event Boundary (`playing` / `waiting` / `stalled`)
- `playing` is contextual playback-active signal and not direct frame-progress proof;
- `waiting` and `stalled` classify recoverable starvation context and are not terminal by themselves;
- context events guide branch classification but do not replace progress surfaces.

## Grace-Window and Freeze-Suspicion Rules
- freeze suspicion requires active-playback-compatible context plus no progress beyond configured grace window;
- grace window is required after initial playback start, resume from `waiting`/`stalled`, and remount/reattach recovery;
- no progress outside active-playback-compatible context remains `progress_unproven`, not freeze.

## Classification States
Canonical branches:
- `progress_observed`
- `progress_unproven`
- `resume_grace`
- `starvation_context`
- `freeze_suspected`
- `unsupported`

## Scope Boundary
- Step 29.3 covers ongoing frame-progress observability and freeze suspicion only.
- First-frame readiness threshold remains in Step 29.2.
- Waiting/stalled recovery handling semantics are finalized in Step 29.4.
- Dimension-change reconciliation remains in Step 29.5.

## Invariants
- first-frame readiness and ongoing progress truth remain separate;
- `playing` is never sufficient proof of frame progression;
- `waiting`/`stalled` are contextual starvation branches and non-terminal by default;
- freeze suspicion requires grace-window-aware, context-aware no-progress observation;
- rvfc is primary when supported, fallback quality model is mandatory when rvfc is unsupported;
- production runtime path switch is out of scope for Step 29.3.

## Closure Criteria
Step 29.3 is closed when:
- baseline doc/module/checker are present;
- rvfc-primary plus playback-quality-fallback models are explicit;
- contextual-event boundaries and grace-window freeze rules are explicit;
- dependency alignment with Steps 29.1-29.2 (and Stage 28 terminal boundary) is checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_readiness_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_frame_progress_freeze_detection_observability_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

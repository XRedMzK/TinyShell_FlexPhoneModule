# Step 29.2 - Remote Video First-Frame Readiness Contract Baseline

## Goal
Define deterministic contract for remote-video first-frame readiness over Stage 29.1 baseline without collapsing metadata/playback-intent/frame-progress semantics.

## Scope
Step 29.2 defines:
- explicit separation between metadata-known, first-frame-ready, play-requested, and playback-started states;
- authoritative first-frame readiness surfaces and supporting-signal model;
- deterministic minimum readiness threshold for first frame;
- boundary between first-frame readiness (`29.2`) and ongoing frame-progress/freeze detection (`29.3`).

Step 29.2 is contract-definition only and does not introduce runtime behavior changes.

## First-Frame Readiness Surfaces
- metadata surface: `HTMLMediaElement.loadedmetadata`;
- first-frame surface: `HTMLMediaElement.loadeddata`;
- play-intent surface: `HTMLMediaElement.play`;
- playback-start/resume surface: `HTMLMediaElement.playing`;
- supporting readiness surface: `HTMLMediaElement.readyState`.

## Metadata vs First-Frame vs Playback Semantics
- `loadedmetadata` means metadata/dimensions known and is not first-frame proof by itself;
- `loadeddata` is minimum first-frame readiness threshold;
- `play` means paused-state transition intent and is not first-frame proof;
- `playing` is playback start/resume signal and is stronger than `play`, but still not ongoing frame-progress proof;
- ongoing frame-progress truth is explicitly deferred to Step 29.3.

## readyState Supporting Signal Model
- `readyState` is supporting signal and not sole source of first-frame truth;
- primary first-frame readiness proof remains `loadeddata`;
- equivalent deterministic fallback proof is allowed when `readyState >= HAVE_CURRENT_DATA` and `loadeddata` has not been observed yet;
- readiness fallback must remain explicit and never be inferred from attach-only state.

## First-Frame State Model
Canonical states:
- `video_unattached`
- `metadata_known_dimensions_ready`
- `play_requested_first_frame_pending`
- `playback_started_first_frame_unproven`
- `first_frame_ready`
- `playback_started_frame_progress_pending`

Canonical transitions:
- `video_unattached -> metadata_known_dimensions_ready` on `loadedmetadata`;
- `video_unattached|metadata_known_dimensions_ready -> play_requested_first_frame_pending` on `play`;
- `play_requested_first_frame_pending -> playback_started_first_frame_unproven` on `playing` when first-frame proof is not established yet;
- `playback_started_first_frame_unproven -> first_frame_ready` on `loadeddata` (or explicit equivalent fallback threshold);
- `metadata_known_dimensions_ready|play_requested_first_frame_pending -> first_frame_ready` on `loadeddata` (or explicit equivalent fallback threshold);
- `first_frame_ready -> playback_started_frame_progress_pending` on `playing`.

## Deterministic Transition Contract
- first-frame readiness must never be concluded from `play` only;
- first-frame readiness must never be concluded from `loadedmetadata` only;
- `playing` without first-frame proof keeps branch in `playback_started_first_frame_unproven` until threshold is satisfied;
- once first-frame threshold is reached, contract may advance to frame-progress evaluation branch (owned by Step 29.3).

## Scope Boundary
- Step 29.2 covers first-frame readiness only;
- frame-progress/freeze detection observability is out of scope for 29.2 and deferred to 29.3;
- waiting/stalled resume recovery semantics are out of scope for 29.2 and deferred to 29.4;
- dimension reconciliation deep semantics are out of scope for 29.2 and deferred to 29.5.

## Invariants
- `loadedmetadata` is not first-frame proof;
- `loadeddata` (or explicit equivalent threshold) is minimum first-frame proof;
- `play` is not playback truth and not first-frame truth;
- `playing` is playback-start signal but not frame-progress truth;
- `readyState` is supporting-only surface and never sole truth source;
- production runtime path switch is out of scope for Step 29.2.

## Closure Criteria
Step 29.2 is closed when:
- baseline doc/module/checker are present;
- first-frame threshold and non-equivalence rules are explicit;
- dependency alignment with Step 29.1 is checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_readiness_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

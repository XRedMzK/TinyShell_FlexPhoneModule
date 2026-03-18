# Step 29.4 - Waiting/Stalled and Resume Recovery Contract Baseline

## Goal
Define deterministic remote-video starvation and resume-recovery contract that separates temporary data-starvation branches from terminal failure branches.

## Scope
Step 29.4 defines:
- explicit starvation semantics for `HTMLMediaElement.waiting` and `HTMLMediaElement.stalled`;
- explicit resume semantics for `HTMLMediaElement.playing`;
- `HTMLMediaElement.canplay` as supporting readiness hint only;
- grace-window-aware resume classification before frame-progress re-proof;
- non-equivalence between starvation branches and terminal media failure.

Step 29.4 is contract-definition only and does not introduce runtime behavior changes.

## Starvation and Resume Surfaces
- temporary playback starvation surface: `HTMLMediaElement.waiting`;
- fetch-path starvation surface: `HTMLMediaElement.stalled`;
- start/resume signal surface: `HTMLMediaElement.playing`;
- pre-resume readiness hint surface: `HTMLMediaElement.canplay`.

## Waiting/Stalled Semantics
- `waiting` is temporary starvation where playback stops due to temporary lack of data;
- `stalled` is starvation branch where data fetch is attempted but expected data is not forthcoming;
- both branches are non-terminal by default and must not be merged with terminal track/media end;
- starvation classification does not require remount/reattach by default.

## Resume Semantics
- `playing` is canonical start/resume signal after initial start or after starvation-induced delay;
- after resume signal, contract enters explicit grace branch before freeze suspicion can be re-evaluated by Step 29.3;
- `playing` does not bypass frame-progress re-proof requirements.

## canplay Supporting-Hint Boundary
- `canplay` is a non-terminal readiness hint only;
- `canplay` is not sufficient proof of successful starvation recovery by itself;
- final recovery truth remains dependent on resume + progress model (`29.3`).

## Resume Grace Rules
- grace window is required immediately after `playing` that follows starvation context;
- during grace, no-progress state is classified as `resume_grace`, not freeze regression;
- freeze suspicion may be re-enabled only after grace expires and progress remains unproven in active playback context.

## Classification States
Canonical branches:
- `starvation_waiting`
- `starvation_stalled`
- `resume_signal_received`
- `resume_grace`
- `resume_progress_unproven`
- `terminal_out_of_scope`

## Scope Boundary
- Step 29.4 covers starvation/resume classification only.
- Ongoing frame-progress proof and freeze suspicion remain owned by Step 29.3.
- First-frame threshold remains owned by Step 29.2.
- Dimension/resize reconciliation remains owned by Step 29.5.

## Invariants
- `waiting` and `stalled` are non-terminal starvation branches by default;
- `waiting` and `stalled` are not equivalent branches and remain separately classifiable;
- `playing` is start/resume signal, not frame-progress truth;
- `canplay` is hint-only and not final recovery proof;
- starvation branches do not imply reattach/remount by themselves;
- terminal media end remains explicit out-of-scope boundary for 29.4.

## Closure Criteria
Step 29.4 is closed when:
- baseline doc/module/checker are present;
- waiting/stalled/playing/canplay boundaries are explicit;
- resume-grace semantics before freeze re-evaluation are explicit;
- dependency alignment with Steps 29.1-29.3 and terminal boundary from Stage 28 is checker-enforced;
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
.venv_tmpcheck/bin/python tools/check_webrtc_waiting_stalled_resume_recovery_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

# Step 29.6 - Remote Video Resilience Sandbox Smoke Baseline

## Goal
Validate in manual-runtime sandbox that Stage 29 contracts (`29.1-29.5`) hold for first-frame readiness, frame-progress truth, starvation/resume handling, and intrinsic dimension reconciliation.

## Scope
Step 29.6 validates scenario-level behavior for:
- cold attach and first-frame happy path;
- false-positive guard when metadata is available but first-frame proof is not yet established;
- temporary starvation (`waiting`) and resume flow with grace-window handling;
- fetch-starvation (`stalled`) classification boundary;
- intrinsic dimension update via `resize` without failure/reattach misclassification;
- remount/reattach continuity with preserved progress/dimension truth model;
- fallback progress proof when rvfc is unavailable;
- `playing` without real frame progress guard branch.

Step 29.6 is manual-runtime smoke oriented and does not change production runtime behavior.

## Preflight
- Stage 29 contract artifacts (`29.1-29.5`) are present;
- sandbox runtime exposes deterministic simulation outputs for:
  - first-frame state classification;
  - frame-progress classification;
  - waiting/stalled resume classification;
  - dimension reconciliation classification;
- manual-runtime output marker is visible.

## Scenario Matrix
- A: cold attach happy path (`loadedmetadata` -> first-frame proof -> `playing` -> progress observed).
- B: metadata without first-frame proof (no early-ready false positive).
- C: `waiting` starvation -> `playing` resume -> grace-window branch -> progress resumes.
- D: `stalled` fetch-starvation branch (non-terminal, non-fatal).
- E: intrinsic dimension update (`resize`, `videoWidth`/`videoHeight`) without reattach/failure branch.
- F: remount/reattach continuity preserving dimension/progress contracts.
- G: rvfc unavailable fallback path using playback-quality deltas.
- H: `playing` without real frame progress remains non-success (`resume_grace`/`progress_unproven`) before any freeze declaration.

## Authoritative Observation Surfaces
- first-frame boundary:
  - `HTMLMediaElement.loadedmetadata`
  - `HTMLMediaElement.loadeddata`
  - `HTMLMediaElement.readyState`
- frame-progress boundary:
  - `HTMLVideoElement.requestVideoFrameCallback()` (when supported)
  - `HTMLVideoElement.getVideoPlaybackQuality()` fallback
- starvation/resume boundary:
  - `HTMLMediaElement.waiting`
  - `HTMLMediaElement.stalled`
  - `HTMLMediaElement.playing`
  - `HTMLMediaElement.canplay` (hint-only)
- dimension boundary:
  - `HTMLVideoElement.videoWidth`
  - `HTMLVideoElement.videoHeight`
  - `HTMLVideoElement.resize`

## Acceptance Criteria
- first-frame readiness is never inferred from metadata-only or play-intent-only signals;
- `waiting`/`stalled` are classified as starvation context and never terminal by default;
- resume branch enters grace before frame-progress re-proof;
- intrinsic dimension updates reconcile through `videoWidth`/`videoHeight` + `resize`, not via CSS box heuristics;
- dimension change does not trigger failure/reattach branch by default;
- rvfc-unavailable path still provides deterministic progress proof through playback-quality fallback;
- runner emits scenario proofs (`A-H`) and explicit success marker.

## Expected Proof Set
Per scenario:
- `scenario_id`
- `trigger`
- `authoritative_surfaces`
- `deterministic_actions`
- `expected_state_assertions`
- `status`

Global proof fields:
- `overall_status`
- `scenarios_total`
- `scenarios_passed`
- `scenario_ids`
- `first_frame_false_positive_guard_enforced`
- `resume_grace_before_freeze_recheck_enforced`
- `dimension_non_failure_boundary_enforced`
- `fallback_progress_branch_enforced`

## Closure Criteria
Step 29.6 is closed when:
- baseline doc, sandbox runner, and evidence artifact are present;
- runner executes scenarios `A-H` successfully in local sandbox simulation;
- manual runtime output includes explicit success marker.

## Verification Type
- `manual runtime check`

## Manual Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_webrtc_remote_video_resilience_sandbox_smoke.py
```

Success marker:
- `WebRTC remote video resilience sandbox smoke: OK`

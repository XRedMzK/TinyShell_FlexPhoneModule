# Step 29.7 - Remote Video Resilience CI Gate Baseline

## Goal
Convert Stage 29 contracts and Step 29.6 manual smoke evidence into fail-closed CI gate so regressions in remote-video runtime resilience cannot pass silently.

## Scope
Step 29.7 defines CI gate for Stage 29 coverage across artifacts:
- Stage 29 baseline scope and boundaries (`29.1`);
- first-frame readiness contract (`29.2`);
- frame-progress/freeze observability contract (`29.3`);
- waiting/stalled resume-recovery contract (`29.4`);
- intrinsic dimension/resize reconciliation contract (`29.5`);
- manual runtime smoke evidence completeness for matrix `A-H` (`29.6`).

## CI Contract vs Real Runtime
- CI gate validates deterministic contract and evidence integrity;
- CI gate does not claim full real-browser/media-policy truth across all engines/webviews;
- unsupported runtime capability is explicit outcome class and is never treated as `PASS`;
- fail-closed behavior is mandatory for missing/incomplete evidence or invariant breaches.

## Dependency Closure
Mandatory dependencies:
- `28.7`
- `29.1`
- `29.2`
- `29.3`
- `29.4`
- `29.5`
- `29.6`

CI gate must fail when any dependency checker is missing or non-green.

## Manual Smoke Evidence Contract
Evidence source:
- `docs/evidence/step29-remote-video-resilience-sandbox-smoke-evidence.json`

Mandatory smoke scenario IDs:
- `A_cold_attach_happy_path`
- `B_metadata_without_first_frame_false_positive_guard`
- `C_waiting_resume_grace_then_progress`
- `D_stalled_fetch_starvation_branch`
- `E_intrinsic_dimension_update_no_failure_reattach`
- `F_remount_reattach_continuity`
- `G_rvfc_unavailable_quality_fallback`
- `H_playing_without_real_frames_non_success_guard`

Mandatory per-scenario fields:
- `scenario_id`
- `runtime`
- `browser_engine`
- `result` (`PASS|FAIL|UNSUPPORTED`)
- `proof_refs`
- `verified_invariants`

## Mandatory Transition Invariants
- metadata-only branch never proves first-frame readiness;
- first-frame proof and ongoing progress proof remain separated;
- waiting/stalled branches remain non-terminal starvation context;
- resume applies grace before freeze re-evaluation;
- intrinsic dimension updates reconcile through `videoWidth`/`videoHeight` + `resize`;
- dimension updates do not auto-trigger failure/reattach branch;
- rvfc-unavailable fallback branch is explicitly supported through playback-quality deltas;
- remount continuity preserves dimension/progress contract boundaries.

## Outcome Model
Gate outcome classes:
- `PASS`: dependencies green + evidence complete + all required invariants proven;
- `FAIL`: any dependency/evidence/invariant failure;
- `UNSUPPORTED`: evidence indicates unsupported runtime, reported explicitly and not treated as pass.

## Fail Conditions
- missing baseline doc/module/checker/runner/workflow;
- missing dependency checker or failed dependency checker;
- missing smoke evidence manifest;
- missing scenario from required matrix `A-H`;
- missing required evidence fields/invariant markers;
- stale/invalid evidence schema;
- `UNSUPPORTED` silently treated as pass;
- compile/import checks fail.

## Workflow Baseline
Workflow:
- `.github/workflows/webrtc-remote-video-resilience-ci.yml`

Runner:
- `server/tools/run_webrtc_remote_video_resilience_ci_gate.py`

## Closure Criteria
Step 29.7 is closed when:
- baseline doc/module/checker/runner/workflow exist;
- dependency closure on `29.1-29.6` is checker-enforced (`28.7` included as upstream dependency);
- evidence completeness check for matrix `A-H` is fail-closed;
- outcome classes `PASS|FAIL|UNSUPPORTED` are explicit and non-overlapping;
- compileall and all Stage 29 gate checks pass.

## Verification Type
- `build check`

## Build-Level Validation
Run locally:

```bash
cd server
.venv_tmpcheck/bin/python -m compileall app tools
.venv_tmpcheck/bin/python tools/check_webrtc_remote_media_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_readiness_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_frame_progress_freeze_detection_observability_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_waiting_stalled_resume_recovery_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_dimension_resize_reconciliation_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/run_webrtc_remote_video_resilience_ci_gate.py
```

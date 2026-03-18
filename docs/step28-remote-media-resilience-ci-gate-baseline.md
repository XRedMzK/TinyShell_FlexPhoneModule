# Step 28.7 - Remote Media Resilience CI Gate Baseline

## Goal
Convert Stage 28 contracts and Step 28.6 manual smoke evidence into fail-closed CI gate so regressions in remote attach/playback/runtime semantics cannot pass silently.

## Scope
Step 28.7 defines CI gate for Stage 28 coverage across artifacts:
- remote attach/autoplay/track-state baseline scope and boundaries (`28.1`);
- remote track attach ownership and streamless fallback contract (`28.2`);
- autoplay/play-promise/user-gesture recovery contract (`28.3`);
- remote track `mute`/`unmute`/`ended` resilience contract (`28.4`);
- media-element remount/reattach recovery contract (`28.5`);
- manual runtime smoke evidence completeness for matrix `A-F` (`28.6`).

## CI Contract vs Real Runtime
- CI gate validates deterministic contract and evidence integrity;
- CI gate does not claim full real-browser autoplay/device-policy truth across all engines;
- unsupported runtime capability is explicit outcome class and is never treated as `PASS`;
- fail-closed behavior is mandatory for missing/incomplete evidence or invariant breaches.

## Dependency Closure
Mandatory dependencies:
- `27.7`
- `28.1`
- `28.2`
- `28.3`
- `28.4`
- `28.5`
- `28.6`

CI gate must fail when any dependency checker is missing or non-green.

## Manual Smoke Evidence Contract
Evidence source:
- `docs/evidence/step28-remote-media-resilience-sandbox-smoke-evidence.json`

Mandatory smoke scenario IDs:
- `A_clean_remote_attach`
- `B_streamless_remote_attach`
- `C_autoplay_blocked_user_gesture_recovery`
- `D_temporary_interruption_mute_unmute`
- `E_terminal_track_end`
- `F_remount_reattach_abort_safe_replay`

Mandatory per-scenario fields:
- `scenario_id`
- `executed_at`
- `runtime`
- `browser_engine`
- `track_kind`
- `has_stream`
- `initial_play_outcome`
- `retry_play_outcome`
- `mute_seen`
- `unmute_seen`
- `ended_seen`
- `old_element_torn_down`
- `duplicate_attach_prevented`
- `final_binding_owner_key`
- `result` (`PASS|FAIL|UNSUPPORTED`)
- `proof_refs`
- `verified_invariants`
- `notes`

## Mandatory Transition Invariants
- clean attach reaches deterministic playback start branch;
- streamless attach uses fallback binding and duplicate attach remains no-op;
- autoplay blocked branch requires explicit user-gesture recovery;
- `mute`/`unmute` preserves binding and never maps to terminal branch;
- `ended` maps to terminal branch and is not treated as temporary interruption;
- remount/reattach requires old-element teardown and replay-safe attach+play;
- reattach-time `AbortError` remains transitional interruption branch, not source-invalid fatal branch.

## Outcome Model
Gate outcome classes:
- `PASS`: dependencies green + evidence complete + all required invariants proven;
- `FAIL`: any dependency/evidence/invariant failure;
- `UNSUPPORTED`: evidence indicates unsupported runtime, reported explicitly and not treated as pass.

## Fail Conditions
- missing baseline doc/module/checker/runner/workflow;
- missing dependency checker or failed dependency checker;
- missing smoke evidence manifest;
- missing scenario from required matrix `A-F`;
- missing required evidence fields/invariant markers;
- stale/invalid evidence schema;
- `UNSUPPORTED` silently treated as pass;
- compile/import checks fail.

## Workflow Baseline
Workflow:
- `.github/workflows/webrtc-remote-media-resilience-ci.yml`

Runner:
- `server/tools/run_webrtc_remote_media_resilience_ci_gate.py`

## Closure Criteria
Step 28.7 is closed when:
- baseline doc/module/checker/runner/workflow exist;
- dependency closure on `28.1-28.6` is checker-enforced (`27.7` included as upstream dependency);
- evidence completeness check for matrix `A-F` is fail-closed;
- outcome classes `PASS|FAIL|UNSUPPORTED` are explicit and non-overlapping;
- compileall and all Stage 28 gate checks pass.

## Verification Type
- `build check`

## Build-Level Validation
Run locally:

```bash
cd server
.venv_tmpcheck/bin/python -m compileall app tools
.venv_tmpcheck/bin/python tools/check_webrtc_output_route_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_track_attach_ownership_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_element_remount_reattach_recovery_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_media_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/run_webrtc_remote_media_resilience_ci_gate.py
```

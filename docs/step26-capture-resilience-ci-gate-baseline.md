# Step 26.7 - Capture Resilience CI Gate Baseline

## Goal
Convert Stage 26 capture resilience contracts into mandatory deterministic CI gate so contract regressions fail pipeline automatically.

## Scope
Step 26.7 defines CI gate for Stage 26 contract coverage across artifacts:
- capture scope, slot model, failure classes, and fallback rules (`26.1`);
- permission-gated inventory visibility model (`26.2`);
- terminal vs temporary track semantics (`26.3`);
- screen-share lifecycle and source-reselection boundaries (`26.4`);
- advisory `devicechange` vs authoritative `enumerateDevices()` reconciliation (`26.5`);
- manual sandbox scenario matrix semantics proven in `26.6`.

## CI Topology
- GitHub Actions workflow with one deterministic isolated gate job;
- compile + Stage 26 checkers + deterministic CI simulation;
- no physical capture device requirement;
- no real permission prompts / transient user gestures in CI;
- no reliance on real browser `devicechange` delivery;
- non-zero exit on contract breach.

## Scenario Matrix Source
CI gate reuses Step 26.6 runtime scenarios directly (`A-H`):
- `A_permission_drift_device_capture`
- `B_hardware_device_drift`
- `C_direct_local_stop`
- `D_temporary_display_interruption`
- `E_permanent_display_loss`
- `F_fallback_refresh_without_devicechange`
- `G_device_reacquire_after_terminal`
- `H_display_reacquire_after_terminal`

## Mandatory Assertions
- scenario result status is `PASS` for each `A-H` scenario;
- `devicechange` remains advisory-only (`not correctness required`);
- authoritative reconcile surface remains `fresh_enumerate_devices_snapshot`;
- direct-stop path keeps `readyState=ended` without required `ended` event wait;
- display-source model remains non-enumerable and outside `devicechange` source discovery;
- display-source reselection remains user-mediated only;
- fresh re-acquire semantics preserve new track object requirement for terminal recovery.

## Fail Conditions
- scenario missing or unexpected in proof payload;
- scenario status not `PASS`;
- required assertion marker missing/false;
- `devicechange` interpreted as authoritative truth source;
- authoritative reconcile surface mismatch;
- direct-stop vs event-driven terminal boundary breach;
- display-source non-enumerable boundary breach;
- incomplete or non-deterministic proof payload.

## Invariants
- CI gate validates deterministic contract transitions, not real hardware/browser quirks;
- CI does not depend on capture-device availability;
- CI does not require real display picker or permission prompt flow;
- Stage 26 correctness remains checker + deterministic simulation driven;
- production runtime path remains unchanged.

## Workflow Baseline
Workflow:
- `.github/workflows/webrtc-capture-resilience-ci.yml`

Runner:
- `server/tools/run_webrtc_capture_resilience_ci_simulation.py`

Dependencies:
- `server/tools/run_webrtc_capture_resilience_sandbox_smoke.py`
- `server/tools/check_webrtc_capture_source_device_permission_resilience_baseline.py`
- `server/tools/check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py`
- `server/tools/check_webrtc_track_source_termination_semantics_baseline.py`
- `server/tools/check_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py`
- `server/tools/check_webrtc_device_change_reconciliation_baseline.py`
- `server/tools/check_webrtc_capture_resilience_ci_gate_baseline.py`

## Closure Criteria
Step 26.7 is closed when:
- baseline doc/module/checker/workflow/runner exist;
- CI job executes compile + Stage 26 checker set + CI simulation runner;
- local CI-equivalent simulation is green (`all` + targeted scenarios);
- compile and baseline checkers pass.

## Verification Type
- `build check`

## Build-Level Validation
Run locally:

```bash
cd server
.venv_tmpcheck/bin/python -m compileall app tools
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_capture_source_device_permission_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_track_source_termination_semantics_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_device_change_reconciliation_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_capture_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/run_webrtc_capture_resilience_ci_simulation.py
FLEXPHONE_WEBRTC_CAPTURE_CI_SCENARIO=A_permission_drift_device_capture .venv_tmpcheck/bin/python tools/run_webrtc_capture_resilience_ci_simulation.py
FLEXPHONE_WEBRTC_CAPTURE_CI_SCENARIO=H_display_reacquire_after_terminal .venv_tmpcheck/bin/python tools/run_webrtc_capture_resilience_ci_simulation.py
```

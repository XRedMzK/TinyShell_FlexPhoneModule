# Step 25.7 - In-Call Media-Control CI Gate Baseline

## Goal
Convert Stage 25 in-call media-control contracts into mandatory CI gate so contract regressions fail pipeline automatically.

## Scope
Step 25.7 defines CI gate for Stage 25 contract coverage across artifacts:
- media-control ownership/state inventory (`25.2`);
- mute/switch/direction behavior contract (`25.3`);
- sender parameter boundary contract (`25.4`);
- in-call quality observability baseline (`25.5`);
- sandbox smoke runtime contract proven in `25.6`.

## CI Topology
- GitHub Actions workflow with one deterministic isolated gate job;
- compile + Stage 25 checkers + CI simulation run;
- no external TURN/STUN/device dependency;
- non-zero exit on contract breach.

## Scenario Matrix Source
CI gate reuses Step 25.6 runtime scenarios and adds CI-only stats gate semantics:
- `A_user_mute_unmute`
- `B_source_switch_replace_track`
- `C_transceiver_direction_desired_vs_effective`
- `D_sender_parameters_boundary`
- `E_quality_observability_getstats`
- `F_late_controls_after_close`
- `G_required_optional_stats_gate_semantics` (CI-only assertion over required/optional stats handling)

## Mandatory Assertions
- scenario result status is `PASS` for `A-F`;
- `replaceTrack` boundary keeps invalid-kind reject and late-abort non-mutating behavior;
- `direction` (desired) and `currentDirection` (effective) remain explicitly separated;
- sender parameter updates keep supported/unsupported/out-of-envelope/terminal deterministic actions;
- required stats families remain gating (`candidate-pair`/`outbound-rtp`/`inbound-rtp`);
- limited-availability metrics remain non-gating and must not fail CI.

## Fail Conditions
- scenario missing or unexpected in proof payload;
- scenario status not `PASS`;
- required assertion missing/false;
- replaceTrack boundary breach;
- direction desired/effective boundary breach;
- sender parameter boundary breach;
- required-vs-optional stats gate breach;
- incomplete or non-deterministic proof payload.

## Invariants
- CI gate reuses Step 25.6 sandbox scenario semantics;
- contract breach returns non-zero exit;
- required stats types stay gating;
- limited-availability metrics stay non-gating;
- build gate does not depend on external network/device runtime;
- production runtime path remains unchanged.

## Workflow Baseline
Workflow:
- `.github/workflows/webrtc-incall-media-control-ci.yml`

Runner:
- `server/tools/run_webrtc_incall_media_control_ci_simulation.py`

Dependencies:
- `server/tools/run_webrtc_incall_media_control_sandbox_smoke.py`
- `server/tools/check_webrtc_incall_media_control_quality_observability_baseline.py`
- `server/tools/check_webrtc_media_control_state_inventory.py`
- `server/tools/check_webrtc_mute_unmute_source_switch_transceiver_direction_contract.py`
- `server/tools/check_webrtc_sender_parameters_bitrate_codec_boundary_contract.py`
- `server/tools/check_webrtc_incall_quality_observability_baseline.py`
- `server/tools/check_webrtc_incall_media_control_ci_gate_baseline.py`

## Closure Criteria
Step 25.7 is closed when:
- baseline doc/module/checker/workflow/runner exist;
- CI job executes compile + Stage 25 checker set + simulation runner;
- local CI-equivalent simulation is green (`all` + targeted scenarios);
- compile and baseline checkers pass.

## Verification Type
- `build check`

## Build-Level Validation
Run locally:

```bash
cd server
.venv_tmpcheck/bin/python -m compileall app tools
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_quality_observability_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_control_state_inventory.py
.venv_tmpcheck/bin/python tools/check_webrtc_mute_unmute_source_switch_transceiver_direction_contract.py
.venv_tmpcheck/bin/python tools/check_webrtc_sender_parameters_bitrate_codec_boundary_contract.py
.venv_tmpcheck/bin/python tools/check_webrtc_incall_quality_observability_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO=A_user_mute_unmute .venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO=B_source_switch_replace_track .venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO=C_transceiver_direction_desired_vs_effective .venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO=D_sender_parameters_boundary .venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO=E_quality_observability_getstats .venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO=F_late_controls_after_close .venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
FLEXPHONE_WEBRTC_INCALL_CI_SCENARIO=G_required_optional_stats_gate_semantics .venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_ci_simulation.py
```

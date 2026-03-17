# Step 24.6 - Lifecycle CI Gate Baseline

## Goal
Convert Step 24 lifecycle contract into mandatory CI gate so lifecycle contract violations fail pipeline automatically.

## Scope
Step 24.6 defines CI gate for lifecycle contract coverage across Step 24 artifacts:
- state inventory and transition matrix (`24.2`);
- negotiation/glare role contract (`24.3`);
- reconnect/ICE-restart/pending-recovery contract (`24.4`);
- runtime scenario matrix proven in sandbox smoke (`24.5`).

## CI Topology
- GitHub Actions workflow with isolated lifecycle gate job;
- matrix strategy by lifecycle scenario id (`A-F`);
- compile + baseline checkers + CI simulation run per matrix row;
- non-zero exit on contract breach.

## Scenario Matrix Source
CI gate reuses exactly the Step 24.5 scenario matrix:
- `A_happy_path_lifecycle`
- `B_glare_collision_roles`
- `C_transient_disconnect_recovery`
- `D_failed_ice_restart_recovery`
- `E_late_signaling_ignored`
- `F_close_during_pending_recovery`

## Mandatory Assertions
- scenario result status is `PASS`;
- expected deterministic action matches contract;
- expected terminal/recovery end state matches contract;
- glare scenario keeps deterministic polite/impolite role actions;
- close scenario keeps terminal ownership and rejects late/stale signaling.

## Fail Conditions
- scenario missing or unexpected in proof payload;
- scenario status not `PASS`;
- end-state or deterministic-action mismatch;
- glare role action mismatch;
- failed/restart recovery contract mismatch;
- stale/late signaling mutates closed ownership;
- incomplete or non-deterministic proof payload.

## Invariants
- CI gate must reuse Step 24.5 scenario matrix;
- contract breach must return non-zero exit;
- no forbidden state-transition outcome is accepted;
- `closed` remains terminal;
- production runtime path remains unchanged.

## Workflow Baseline
Workflow:
- `.github/workflows/webrtc-lifecycle-ci.yml`

Runner:
- `server/tools/run_webrtc_lifecycle_ci_simulation.py`

Dependencies:
- `server/tools/run_webrtc_lifecycle_sandbox_smoke.py`
- `server/tools/check_webrtc_session_lifecycle_hardening_baseline.py`
- `server/tools/check_webrtc_peer_session_state_inventory.py`
- `server/tools/check_webrtc_negotiation_glare_resolution_contract.py`
- `server/tools/check_webrtc_reconnect_ice_restart_pending_recovery_contract.py`
- `server/tools/check_webrtc_lifecycle_ci_gate_baseline.py`

## Closure Criteria
Step 24.6 is closed when:
- baseline doc/module/checker/workflow/runner exist;
- CI matrix covers all lifecycle scenarios A-F;
- local CI-equivalent simulation is green for all scenarios;
- compile and baseline checkers pass.

## Verification Type
- `build check`

## Build-Level Validation
Run locally:

```bash
cd server
.venv_tmpcheck/bin/python -m compileall app tools
.venv_tmpcheck/bin/python tools/check_webrtc_session_lifecycle_hardening_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_peer_session_state_inventory.py
.venv_tmpcheck/bin/python tools/check_webrtc_negotiation_glare_resolution_contract.py
.venv_tmpcheck/bin/python tools/check_webrtc_reconnect_ice_restart_pending_recovery_contract.py
.venv_tmpcheck/bin/python tools/check_webrtc_lifecycle_ci_gate_baseline.py
FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO=A_happy_path_lifecycle .venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_ci_simulation.py
FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO=B_glare_collision_roles .venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_ci_simulation.py
FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO=C_transient_disconnect_recovery .venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_ci_simulation.py
FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO=D_failed_ice_restart_recovery .venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_ci_simulation.py
FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO=E_late_signaling_ignored .venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_ci_simulation.py
FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO=F_close_during_pending_recovery .venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_ci_simulation.py
```

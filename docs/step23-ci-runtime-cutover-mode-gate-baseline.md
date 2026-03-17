# Step 23.5 - CI Runtime Cutover Mode Gate Baseline

## Goal
Convert runtime cutover mode contract into mandatory CI gate, so contract violations fail pipeline automatically and cannot be merged silently.

## Scope
Step 23.5 defines CI gate for runtime cutover modes:
- `pubsub_legacy`
- `dual_write_shadow`
- `durable_authoritative`

Gate validates mode-specific runtime invariants, mismatch handling, reconnect/replay behavior, and rollback boundaries using isolated Redis-backed simulation.

## CI Topology
- GitHub Actions workflow with isolated job + Redis service container;
- matrix strategy by `mode`;
- compile + baseline checkers + mode simulation in each matrix job;
- non-zero exit code on contract breach.

## Gate Scenarios
- `pubsub_legacy`: legacy control-plane flow + rollback-to-legacy compatibility.
- `dual_write_shadow`: primary truth boundary on legacy path + forced mismatch detection (`legacy_ok_durable_append_fail`) + promotion block.
- `durable_authoritative`: durable replay/pending/dedup proof + rollback to shadow boundary.

## Fail Conditions
- mode contract violation;
- ownership boundary violation;
- shadow equivalence/mismatch action violation;
- unexpected promotion behavior;
- rollback boundary violation;
- replay/pending-recovery invariant violation;
- non-deterministic or incomplete proof payload.

## Invariants
- CI gate validates contract semantics, not only process startup;
- Redis is isolated per job via service container;
- gate remains production-path-neutral;
- contract breach always returns non-zero exit.

## Workflow Baseline
Workflow:
- `.github/workflows/runtime-cutover-ci.yml`

Runner:
- `server/tools/run_runtime_cutover_ci_simulation.py`

Dependencies:
- `server/tools/run_runtime_cutover_sandbox_smoke.py`
- `server/tools/check_durable_signaling_runtime_path_inventory.py`
- `server/tools/check_durable_signaling_dual_write_shadow_read_contract.py`
- `server/tools/check_runtime_cutover_ci_gate_baseline.py`

## Closure Criteria
Step 23.5 is closed when:
- baseline doc + workflow + CI simulation runner exist;
- workflow matrix runs all cutover modes;
- local CI-equivalent simulation for all modes reports success;
- compile/checkers pass.

## Verification Type
- `build check`

## Build-Level Validation
Run locally:

```bash
cd server
.venv_tmpcheck/bin/python -m compileall app tools
.venv_tmpcheck/bin/python tools/check_durable_signaling_runtime_path_inventory.py
.venv_tmpcheck/bin/python tools/check_durable_signaling_dual_write_shadow_read_contract.py
.venv_tmpcheck/bin/python tools/check_runtime_cutover_ci_gate_baseline.py
FLEXPHONE_CUTOVER_CI_MODE=pubsub_legacy .venv_tmpcheck/bin/python tools/run_runtime_cutover_ci_simulation.py
FLEXPHONE_CUTOVER_CI_MODE=dual_write_shadow .venv_tmpcheck/bin/python tools/run_runtime_cutover_ci_simulation.py
FLEXPHONE_CUTOVER_CI_MODE=durable_authoritative .venv_tmpcheck/bin/python tools/run_runtime_cutover_ci_simulation.py
```

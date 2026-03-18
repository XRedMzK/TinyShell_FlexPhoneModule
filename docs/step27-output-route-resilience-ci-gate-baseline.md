# Step 27.7 - Output-Route Resilience CI Gate Baseline

## Goal
Convert Stage 27 contracts and manual smoke evidence into fail-closed CI gate so contract regressions cannot pass silently.

## Scope
Step 27.7 defines CI gate for Stage 27 coverage across artifacts:
- output-route baseline scope and boundaries (`27.1`);
- output inventory visibility contract (`27.2`);
- selection/apply split and error classes (`27.3`);
- stale-sink fallback/rebind contract (`27.4`);
- `devicechange`-hint + enumerate-truth reconciliation contract (`27.5`);
- manual runtime smoke evidence completeness for matrix `A-F` (`27.6`).

## CI Contract vs Real Runtime
- CI gate validates deterministic contract and evidence integrity;
- CI gate does not attempt to prove real browser output-routing behavior in headless runtime;
- unsupported runtime capability is explicit outcome class and is never treated as `PASS`;
- fail-closed behavior is mandatory for missing/incomplete evidence or invariant breaches.

## Dependency Closure
Mandatory dependencies:
- `26.7`
- `27.1`
- `27.2`
- `27.3`
- `27.4`
- `27.5`
- `27.6`

CI gate must fail when any dependency checker is missing or non-green.

## Manual Smoke Evidence Contract
Evidence source:
- `docs/evidence/step27-output-route-resilience-sandbox-smoke-evidence.json`

Mandatory smoke scenario IDs:
- `A_non_default_apply_happy_path`
- `B_stale_sink_loss_fallback_default`
- `C_passive_rebind_after_return`
- `D_interactive_rebind_rotated_id`
- `E_explicit_reconcile_without_devicechange`
- `F_error_class_sanity`

Mandatory per-scenario fields:
- `scenario_id`
- `executed_at`
- `runtime_class`
- `result` (`PASS|FAIL|UNSUPPORTED`)
- `proof_refs`
- `verified_invariants`
- `notes`

## Mandatory Transition Invariants
- stale/apply-failure branch converges to fallback-to-default path;
- fallback preserves `preferred_sink_id`;
- passive and interactive rebind branches remain distinct;
- explicit reconcile path works without mandatory `devicechange` delivery;
- `devicechange` remains hint and fresh `enumerateDevices()` remains truth;
- `NotAllowedError` branch remains separate from stale-sink branch;
- `NotFoundError`/`AbortError` never map to success branch.

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
- `.github/workflows/webrtc-output-route-resilience-ci.yml`

Runner:
- `server/tools/run_webrtc_output_route_resilience_ci_gate.py`

## Closure Criteria
Step 27.7 is closed when:
- baseline doc/module/checker/runner/workflow exist;
- dependency closure on `27.1-27.6` is checker-enforced;
- evidence completeness check for matrix `A-F` is fail-closed;
- outcome classes `PASS|FAIL|UNSUPPORTED` are explicit and non-overlapping;
- compileall and all Stage 27 gate checks pass.

## Verification Type
- `build check`

## Build-Level Validation
Run locally:

```bash
cd server
.venv_tmpcheck/bin/python -m compileall app tools
.venv_tmpcheck/bin/python tools/check_webrtc_capture_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_audio_output_remote_playout_route_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_output_device_inventory_permission_policy_visibility_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_sink_selection_apply_semantics_error_class_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_output_device_loss_fallback_rebinding_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_output_devicechange_reconciliation_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_output_route_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/run_webrtc_output_route_resilience_ci_gate.py
```

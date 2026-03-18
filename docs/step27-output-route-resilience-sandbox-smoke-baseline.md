# Step 27.6 - Output-Route Resilience Sandbox Smoke Baseline

## Goal
Validate that Stage 27 contracts (`27.1-27.5`) hold in isolated sandbox runtime smoke scenarios for output-route resilience.

## Scope
Step 27.6 validates scenario-level behavior for:
- non-default sink selection/apply happy path;
- stale-sink loss fallback to default route;
- preference retention across fallback and rebind;
- passive and interactive rebind flows (including rotated id handling);
- explicit reconcile path correctness without dependency on `devicechange` delivery;
- phase-specific apply/permission error-class handling.

Step 27.6 is manual-runtime smoke oriented and does not change production runtime behavior.

## Preflight
- secure context assumptions are satisfied;
- at least one default route and one non-default route are represented in sandbox state;
- debug state fields are observable:
  - `preferred_sink_id`
  - `effective_sink_id`
  - `rebind_status`
  - `last_route_error_class`
  - reconcile reason/timestamp

## Scenario Matrix
- A: non-default route apply happy path (`select` -> `setSinkId`).
- B: stale-sink loss while playing -> deterministic fallback-to-default.
- C: passive rebind after preferred sink returns.
- D: interactive rebind with persisted/rotated id revalidation.
- E: explicit reconcile path without reliance on `devicechange` delivery.
- F: error-class sanity (`NotFoundError`/`AbortError`/`NotAllowedError`) branch separation.

## Acceptance Criteria
- stale-sink path converges to fallback-to-default;
- fallback keeps `preferred_sink_id` intact;
- passive/interactive rebind paths are deterministic and non-overlapping;
- explicit reconcile path restores correctness without mandatory `devicechange` delivery;
- error-class branches remain phase-specific and non-conflated;
- runner emits deterministic proof set and explicit success marker.

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
- `scenarios_passed`
- `scenarios_total`
- `explicit_reconcile_without_devicechange_supported`
- `fallback_preserves_preference`

## Closure Criteria
Step 27.6 is closed when:
- baseline doc and sandbox smoke runner are present;
- runner executes scenarios `A-F` successfully in local sandbox;
- manual runtime check output includes explicit success marker.

## Verification Type
- `manual runtime check`

## Manual Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_webrtc_output_route_resilience_sandbox_smoke.py
```

Success marker:
- `WebRTC output-route resilience sandbox smoke: OK`

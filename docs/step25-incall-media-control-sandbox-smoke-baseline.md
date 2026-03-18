# Step 25.6 - In-Call Media-Control Sandbox Smoke Baseline

## Goal
Validate that Stage 25 contracts (`25.2-25.5`) hold in deterministic isolated sandbox runtime simulation for in-call media-control operations and quality observability.

## Scope
Step 25.6 validates scenario-level runtime behavior for:
- user mute/unmute semantics via `MediaStreamTrack.enabled`;
- source-mute observation without user-intent overwrite;
- source switch via `RTCRtpSender.replaceTrack`;
- transceiver direction desired/effective separation and negotiation commit/rollback path;
- sender-parameter updates via `RTCRtpSender.getParameters/setParameters` including unsupported/out-of-envelope handling;
- `getStats()` quality observability proof over required surfaces and non-gating optional metrics.

Step 25.6 is an isolated manual sandbox smoke and does not change production runtime behavior.

## Scenario Matrix
- A: user mute/unmute with source-mute distinction proof.
- B: source switch (`replaceTrack`) success + invalid-kind reject + late-abort ignore.
- C: transceiver direction change desired/effective proof (`direction` vs `currentDirection`) with commit/failure rollback.
- D: sender-parameter update path (`bitrate_tuning`) + unsupported/out-of-envelope + terminal reject.
- E: quality observability proof (`candidate-pair`/`inbound-rtp`/`outbound-rtp`) with limited-metric non-gating handling.
- F: closed-session late control rejection and state-integrity proof.

## Acceptance Criteria
- each scenario reaches expected deterministic outcome;
- user mute and source mute are explicitly non-conflated;
- source switch is validated via sender binding semantics;
- direction desired/effective semantics and negotiation boundary remain explicit;
- sender-parameter updates remain separate from mute/switch/direction control paths;
- missing limited-availability metrics are classified `unknown_non_gating` and do not fail smoke;
- runner emits deterministic proof and explicit pass/fail marker.

## Expected Proof Set
Per scenario:
- `scenario_id`
- `operations`
- `deterministic_actions`
- `expected_contract_assertions`
- `status`

Global proof fields:
- `overall_status`
- `scenarios_passed`
- `scenarios_total`
- `required_stat_types`
- `non_gating_missing_metrics`

## Closure Criteria
Step 25.6 is closed when:
- baseline doc and sandbox smoke runner are present;
- runner executes scenarios A-F successfully in local sandbox;
- manual runtime check output includes explicit success marker.

## Verification Type
- `manual runtime check`

## Manual Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_webrtc_incall_media_control_sandbox_smoke.py
```

Success marker:
- `WebRTC in-call media-control sandbox smoke: OK`

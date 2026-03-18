# Step 27.1 - Audio Output and Remote Playout Route Resilience Baseline

## Goal
Define baseline for next roadmap stage `Audio Output / Remote Playout Route Resilience` after closure of Stage 26 capture-side resilience.

## Scope
Step 27.1 defines:
- remote audio playback routing scope for call/media playout elements;
- authoritative output-selection surfaces (`selectAudioOutput` and `setSinkId`);
- optional `AudioContext.setSinkId` path only when application explicitly owns Web Audio playout graph;
- output inventory and visibility model based on permission/policy-shaped `enumerateDevices()` snapshot;
- advisory role of `devicechange` and authoritative reconcile through fresh snapshot;
- deterministic fallback behavior for missing sink, blocked permission/policy, unsupported API, and sink-switch failure;
- explicit boundary excluding capture acquisition and transport-quality contracts.

Step 27.1 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Output-Selection Surfaces
- selection API: `navigator.mediaDevices.selectAudioOutput()`;
- apply API (media element path): `HTMLMediaElement.setSinkId()`;
- optional apply API (Web Audio path): `AudioContext.setSinkId()` only when playout owner path is explicitly declared;
- authoritative route apply must be tied to explicit output-route owner path, not capture-side logic.

## Output Inventory and Visibility Model
- authoritative inventory API: `navigator.mediaDevices.enumerateDevices()`;
- Stage 27 authoritative output kind: `audiooutput`;
- inventory is treated as permission/policy/visibility-shaped snapshot, not OS hardware truth;
- inventory semantics remain secure-context and enumeration-eligibility dependent;
- default output device handling is explicit and distinct from non-default sink routing.

## Permission and Policy Model
- `selectAudioOutput()` requires transient user activation;
- non-default output sink routing is permission-gated;
- `speaker-selection` Permissions Policy may block output selection/apply paths;
- policy/permission denial is classified as deterministic failure class (not ambiguous runtime drift);
- permission helper APIs may be observed but never replace authoritative apply/reconcile surfaces.

## Reconciliation Model
- `devicechange` is advisory refresh trigger only;
- authoritative reconciliation source is fresh `enumerateDevices()` snapshot;
- reconciliation correctness never depends on `devicechange` delivery timing/support;
- current route validity is checked by `sinkId` presence/eligibility in latest snapshot under allowed enumeration conditions.

## Deterministic Fallback Rules
- missing selected sink -> deterministic fallback to default sink or explicit re-selection requirement;
- policy/permission blocked sink -> fail-closed to allowed route and surface actionable user re-selection path;
- sink apply failure (`AbortError`) -> deterministic rollback/fallback outcome;
- unsupported `setSinkId`/`selectAudioOutput` -> deterministic degraded mode without route-switch assumption;
- fallback decisions are explicit and never inferred from capture-side contracts.

## Scope Boundary
- Stage 27 covers output routing / remote playout resilience only;
- capture acquisition (`getUserMedia`, `getDisplayMedia`) is out of scope;
- RTP sender/receiver quality/stat contracts remain out of scope for 27.1;
- signaling and transport durability contracts remain out of scope for 27.1.

## Invariants
- output-route owner path is explicit and separate from capture owner path;
- authoritative output apply surface is `setSinkId` (media element) or explicit Web Audio owner equivalent;
- authoritative output reconciliation surface is fresh `enumerateDevices()` snapshot;
- `devicechange` remains advisory and non-required for correctness;
- `speaker-selection` policy/permission constraints are explicit in routing decisions;
- fallback outcomes are deterministic and fail-closed;
- production runtime path switch is out of scope for Step 27.1.

## Closure Criteria
Step 27.1 is closed when:
- baseline doc/module/checker are present;
- scope, authoritative surfaces, permission/policy model, reconciliation model, and fallback rules are explicit;
- Stage 26 dependency alignment is checker-enforced;
- Stage 27 draft and verification map are explicit;
- checker and compileall pass.

## Verification Type
- `build check`

## Stage 27 Draft
- `27.1` baseline definition
- `27.2` output device inventory + permission/policy visibility contract
- `27.3` sink selection/apply semantics and error-class contract
- `27.4` output-device loss fallback and rebinding contract
- `27.5` output `devicechange` reconciliation contract
- `27.6` output-route resilience sandbox smoke baseline
- `27.7` output-route resilience CI gate baseline

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_capture_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_audio_output_remote_playout_route_resilience_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

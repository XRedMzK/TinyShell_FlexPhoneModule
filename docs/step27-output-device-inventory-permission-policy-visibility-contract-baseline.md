# Step 27.2 - Output Device Inventory and Permission/Policy Visibility Contract Baseline

## Goal
Define authoritative output-device inventory and visibility contract for remote playout routing over Step 27.1 output-route resilience baseline.

## Scope
Step 27.2 defines:
- authoritative output inventory surface for Stage 27 routing decisions;
- output inventory semantics as permission-shaped and policy-shaped snapshot (not complete OS hardware truth);
- `audiooutput` visibility model under `speaker-selection` policy constraints;
- default-vs-non-default sink visibility and permission semantics;
- explicit and implicit visibility paths for non-default sinks;
- identity rules for `deviceId`, `groupId`, and `label` for output routing inventory;
- boundary that keeps Stage 27 inventory contract focused on output playout routing.

Step 27.2 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Inventory Surface
- authoritative output inventory API: `navigator.mediaDevices.enumerateDevices()`;
- authoritative output kind in Stage 27: `audiooutput`;
- inventory snapshot is interpreted as permission/policy/visibility-shaped view;
- inventory snapshot is not interpreted as complete OS-level hardware truth;
- secure context, fully-active document, and visible document are required assumptions.

## Permission and Policy Visibility Semantics
- `speaker-selection` Permissions Policy gates output-device visibility/usability for routing;
- policy-blocked output devices are excluded from authoritative visibility assumptions;
- non-default output visibility/usability is permission-gated;
- permission helper APIs are optional hints and never replace authoritative inventory snapshot.

## Default vs Non-Default Sink Semantics
- default sink remains baseline-usable without additional non-default routing permission;
- non-default sinks require visibility permission path before authoritative routing use;
- missing non-default sinks in current snapshot are treated as missing in current visibility envelope, not absolute hardware absence.

## Visibility Paths
- explicit visibility path for non-default sink: `MediaDevices.selectAudioOutput()` grant;
- implicit visibility path for non-default sink: relevant `getUserMedia()` grant with same-`groupId` affinity;
- authoritative visibility confirmation always comes from fresh `enumerateDevices()` snapshot.

## Identity and Metadata Rules
- primary inventory identity key: `kind + deviceId`;
- `groupId` is association metadata only (affinity hint), not primary identity key;
- `label` is UX-only metadata and never authoritative identity key;
- routing logic must not use `label` as durable identifier.

## Scope and Boundary
- Step 27.2 covers output inventory and visibility semantics for remote playout routing;
- capture acquisition contracts remain out of scope;
- sender/receiver transport quality contracts remain out of scope;
- sink apply/error handling semantics are deferred to Step 27.3.

## Invariants
- `enumerateDevices()` is the authoritative output inventory surface for Stage 27;
- output inventory is a permission/policy-shaped snapshot, not OS hardware truth;
- default-vs-non-default distinction is treated as permission semantics, not full-list guarantee;
- non-default visibility requires explicit or implicit grant path;
- `speaker-selection` policy constraints are explicit in inventory interpretation;
- `kind + deviceId` is identity key; `groupId` association-only; `label` UX-only;
- production runtime path switch remains out of scope for Step 27.2.

## Closure Criteria
Step 27.2 is closed when:
- baseline doc/module/checker are present;
- authoritative output inventory surface, permission/policy visibility semantics, default-vs-non-default rules, and identity rules are explicit;
- dependency alignment with Step 27.1 is checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_capture_resilience_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_audio_output_remote_playout_route_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_output_device_inventory_permission_policy_visibility_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

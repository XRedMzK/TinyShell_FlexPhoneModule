# Step 26.2 - Media Device Inventory and Permission-Gated Visibility Contract Baseline

## Goal
Define authoritative inventory visibility contract for capture-side media-device discovery over Step 26.1 capture resilience baseline.

## Scope
Step 26.2 defines:
- authoritative inventory surface for capture-side device discovery;
- inventory semantics as permission-shaped/policy-shaped/visibility-shaped snapshot (not OS hardware truth);
- capture-scope inventory authority for `audioinput` and `videoinput`;
- observed-but-non-authoritative `audiooutput` handling under Stage 26 scope boundary;
- visibility state model (`redacted` -> `expanded*`) and transition assumptions;
- identity rules for `deviceId`, `groupId`, and `label`;
- explicit exclusion of display-source inventory from `enumerateDevices`/`devicechange` model;
- optional-hint boundary for `Permissions.query`.

Step 26.2 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Inventory Surface
- authoritative inventory API: `navigator.mediaDevices.enumerateDevices()`;
- snapshot is permission-gated, policy-gated, visibility-gated;
- secure context, fully-active document, and visible document are required assumptions;
- snapshot is not treated as complete OS-level hardware truth.

## Capture-Side Inventory Authority
- authoritative capture kinds: `audioinput`, `videoinput`;
- observed non-authoritative kind: `audiooutput`;
- Stage 26 excludes output-sink routing, therefore `audiooutput` is never capture-slot authority;
- default devices are expected first in ordered inventory snapshots.

## Visibility State Model
`inventory_visibility_state`:
- `redacted`:
  - pre-capture / no relevant grant exposure;
  - at most one entry per capture kind;
  - `deviceId`, `label`, `groupId` may be empty;
- `expanded_partial`:
  - partial exposure after grant or active capture for relevant kind(s);
  - non-default devices may become visible;
- `expanded_full_unknown`:
  - broad exposure available but current runtime capture not guaranteed live;
- `expanded_full_live`:
  - active local capture with expanded visibility for relevant kinds.

Visibility transitions are dynamic and may contract back to redacted after revoke/reset/policy changes.

## Identity and Metadata Rules
- primary inventory identity key: `kind + deviceId`;
- `groupId` is association metadata (affinity/grouping hint), never primary identity;
- `label` is UX-only metadata and never authoritative identity key;
- missing non-default entries in redacted state are not treated as hardware absence;
- device identity is origin-scoped and resettable by browser privacy lifecycle.

## Display-Capture Exclusion
- display capture sources are out of `enumerateDevices()` inventory contract;
- display-source changes are not inferred from `devicechange`;
- display-source inventory modeling belongs to Stage `26.4/26.5`, not `26.2`.

## Permissions Hint Boundary
- `Permissions.query` is optional hint surface only;
- unsupported permission names are tolerated and non-fatal to inventory correctness;
- authoritative truth remains actual inventory/capture behavior, not Permissions API response alone.

## Invariants
- `enumerateDevices()` is the only authoritative capture-device inventory surface in Stage 26;
- inventory is interpreted as exposure snapshot, not hardware truth;
- redacted pre-capture inventory must not be treated as exhaustive;
- `label` is never used as identity or reconciliation key;
- `groupId` is association-only metadata;
- display sources are non-enumerable in this contract;
- output-sink routing remains out of scope.

## Closure Criteria
Step 26.2 is closed when:
- baseline doc/module/checker are present;
- authoritative surface, state model, identity rules, and scope boundaries are explicit;
- dependency alignment with Step 26.1 is checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_ci_gate_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_capture_source_device_permission_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

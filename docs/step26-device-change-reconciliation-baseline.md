# Step 26.5 - Device-Change Reconciliation Baseline

## Goal
Define deterministic capture-side reconciliation contract where `devicechange` is advisory and authoritative reconciliation is based on fresh `enumerateDevices()` snapshots.

## Scope
Step 26.5 defines:
- `devicechange` role as optional advisory refresh trigger;
- authoritative reconciliation source and snapshot semantics;
- capture-side slot reconciliation rules for `mic` and `camera`;
- fallback refresh triggers that do not depend on `devicechange` availability;
- explicit exclusion of screen-share source changes from device-inventory reconciliation;
- deterministic reconciliation flow and boundary behavior under permission/policy/visibility constraints.

Step 26.5 is contract-definition only and does not introduce runtime behavior changes.

## Devicechange Advisory Trigger Model
- `devicechange` is opportunistic/advisory refresh trigger only;
- `devicechange` delivery is not correctness prerequisite;
- delayed/coalesced/missing `devicechange` delivery is tolerated by contract;
- receiving `devicechange` means "perform reconciliation", not "assume inventory truth changed exactly once".

## Authoritative Reconciliation Surface
- authoritative reconciliation source: fresh `navigator.mediaDevices.enumerateDevices()` snapshot;
- cached inventory is never authoritative for reconciliation outcome;
- snapshot is taken only when enumeration is allowed (secure context, fully active document, visible document);
- reconciliation result is interpreted as permission/policy/visibility-shaped inventory truth for current document context.

## Capture-Side Slot Reconciliation Rules
Scope covered by device-inventory reconciliation:
- `mic` (`audioinput`)
- `camera` (`videoinput`)

Rules:
- authoritative slot-binding comparison key: `kind + deviceId`;
- snapshot absence means "not present in current permission-visible inventory";
- snapshot absence is not interpreted as absolute OS-hardware absence;
- `audiooutput` may be observed but remains out of capture-slot authority.

## Fallback Refresh Trigger Set
Reconciliation fallback triggers (independent of `devicechange` support):
- post-success `getUserMedia()` acquire;
- post-terminal end of device-capture track;
- post-device acquire failure;
- on document recovery to enumeration-eligible state;
- explicit manual refresh trigger.

When `devicechange` is supported and fired, it is an additional trigger in the same refresh set.

## Display-Capture Exclusion from Device Reconciliation
- display-source changes do not participate in `devicechange`/`enumerateDevices` reconciliation;
- no screen-share source discovery via device inventory;
- no reliance on `devicechange` for `getDisplayMedia()` source changes;
- display-source lifecycle and reselection remain governed by Step `26.4` and fresh user-mediated `getDisplayMedia()` acquisition.

## Deterministic Reconciliation Flow
1. detect refresh trigger (`devicechange` if available, fallback trigger otherwise);
2. if enumeration is currently disallowed, mark reconcile as pending-deferred;
3. when enumeration becomes allowed, take fresh `enumerateDevices()` snapshot;
4. reconcile `mic/camera` slot bindings against snapshot;
5. classify outcomes (`binding_preserved`, `binding_missing_source`, `binding_blocked_permission`, `binding_requires_user_selection`);
6. never derive display-source changes from this flow.

## Invariants
- `devicechange` is advisory-only and never correctness-critical;
- authoritative reconciliation requires fresh `enumerateDevices()` snapshot;
- reconciliation is valid only under enumeration-eligible document conditions;
- fallback refresh triggers exist independent of `devicechange` support;
- `mic/camera` reconciliation and display-source lifecycle stay separated;
- no screen-share source decision is derived from device inventory snapshots;
- production runtime path switch is out of scope for Step 26.5.

## Closure Criteria
Step 26.5 is closed when:
- baseline doc/module/checker are present;
- advisory-vs-authoritative distinction (`devicechange` vs `enumerateDevices`) is explicit;
- fallback trigger set is explicit and independent of `devicechange` support;
- display-source exclusion from device reconciliation is explicit;
- deterministic reconciliation flow and outcome classes are checker-enforced;
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
.venv_tmpcheck/bin/python tools/check_webrtc_track_source_termination_semantics_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_device_change_reconciliation_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

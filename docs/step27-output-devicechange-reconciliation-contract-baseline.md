# Step 27.5 - Output `devicechange` Reconciliation Contract Baseline

## Goal
Define deterministic reconciliation contract for output routing where `devicechange` is advisory trigger and fresh `enumerateDevices()` snapshot is authoritative truth.

## Scope
Step 27.5 defines:
- trigger model for output-inventory reconciliation;
- authoritative ordered snapshot model for `audiooutput` devices;
- stale-sink trigger boundaries for preferred/effective sink ids;
- explicit branch for default-route change without stale sink;
- single-flight/coalesced reconciliation policy;
- explicit reconcile path that does not depend on `devicechange` delivery.

Step 27.5 is contract-definition only and does not introduce runtime behavior changes.

## Normative Basis
- `devicechange` is treated as hint trigger, not event-delta truth;
- user agent may coalesce/fuzz timing of `devicechange` notifications;
- output sink validity after device changes is confirmed via fresh `enumerateDevices()` snapshot and sink-id presence checks;
- output routing must not assume automatic UA fallback when selected sink disappears.

## Authoritative Reconcile Source
- authoritative inventory source: fresh `navigator.mediaDevices.enumerateDevices()` snapshot;
- authoritative reconciliation scope in this step: ordered `audiooutput` subset only;
- event payload fields (`devices`, `userInsertedDevices`) are optional telemetry surfaces and non-authoritative for correctness.

## Ordered Snapshot Model
Canonical snapshot fields:
- `visible_audiooutput_devices`: ordered list of visible devices;
- `visible_audiooutput_ids_ordered`: ordered sink-id list;
- `inventory_revision_hash`: deterministic hash over ordered snapshot;
- `default_route_revision`: deterministic marker for default-route changes.

Order-sensitive diff is mandatory: order changes are treated as reconciliation-relevant inventory changes.

## Trigger Taxonomy
Reconcile entrypoint must be invokable for:
- `devicechange` event;
- startup/bootstrap output routing;
- visibility regain/resume;
- `setSinkId()` apply failure (`NotFoundError`, `AbortError`);
- successful select/apply events that can change visible route state;
- explicit user/manual reconcile action.

## Stale-Sink Trigger Boundaries
- `preferred_sink_id != ""` and missing in current ordered ids => `preferred_stale`;
- `effective_sink_id != ""` and missing in current ordered ids => `effective_stale`;
- `effective_sink_id == ""` is default route and not stale;
- `NotAllowedError` branch is permission/policy branch and must not be merged into stale-sink branch.

## Default-Route Branch
When `effective_sink_id == ""`:
- sink-loss fallback branch is not triggered;
- reconciliation may still record `default_route_revision_changed` as route-change signal;
- default-route change and stale non-default sink are separate branches.

## Single-Flight and Coalescing Policy
- reconciliation runs as single-flight operation;
- if new trigger arrives during active pass, set `rerun_requested = true`;
- after current pass completes, execute one immediate rerun if requested;
- triggers are not processed as independent event-delta log entries.

## Deterministic Reconcile Flow
1. Accept trigger reason.
2. If reconcile active -> set rerun flag and return.
3. Acquire fresh `enumerateDevices()` snapshot.
4. Build ordered `audiooutput` snapshot and compute revision markers.
5. Compute `inventory_changed`, `inventory_order_changed`, `preferred_stale`, `effective_stale`, `default_route_revision_changed`.
6. If `effective_stale` and effective sink is non-default -> route to `27.4` fallback-to-default branch.
7. If `pending_rebind` and preferred sink visible -> attempt passive rebind path from `27.4`.
8. If rerun requested during pass -> run one immediate additional pass.

## Scope and Boundary
- Step 27.5 covers reconciliation contract only;
- fallback/rebind state semantics remain in Step 27.4;
- sandbox smoke is deferred to Step 27.6;
- capture-side device contracts remain out of scope.

## Closure Criteria
Step 27.5 is closed when:
- baseline doc/module/checker are present;
- authoritative ordered snapshot contract and trigger taxonomy are explicit;
- stale/default-route branch split and single-flight policy are explicit;
- dependency alignment with Step 27.1/27.2/27.3/27.4 is checker-enforced;
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
.venv_tmpcheck/bin/python tools/check_webrtc_sink_selection_apply_semantics_error_class_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_output_device_loss_fallback_rebinding_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_output_devicechange_reconciliation_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

# Step 27.4 - Output-Device Loss Fallback and Rebinding Contract Baseline

## Goal
Define deterministic sink-loss resilience contract for remote playout routing over Step 27.1/27.2/27.3 baselines.

## Scope
Step 27.4 defines:
- stale-sink detection semantics;
- fallback-to-default contract when preferred sink is lost or apply fails;
- preferred-vs-effective sink state separation;
- deterministic passive and interactive rebind modes;
- boundary between sink-loss resilience (`27.4`) and devicechange reconciliation trigger contract (`27.5`).

Step 27.4 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative State Model
State fields:
- `preferred_sink_id`: persisted user preference (`""` means default preference/no override);
- `effective_sink_id`: currently applied sink id on playout element (`""` means default route);
- `rebind_status`:
  - `bound`
  - `fallback_default`
  - `pending_rebind`
  - `rebind_required_user_activation`
  - `permission_blocked`
  - `unsupported`
- `last_route_error_class`:
  - `null`
  - `not_found`
  - `abort`
  - `not_allowed`
  - `invalid_state`
  - `unsupported`

## Terms
- stale sink: `preferred_sink_id != ""` and id missing in current `enumerateDevices()` `audiooutput` snapshot;
- apply failure: `setSinkId(preferred_sink_id)` fails with `NotFoundError` or `AbortError`;
- default fallback: successful `setSinkId("")`;
- passive rebind candidate: preferred id is visible again in authoritative snapshot;
- interactive rebind candidate: sink must be revalidated via explicit user `selectAudioOutput(...)` path.

## Normative Invariants
- sink loss is never assumed auto-recovered by UA behavior;
- stale sink or apply `NotFoundError`/`AbortError` requires deterministic fallback attempt to `setSinkId("")`;
- successful default fallback sets `effective_sink_id = ""` and preserves `preferred_sink_id`;
- fallback does not erase user preference;
- interactive rebind path requiring `selectAudioOutput()` is allowed only with explicit user activation;
- `devicechange` is advisory trigger only and never required for sink-loss correctness.

## Failure Taxonomy
- `NotFoundError` (apply phase): preferred sink missing/stale in current visibility envelope;
- `AbortError` (apply phase): sink-switch failure after selection/apply attempt;
- `NotAllowedError` (apply/selection): policy/permission branch (not sink-loss branch);
- `InvalidStateError` (selection): missing user activation for interactive rebind.

## Deterministic Event Flow
### A. Apply Preferred Sink
- apply success -> `effective_sink_id = preferred_sink_id`, `rebind_status = bound`;
- apply `NotFoundError` -> classify `stale_sink_missing`, attempt default fallback, set `pending_rebind` on success;
- apply `AbortError` -> classify `sink_switch_failed`, attempt default fallback, set `pending_rebind` on success;
- apply `NotAllowedError` -> classify `permission_blocked` and keep sink-loss branch separate.

### B. Stale Detection Without Apply
- reconcile fresh `enumerateDevices()` snapshot;
- if preferred non-default sink is missing, classify stale sink;
- attempt default fallback if effective route is stale/bound to missing sink;
- on successful fallback preserve preference and set `pending_rebind`.

### C. Passive Rebind
- trigger: reconcile/event loop sees preferred sink visible again;
- action: attempt `setSinkId(preferred_sink_id)` without user prompt;
- success outcome: `effective_sink_id = preferred_sink_id`, `rebind_status = rebound_or_bound`.

### D. Interactive Rebind
- trigger: explicit user action `restore preferred output`;
- action: `selectAudioOutput({ deviceId: preferred_sink_id })` then `setSinkId(returned.deviceId)`;
- if UA returns rotated id, update `preferred_sink_id` to returned id before apply;
- no interactive rebind calls from background reconcile path.

## Scope and Boundary
- Step 27.4 covers sink-loss fallback/rebind semantics only;
- sink selection/apply phase definitions remain in Step 27.3;
- devicechange trigger ordering/coalescing details are deferred to Step 27.5;
- capture-side contracts remain out of scope.

## Closure Criteria
Step 27.4 is closed when:
- baseline doc/module/checker are present;
- stale-sink detection, fallback-to-default, and passive/interactive rebind split are explicit;
- preferred-vs-effective sink persistence rule is explicit;
- dependency alignment with Step 27.1/27.2/27.3 is checker-enforced;
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
.venv_tmpcheck/bin/python -m compileall app tools
```

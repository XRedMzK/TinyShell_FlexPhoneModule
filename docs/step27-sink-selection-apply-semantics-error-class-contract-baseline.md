# Step 27.3 - Sink Selection/Apply Semantics and Error-Class Contract Baseline

## Goal
Define deterministic two-phase output-route contract for sink selection and sink apply over Step 27.1/27.2 baselines.

## Scope
Step 27.3 defines:
- strict split between sink selection path and sink apply path;
- phase-specific preconditions and error classes;
- persisted/reused sink-id revalidation rule;
- deterministic handling map for selection/apply failures;
- boundary between inventory visibility semantics (`27.2`) and apply/runtime semantics (`27.3`).

Step 27.3 is contract-definition only and does not introduce runtime behavior changes.

## Two-Phase Contract Model
- selection path (permission/user-choice): `navigator.mediaDevices.selectAudioOutput()`;
- apply path (route apply on playout element): `HTMLMediaElement.setSinkId()`;
- selection and apply are distinct operations with distinct failure semantics.

## Selection Path Preconditions
- secure context is required;
- transient user activation is required;
- selection is authoritative explicit permission-grant path for non-default output sink usage;
- successful selection returns output device metadata usable for subsequent apply path.

## Apply Path Preconditions
- secure context is required;
- apply is performed on specific remote playout `HTMLMediaElement`;
- apply path requires already-usable sink id;
- apply path is not a replacement for selection/permission path.

## Persisted Sink-ID Revalidation Rule
- persisted or previously-exposed sink ids are not treated as permanently valid;
- before relying on persisted sink id, application must revalidate through `selectAudioOutput()`;
- id rotation/revocation is treated as expected platform behavior and must not be interpreted as contract breach.

## Error-Class Matrix
### Selection Path
- `InvalidStateError` -> no transient activation;
- `NotAllowedError` -> policy blocked or user cancelled/denied selection;
- `NotFoundError` -> no available output devices for selection.

### Apply Path
- `NotAllowedError` -> policy/permission blocked sink apply;
- `NotFoundError` -> sink id missing/stale for current visibility envelope;
- `AbortError` -> sink switch failed at apply stage after selection path.

## Deterministic Handling Rules
- do not call `setSinkId()` as substitute for selection/permission;
- selection-phase `NotAllowedError` => `selection_blocked_or_cancelled` (retry only with fresh user action);
- apply-phase `NotAllowedError` => `apply_blocked_by_policy_or_permission` (no blind retry loop);
- selection/apply `NotFoundError` => stale/missing sink handling with fresh visibility/reselection flow;
- apply-phase `AbortError` => apply-failure class (selection success does not imply apply success);
- selection/apply failure classes are explicit and non-overlapping.

## Scope and Boundary
- Step 27.3 covers selection/apply semantics and deterministic error handling only;
- output inventory visibility remains in Step 27.2;
- output loss fallback/rebinding flow details are deferred to Step 27.4;
- capture-side contracts remain out of scope.

## Invariants
- sink selection and sink apply remain separate authoritative phases;
- transient activation applies to selection phase only;
- apply path never acts as implicit permission-grant path;
- persisted sink ids require revalidation through selection path before reuse;
- error matrix is phase-specific and deterministic;
- production runtime path switch remains out of scope for Step 27.3.

## Closure Criteria
Step 27.3 is closed when:
- baseline doc/module/checker are present;
- selection/apply split, preconditions, persisted-id revalidation, and phase-specific error matrix are explicit;
- dependency alignment with Step 27.1/27.2 is checker-enforced;
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
.venv_tmpcheck/bin/python -m compileall app tools
```

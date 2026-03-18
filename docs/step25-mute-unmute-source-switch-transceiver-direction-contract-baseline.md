# Step 25.3 - Mute/Unmute, Source-Switch, and Transceiver-Direction Contract Baseline

## Goal
Define deterministic in-call media-control behavior contract for `mute/unmute`, `source-switch`, and `transceiver-direction change` over Step 25.2 state inventory and ownership matrix.

## Scope
Step 25.3 defines:
- authoritative control surface for each operation;
- user-mute vs source-mute semantics distinction;
- source-switch eligibility and boundary rules;
- desired vs effective transceiver-direction semantics;
- renegotiation requirement matrix;
- deterministic case actions and ownership boundaries for success/fail/late-abort paths.

Step 25.3 is contract-definition only and does not change runtime behavior.

## Mute/Unmute Contract
- operation scope: `mic_mute_unmute`, `camera_mute_unmute`;
- authoritative control surface: `MediaStreamTrack.enabled`;
- authoritative owner: `media_runtime_owner`;
- user mute intent source: `local_ui_control_state`;
- source mute signal source: `MediaStreamTrack.muted`/`mute` event;
- `user mute != source mute` is mandatory semantics;
- renegotiation not required;
- terminal session rejects mutation.

## Source-Switch Contract
- operation scope: `source_switch_same_kind`;
- authoritative control surface: `RTCRtpSender.replaceTrack`;
- authoritative owner: `media_runtime_owner`;
- same-kind track relation required for default switch path;
- default switch path does not require renegotiation;
- renegotiation required when switching breaks negotiated envelope boundaries;
- terminal session rejects mutation.

## Transceiver-Direction Contract
- operation scope: `transceiver_direction_change`;
- authoritative control surface: `RTCRtpTransceiver.direction`;
- authoritative owner: `lifecycle_owner`;
- desired field: `direction`;
- effective negotiated field: `currentDirection`;
- desired/effective distinction must remain explicit;
- direction change requires negotiation to affect effective direction;
- terminal session rejects mutation.

## Renegotiation Requirement Matrix
- `mic_mute_unmute` -> no renegotiation
- `camera_mute_unmute` -> no renegotiation
- `source_switch_same_kind` -> no renegotiation by default
- `transceiver_direction_change` -> renegotiation required

## Deterministic Case Actions
Contract defines deterministic actions for:
- user mute/unmute requests;
- source-muted observation without user-intent flip;
- source-switch success and invalid-kind rejection;
- source-switch late-abort handling;
- direction change request, commit, and negotiation failure rollback.

## Ownership Boundaries
- UI intent is not authoritative without control-surface apply;
- track surface is authoritative for user mute operations;
- sender surface is authoritative for source switch operations;
- transceiver surface is authoritative for direction operations;
- source-mute signals are observational and must not overwrite user intent.

## Invariants
- one authoritative control surface per operation;
- `enabled` vs `muted` semantics remain distinct;
- `replaceTrack` is not treated as mute toggle;
- `direction` vs `currentDirection` semantics remain distinct;
- terminal session rejects operation mutation;
- production-path switch is out of scope for Step 25.3.

## Closure Criteria
Step 25.3 is closed when:
- baseline doc/module/checker are present;
- contract is aligned with Step 25.1 operation matrix and Step 25.2 ownership matrix;
- deterministic case actions and ownership boundaries are checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_quality_observability_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_control_state_inventory.py
.venv_tmpcheck/bin/python tools/check_webrtc_mute_unmute_source_switch_transceiver_direction_contract.py
.venv_tmpcheck/bin/python -m compileall app tools
```

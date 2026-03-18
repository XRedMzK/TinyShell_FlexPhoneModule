# Step 25.2 - Media Control State Inventory and Ownership Matrix Baseline

## Goal
Define canonical media-control state inventory and ownership matrix over Stage 25.1 baseline.

## Scope
Step 25.2 defines:
- canonical control surfaces (`MediaStreamTrack`, `RTCRtpSender`, `RTCRtpTransceiver`, UI control, remote-visible state, stats surface);
- desired vs effective state distinction per surface;
- authoritative owner per media-control operation;
- allowed state relations and non-conflation rules;
- inventory completeness and consistency checks.

Step 25.2 is contract-definition only and does not change runtime behavior.

## Canonical Control Surfaces
- `local_ui_control_state`
- `local_media_stream_track_state`
- `local_rtp_sender_state`
- `local_rtp_transceiver_state`
- `remote_visible_media_state`
- `quality_stats_surface`

## Desired vs Effective State Distinction
Required distinctions:
- track `enabled` intent vs source-driven `muted` runtime state;
- transceiver `direction` (desired) vs `currentDirection` (effective negotiated state);
- local UI control intent vs remote-visible media flow state.

`desired` and `effective` states must not be conflated.

## Operation Ownership Matrix
Canonical operations:
- `mic_mute_unmute` -> `MediaStreamTrack.enabled`, owner `media_runtime_owner`, no renegotiation;
- `camera_mute_unmute` -> `MediaStreamTrack.enabled`, owner `media_runtime_owner`, no renegotiation;
- `source_switch_same_kind` -> `RTCRtpSender.replaceTrack`, owner `media_runtime_owner`, no renegotiation;
- `transceiver_direction_change` -> `RTCRtpTransceiver.direction`, owner `lifecycle_owner`, renegotiation required;
- `sender_encoding_update` -> `RTCRtpSender.setParameters`, owner `media_runtime_owner`, no renegotiation.

All operations must reject terminal-session mutation.

## Allowed State Relations
- user mute controls `track.enabled`;
- source mute (`muted`) is not equal to user mute;
- `replaceTrack` updates sender binding surface;
- direction change affects `currentDirection` only after negotiation;
- `setParameters` affects sender surface, not `track.enabled`;
- stats surface is observability-only and not control-authoritative.

## Invariants
- each media-control operation has exactly one authoritative owner;
- desired/effective state separation is explicit;
- `enabled` vs `muted` distinction is mandatory;
- `direction` vs `currentDirection` distinction is mandatory;
- sender parameter state is distinct from track state;
- terminal sessions reject media-control mutation;
- production-path switch is out of scope for Step 25.2.

## Closure Criteria
Step 25.2 is closed when:
- baseline doc/module/checker are present;
- inventory covers all Stage 25.1 control surfaces and operations;
- ownership matrix and state relations are checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_quality_observability_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_control_state_inventory.py
.venv_tmpcheck/bin/python -m compileall app tools
```

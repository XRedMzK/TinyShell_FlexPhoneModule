# Step 25.1 - In-Call Media Control and Quality Observability Baseline

## Goal
Define baseline for next roadmap stage `In-Call Media Control and Quality Observability` over closed Stage 24 lifecycle contracts.

## Scope
Step 25.1 defines:
- media-control ownership boundaries for mute/unmute, source switch, transceiver direction, and sender parameter updates;
- explicit operation matrix for renegotiation-required vs non-renegotiation media controls;
- remote-visible media semantics contract;
- in-call quality observability surface based on `RTCPeerConnection.getStats`;
- closure criteria and verification-type plan for Stage 25 substeps.

Step 25.1 is contract-definition only and does not introduce runtime behavior changes.

## Ownership Boundaries
- UI control layer owns media-control intent (`mute`, `camera toggle`, `source switch`);
- lifecycle layer owns operation admissibility and renegotiation boundary decisions;
- media runtime layer owns track/sender/transceiver state mutation;
- observability layer owns stats sampling, projection, and severity classification;
- ownership overlap is forbidden.

## Operation Matrix Baseline
Canonical media-control operations:
- `mic_mute_unmute` (`MediaStreamTrack.enabled`) - no renegotiation;
- `camera_mute_unmute` (`MediaStreamTrack.enabled`) - no renegotiation;
- `source_switch_same_kind` (`RTCRtpSender.replaceTrack`) - no renegotiation;
- `transceiver_direction_change` (`RTCRtpTransceiver.direction`) - renegotiation required;
- `sender_encoding_update` (`RTCRtpSender.setParameters`) - no renegotiation.

Terminal-session mutation is disallowed for all operations.

## Remote-Visible Semantics
- `enabled=false` is treated as intentional mute semantics;
- `track.muted` and `track.enabled` semantics remain distinct;
- remote-visible media truth is derived from sender/transceiver state;
- terminal session rejects late media-control signals.

## Quality Observability Surface
Stats source:
- `RTCPeerConnection.getStats`

Required metrics:
- `candidate_pair.currentRoundTripTime`
- `candidate_pair.availableOutgoingBitrate`
- `candidate_pair.availableIncomingBitrate`
- `outbound_rtp.packetsSent`
- `outbound_rtp.bytesSent`
- `outbound_rtp.framesEncoded`
- `inbound_rtp.packetsLost`
- `inbound_rtp.jitter`
- `inbound_rtp.bytesReceived`

Required stat types:
- `candidate-pair`
- `outbound-rtp`
- `inbound-rtp`

## Invariants
- each media-control operation has a single canonical owner;
- renegotiation requirement is explicit per operation;
- mute/switch operations do not rely on ad-hoc signaling semantics;
- terminal sessions reject media-control mutations;
- in-call quality metrics are observable from `getStats`;
- production-path switch is out of scope for Step 25.1.

## Closure Criteria
Step 25.1 is closed when:
- baseline doc/module/checker are present;
- scope/invariants/ownership boundaries are explicit;
- Stage 25 closure and verification plan is explicit;
- checker and compileall pass.

## Verification Type
- `build check`

## Stage 25 Draft
- `25.1` baseline definition
- `25.2` media-control state inventory + ownership matrix
- `25.3` mute/unmute + source-switch + transceiver-direction contract
- `25.4` sender-parameters/bitrate/codec boundary contract
- `25.5` in-call quality observability baseline
- `25.6` in-call media-control sandbox smoke baseline
- `25.7` in-call media-control CI gate baseline

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_quality_observability_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

# Step 25.5 - In-Call Quality Observability Baseline

## Goal
Define canonical in-call quality observability contract over `RTCPeerConnection.getStats()` with required metrics, sampling semantics, severity mapping, and non-gating handling for limited-availability metrics.

## Scope
Step 25.5 defines:
- canonical stats surfaces for in-call quality (`candidate-pair`, `inbound-rtp`, `outbound-rtp`, optional `remote-inbound-rtp`);
- required quality metrics for network/transport and media core paths;
- optional enrichment metrics and limited-availability non-gating metrics;
- sampling cadence and rolling-window semantics;
- deterministic severity mapping rules for latency/loss/jitter/bitrate/video-freeze/audio-concealment indicators;
- non-gating handling contract for limited-availability stats.

Step 25.5 is contract-definition only and does not change runtime behavior.

## Canonical Stats Surfaces
- stats source: `RTCPeerConnection.getStats`
- required stat types:
  - `candidate-pair`
  - `inbound-rtp`
  - `outbound-rtp`
- optional enrichment stat types:
  - `remote-inbound-rtp`

## Required Metrics
Required metric groups:
- network/transport:
  - `candidate_pair.currentRoundTripTime`
  - `candidate_pair.availableOutgoingBitrate`
  - `candidate_pair.availableIncomingBitrate`
- inbound media core:
  - `inbound_rtp.packetsLost`
  - `inbound_rtp.jitter`
  - `inbound_rtp.bytesReceived`
- outbound media core:
  - `outbound_rtp.packetsSent`
  - `outbound_rtp.bytesSent`
  - `outbound_rtp.framesEncoded`

## Optional and Limited-Availability Metrics
Optional enrichment metrics:
- `inbound_video.framesPerSecond`
- `inbound_video.framesDecoded`
- `inbound_video.freezeCount`
- `inbound_audio.concealmentEvents`
- `inbound_audio.audioLevel`
- `outbound_rtp.qualityLimitationReason`
- `outbound_rtp.qualityLimitationDurations`
- `remote_inbound_rtp.fractionLost`

Limited-availability metrics are non-gating by contract and must not fail baseline validation when unavailable.

## Sampling Cadence and Window Semantics
- canonical sampling interval: `5000 ms`
- allowed runtime polling bounds: `2000-10000 ms`
- rolling window size: `6 samples`
- trend indicators must be evaluated using rolling-window or delta semantics;
- single-sample spikes are not authoritative for trend-based severity;
- `getStats()` caching/throttling behavior must be treated as sampling-model input.

## Severity Mapping Rules
Required indicator families:
- latency (`currentRoundTripTime`)
- loss (`packetsLost`/`packetsReceived` derived ratio)
- jitter (`inbound_rtp.jitter`)
- bitrate (`availableOutgoingBitrate`/`availableIncomingBitrate`)
- video freeze (`inbound_video.freezeCount` delta, optional non-gating)
- audio concealment (`inbound_audio.concealmentEvents` delta, optional non-gating)

Severity mapping must be deterministic (`healthy|degraded|critical`) and define threshold direction (`>=` or `<=`) per indicator.

## Non-Gating Handling for Limited Metrics
- missing limited-availability metric -> mark `unknown_non_gating`, continue evaluation;
- missing required metric -> contract breach;
- optional metrics may enrich diagnosis but must not block baseline pass;
- non-gating classification must remain explicit in severity output.

## Invariants
- `RTCPeerConnection.getStats` is the only canonical quality stats source;
- required metrics map to required stat types (`candidate-pair`, `inbound-rtp`, `outbound-rtp`);
- limited-availability metrics remain non-gating;
- severity mapping covers latency/loss/jitter/bitrate/video-freeze/audio-concealment;
- sampling cadence and rolling-window semantics are explicit and checker-enforced;
- production-path switch is out of scope for Step 25.5.

## Closure Criteria
Step 25.5 is closed when:
- baseline doc/module/checker are present;
- required/optional metric classes and non-gating handling are checker-enforced;
- sampling/severity contract is checker-enforced;
- dependencies with Steps 25.1-25.4 remain aligned;
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
.venv_tmpcheck/bin/python tools/check_webrtc_sender_parameters_bitrate_codec_boundary_contract.py
.venv_tmpcheck/bin/python tools/check_webrtc_incall_quality_observability_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

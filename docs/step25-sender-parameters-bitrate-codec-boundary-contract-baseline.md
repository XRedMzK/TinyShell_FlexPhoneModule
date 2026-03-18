# Step 25.4 - Sender Parameters, Bitrate, and Codec Boundary Contract Baseline

## Goal
Define sender-level transmission boundary contract for bitrate/encoding updates and codec/negotiation envelope separation over Steps 25.1-25.3.

## Scope
Step 25.4 defines:
- authoritative sender control surface for runtime transmission tuning;
- allowed runtime sender-parameter update classes;
- bitrate/encoding ownership boundaries vs track/transceiver surfaces;
- codec/negotiation envelope separation rules;
- desired vs effective sender-parameter semantics;
- deterministic success/fail handling for supported, unsupported, and out-of-envelope updates.

Step 25.4 is contract-definition only and does not change runtime behavior.

## Sender Control Surface Baseline
- operation scope: `sender_encoding_update`;
- authoritative read API: `RTCRtpSender.getParameters`;
- authoritative write API: `RTCRtpSender.setParameters`;
- authoritative owner: `media_runtime_owner`;
- terminal session rejects mutation.

## Allowed Runtime Update Classes
- `bitrate_tuning` (`encodings[].maxBitrate`) - default renegotiation not required;
- `encoding_activation_toggle` (`encodings[].active`) - default renegotiation not required;
- `degradation_preference_update` (`degradationPreference`) - default renegotiation not required.

All classes require envelope validation before apply.

## Bitrate and Encoding Ownership Boundaries
- sender parameters are authoritative for bitrate/encoding behavior;
- track `enabled` surface is not authoritative for bitrate tuning;
- transceiver direction surface is not authoritative for bitrate tuning;
- UI intent is not effective until sender apply succeeds.

## Codec and Negotiation Envelope Boundaries
- sender parameter update is not a substitute for offer/answer negotiation;
- out-of-envelope codec changes require renegotiation path;
- unsupported codec-related update must fail closed;
- codec preference negotiation surface is distinct from sender runtime tuning.

## Desired vs Effective Sender Parameters
- desired sender parameter source: policy/UI intent;
- effective sender parameter source: `getParameters()` after apply;
- desired and effective states must remain distinct;
- apply flow must follow read-modify-write contract.

## Deterministic Case Actions
- supported update -> apply via `setParameters` and verify effective state via `getParameters`;
- out-of-envelope update -> reject and require renegotiation;
- unsupported update -> reject and keep previous effective parameters;
- terminal session update request -> reject mutation;
- late update after close -> ignore and log.

## Invariants
- one authoritative sender surface for encoding updates;
- bitrate/encoding tuning is not mixed with track enable semantics;
- sender tuning is not mixed with transceiver direction negotiation semantics;
- codec envelope boundary is enforced;
- unsupported or out-of-envelope updates fail closed;
- production-path switch is out of scope for Step 25.4.

## Closure Criteria
Step 25.4 is closed when:
- baseline doc/module/checker are present;
- contract is aligned with Steps 25.1-25.3 baselines;
- deterministic case actions and boundary rules are checker-enforced;
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
.venv_tmpcheck/bin/python -m compileall app tools
```

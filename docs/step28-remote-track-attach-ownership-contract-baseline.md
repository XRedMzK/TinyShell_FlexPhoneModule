# Step 28.2 - Remote Track Attach and Ownership Contract Baseline

## Goal
Define deterministic remote-track attach ownership contract over Step 28.1 `Remote Media Attach / Autoplay / Track-State Resilience` baseline.

## Scope
Step 28.2 defines:
- authoritative ownership key and attach-owner model for remote media attachment;
- canonical handling for `RTCPeerConnection.track` events with stream-based and streamless variants;
- deterministic attach payload model for `HTMLMediaElement.srcObject` assignment;
- duplicate-attach guard and no-op policy for already-bound ownership keys;
- stable binding semantics for remount and reattach paths;
- explicit boundary that keeps autoplay/play-promise and track-state lifecycle deep semantics out of this step.

Step 28.2 is contract-definition only and does not introduce runtime behavior changes.

## Authoritative Ownership Model
- primary ownership key is receiver/transceiver-centric (`receiver` + `transceiver`) and not stream-index based;
- `track.id` is secondary diagnostic identity only;
- ownership must not rely on `event.streams[0]` existence because streamless-track events are valid;
- attach owner is a single writer for each remote media slot and is the only authority allowed to assign `srcObject`.

## ontrack Attach Contract
- authoritative attach trigger is `pc.ontrack`;
- attach payload resolution:
  - when `event.streams` is non-empty, canonical payload is event stream binding;
  - when `event.streams` is empty, attach owner uses deterministic synthetic stream container bound to the ownership key;
- streamless fallback must remain deterministic and re-entrant across repeated events.

## Attach Target and Binding State
- attach target is explicit remote media element slot;
- binding state persists as explicit contract record:
  - `owner_key`
  - `element_slot`
  - `stream_binding_key` (canonical stream id or synthetic stream key)
  - `attached_track_ids`
  - `binding_revision`
- binding comparison is membership/identity based, never dependent on UA track array order.

## Duplicate-Attach Guard
- duplicate attach is detected when ownership key, target slot, and effective stream-binding membership are unchanged;
- duplicate branch is deterministic no-op;
- duplicate branch must not reassign `srcObject`;
- non-duplicate branches are explicit: new binding, remount reattach, or membership update.

## Stable Remount/Reattach Semantics
- remount of media element with unchanged ownership key requires explicit reattach of existing binding state;
- reattach path preserves ownership identity and does not reclassify the branch as new-track arrival;
- reattach policy is deterministic for repeated remount cycles.

## Scope Boundary
- Step 28.2 covers attach ownership and binding stability only.
- Autoplay/play-promise policy branches are deferred to Step 28.3.
- Track temporary/terminal runtime semantics (`mute`/`unmute`/`ended`) are deferred to Step 28.4.
- Capture and output-route contracts remain out of Step 28.2 scope.

## Invariants
- primary attach ownership key is receiver/transceiver-centric;
- streamless `ontrack` path is first-class and deterministic;
- duplicate-attach branch is explicit no-op;
- `srcObject` assignments are single-writer controlled by attach owner;
- stable binding state exists and is order-insensitive for track membership;
- remount/reattach preserves existing ownership semantics;
- production runtime-path switch is out of scope for Step 28.2.

## Closure Criteria
Step 28.2 is closed when:
- baseline doc/module/checker are present;
- ownership key model, streamless fallback, duplicate guard, and stable binding semantics are explicit;
- dependency alignment with Step 28.1 is checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_track_attach_ownership_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

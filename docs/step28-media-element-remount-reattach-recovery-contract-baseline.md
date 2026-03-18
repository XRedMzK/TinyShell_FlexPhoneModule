# Step 28.5 - Media Element Remount/Reattach Recovery Contract Baseline

## Goal
Define deterministic remount/reattach recovery contract for remote media elements over Step 28.1-28.4 baselines.

## Scope
Step 28.5 defines:
- ownership-preservation rule where binding identity outlives individual DOM media element instances;
- deterministic remount detection and ownership-transfer semantics;
- explicit old-element teardown policy to prevent detached ghost playback;
- replay-safe reattach sequence (`srcObject` assignment + explicit `play()` attempt + outcome classification);
- duplicate-reattach no-op guard versus legitimate remount-driven reattach branch;
- explicit `AbortError` classification as transitional replay interruption during reattach.

Step 28.5 is contract-definition only and does not introduce runtime behavior changes.

## Ownership Outlives Element Rule
- remote binding ownership remains receiver/transceiver-centric and is not tied to a single DOM node instance;
- remount must not wait for a new `pc.ontrack` event for already-owned binding;
- media element instance is attach target only; ownership state persists independently.

## Remount Detection and Transfer Contract
- remount is detected when owner key is unchanged and media element instance identity changes;
- remount branch is `legitimate_reattach`, not duplicate attach;
- transfer sequence is deterministic:
  - mark previous element as `old_owner_pending_teardown`;
  - mark new element as `reattach_pending`;
  - replay attach+play sequence on new element.

## Old-Element Teardown Policy
- old detached element must be explicitly revoked from binding ownership;
- teardown path is mandatory when old element may still be potentially playing;
- teardown branch includes explicit pause/cleanup and optional `srcObject` clear boundary;
- old-element lifecycle is separate from track lifecycle and must not be left implicit.

## Replay-Safe Reattach Sequence
- reattach sequence is deterministic and single-owner controlled:
  1. bind new element target for existing owner key;
  2. assign canonical stream binding to `srcObject`;
  3. treat assignment as new media load cycle;
  4. run observed `play()` attempt;
  5. classify play outcome via Step 28.3 taxonomy.
- reattach path is never fire-and-forget;
- replay classification must remain stable across repeated remount cycles.

## Duplicate vs Legitimate Reattach Guard
- duplicate/no-op branch requires unchanged owner key, unchanged element instance, and unchanged provider binding;
- legitimate remount reattach requires unchanged owner key with changed element instance;
- duplicate branch must not rewrite `srcObject`;
- legitimate remount branch must replay attach+play sequence.

## Abort-Safe Reattach Classification
- `AbortError` during remount replay is classified as transitional `reattach_replay_interrupted` branch;
- `AbortError` in this branch is not source-invalid and not autoplay-policy block;
- current owner-driven replay attempt remains authoritative after interruption.

## Scope Boundary
- Step 28.5 covers remount/reattach recovery semantics only.
- Attach ownership model remains anchored in Step 28.2.
- Autoplay/play-promise taxonomy remains anchored in Step 28.3.
- Track interruption/end semantics remain anchored in Step 28.4.
- Sandbox runtime proof and CI gate are deferred to Step 28.6 and Step 28.7.

## Invariants
- binding ownership outlives DOM element instance;
- remount branch never waits for new `ontrack` to reattach existing binding;
- old-element teardown is explicit and mandatory for potentially playing detached node;
- reattach is replay-safe (`srcObject` + observed `play()` outcome);
- duplicate/no-op and legitimate remount reattach branches are deterministic and separated;
- `AbortError` during replay is transitional reattach interruption, not source/policy failure;
- production runtime change is out of scope for Step 28.5.

## Closure Criteria
Step 28.5 is closed when:
- baseline doc/module/checker are present;
- ownership-outlives-element and old-element teardown rules are explicit;
- remount replay-safe reattach sequence is explicit;
- duplicate/no-op versus legitimate remount reattach split is checker-enforced;
- dependency alignment with Step 28.1/28.2/28.3/28.4 is checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_track_attach_ownership_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_media_element_remount_reattach_recovery_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

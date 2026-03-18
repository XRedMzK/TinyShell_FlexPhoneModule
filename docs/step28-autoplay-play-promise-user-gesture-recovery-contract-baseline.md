# Step 28.3 - Autoplay, play()-Promise, and User-Gesture Recovery Contract Baseline

## Goal
Define deterministic autoplay/playback-start contract for attached remote media elements over Step 28.1 and Step 28.2 baselines.

## Scope
Step 28.3 defines:
- distinction between attach-complete and playback-start-complete states;
- autoplay intent semantics versus actual playback truth semantics;
- explicit `HTMLMediaElement.play()` promise outcome taxonomy;
- blocked-autoplay branch and explicit user-gesture recovery path;
- deterministic failure separation for policy block vs source-invalid/media-invalid branches;
- boundary that keeps detailed remote track lifecycle (`mute`/`unmute`/`ended`) outside Step 28.3.

Step 28.3 is contract-definition only and does not introduce runtime behavior changes.

## Autoplay Intent vs Playback Truth Model
- attach completion and `autoplay=true` represent playback intent, not playback success proof;
- playback truth requires observed `play()` outcome (resolved promise and/or playback-start event semantics);
- attach state transitions to `attached_pending_playback` before any playback-success classification.

## play() Promise Outcome Taxonomy
- `play()` resolved -> `playing`;
- `play()` rejected with `NotAllowedError` -> `blocked_requires_user_gesture`;
- `play()` rejected with `NotSupportedError` -> `source_invalid`;
- other `play()` rejection -> `playback_start_failed`.

All playback-start attempts are observed outcomes; fire-and-forget invocation is forbidden.

## Blocked-Autoplay Recovery Branch
- autoplay block is a dedicated recoverable branch and is not treated as remote-track failure;
- background auto-retry loops are forbidden for blocked autoplay;
- retry attempt after blocked autoplay is allowed only from explicit user action handler;
- successful user-gesture retry transitions to `playing`; repeated block keeps branch in `blocked_requires_user_gesture`.

## Policy-vs-Source Failure Separation
- `NotAllowedError` is treated as policy/user-gesture branch;
- `NotSupportedError` is treated as source-invalid/media-invalid branch;
- policy branch and source branch remain deterministic and non-overlapping;
- optional policy hints (for example autoplay policy helper APIs) are advisory and never replace `play()` outcome truth.

## Playback Startup State Model
Canonical states:
- `unattached`
- `attached_pending_playback`
- `play_attempt_inflight`
- `playing`
- `blocked_requires_user_gesture`
- `playback_start_failed`
- `source_invalid`

Canonical transitions:
- `unattached -> attached_pending_playback`
- `attached_pending_playback -> play_attempt_inflight`
- `play_attempt_inflight -> playing`
- `play_attempt_inflight -> blocked_requires_user_gesture`
- `play_attempt_inflight -> source_invalid`
- `play_attempt_inflight -> playback_start_failed`
- `blocked_requires_user_gesture -> play_attempt_inflight` (explicit user action only)

## Scope Boundary
- Step 28.3 covers playback start policy and recovery semantics only.
- Remote attach ownership remains in Step 28.2.
- Remote track runtime semantics (`mute`/`unmute`/`ended`) are deferred to Step 28.4.
- Capture and output-route contracts remain out of Step 28.3 scope.

## Invariants
- attach is never treated as playback success by itself;
- autoplay flag is intent, not success guarantee;
- every `play()` attempt has explicit resolved/rejected classification;
- `NotAllowedError` and `NotSupportedError` branches are deterministic and separated;
- blocked autoplay requires explicit user-gesture recovery branch;
- no infinite auto-retry for blocked autoplay;
- production runtime-path switch is out of scope for Step 28.3.

## Closure Criteria
Step 28.3 is closed when:
- baseline doc/module/checker are present;
- playback truth model, outcome taxonomy, blocked recovery path, and failure separation are explicit;
- dependency alignment with Step 28.1 and Step 28.2 is checker-enforced;
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
.venv_tmpcheck/bin/python -m compileall app tools
```

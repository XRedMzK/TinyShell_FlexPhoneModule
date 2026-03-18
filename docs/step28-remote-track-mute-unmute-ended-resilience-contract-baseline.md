# Step 28.4 - Remote Track mute/unmute/ended Resilience Contract Baseline

## Goal
Define deterministic remote-track runtime resilience contract that separates temporary interruption (`mute`/`unmute`) from terminal track end (`ended`) over Step 28.1-28.3 baselines.

## Scope
Step 28.4 defines:
- remote track lifecycle model for temporary interruption versus terminal end;
- explicit semantics boundary between source-muted events and user/application intent mute (`enabled`);
- deterministic event-driven handling for `mute`, `unmute`, `ended`, and explicit-stop terminal branch;
- UI/runtime boundaries that preserve binding on temporary interruption and mark terminal branch explicitly;
- explicit boundary that keeps remount/reattach recovery details out of this step.

Step 28.4 is contract-definition only and does not introduce runtime behavior changes.

## Lifecycle Model
- runtime truth surfaces:
  - `MediaStreamTrack.mute`
  - `MediaStreamTrack.unmute`
  - `MediaStreamTrack.ended`
  - `MediaStreamTrack.readyState` (`live|ended`)
- temporary interruption branch: muted source while track remains `live`;
- terminal branch: `ended` event or `readyState=ended` explicit-stop path.

## Temporary vs Terminal Semantics
- `mute` is temporary interruption and never terminal by itself;
- `unmute` is recovery of media flow for the same track binding;
- `ended` is terminal for current track object and forbids recovery-in-place;
- explicit `stop()` path is terminal-by-state and does not require `ended` event emission.

## enabled vs muted Separation
- source mute/unmute events represent source availability branch;
- user/app intent mute is managed through `MediaStreamTrack.enabled` and is orthogonal to source-muted branch;
- source interruption and user intent branches remain explicit and non-overlapping in runtime classification.

## Event-Driven Runtime Model
Canonical runtime states:
- `track_live_flowing`
- `track_live_temporarily_muted`
- `track_live_recovering`
- `track_ended_terminal`

Canonical transitions:
- `track_live_flowing -> track_live_temporarily_muted` on `mute`
- `track_live_temporarily_muted -> track_live_flowing` on `unmute`
- `track_live_flowing|track_live_temporarily_muted -> track_ended_terminal` on `ended` or explicit-stop terminal-state observation

## UI and Binding Boundaries
- on `mute`: preserve attach ownership and binding; do not classify as call-end;
- on `unmute`: restore flowing state on same binding;
- on `ended`: mark terminal remote-track branch and stop expecting `unmute` for same track object;
- no detach/teardown solely because of temporary source mute.

## Scope Boundary
- Step 28.4 covers remote-track runtime interruption/end semantics only.
- Attach ownership remains in Step 28.2.
- Autoplay/play-promise recovery remains in Step 28.3.
- Remount/reattach recovery sequencing is deferred to Step 28.5.

## Invariants
- `mute` is temporary and non-terminal;
- `unmute` is recovery of existing binding;
- `ended` and explicit-stop terminal state are terminal branches;
- temporary interruption preserves binding ownership;
- source mute branch and user intent mute branch are explicitly separated;
- `stop()` special-case does not require `ended` event as terminal proof;
- production runtime-path switch is out of scope for Step 28.4.

## Closure Criteria
Step 28.4 is closed when:
- baseline doc/module/checker are present;
- temporary-vs-terminal semantics and enabled-vs-muted separation are explicit;
- explicit-stop terminal branch is captured without requiring ended-event emission;
- dependency alignment with Step 28.1/28.2/28.3 is checker-enforced;
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
.venv_tmpcheck/bin/python -m compileall app tools
```

# Step 28.6 - Remote Media Resilience Sandbox Smoke Baseline

## Goal
Validate in manual-runtime sandbox that Stage 28 contracts (`28.1-28.5`) hold under remote attach, autoplay block/recovery, track-state transitions, and remount/reattach flows.

## Scope
Step 28.6 validates scenario-level behavior for:
- clean remote attach and playback start path;
- streamless-track attach fallback path (`event.streams` empty);
- autoplay-blocked branch with explicit user-gesture recovery;
- temporary remote interruption (`mute`/`unmute`) with binding preservation;
- terminal `ended` boundary without false auto-recovery;
- remount/reattach replay path including transitional `AbortError` classification.

Step 28.6 is manual-runtime smoke oriented and does not change production runtime behavior.

## Preflight
- target runtime is secure and consistent with project desktop sandbox profile;
- Stage 28 contract artifacts (`28.1-28.5`) are present;
- remote media state debug fields are observable:
  - `owner_key`
  - `stream_binding_kind`
  - `playback_state`
  - `track_runtime_state`
  - `current_element_key`
  - `old_element_torn_down`

## Scenario Matrix
- A: clean remote attach (`ontrack` with stream) -> attach -> `play()` resolved.
- B: streamless remote attach (`ontrack` with empty streams) -> deterministic fallback bind -> playback start.
- C: autoplay blocked (`play()` `NotAllowedError`) -> blocked branch -> explicit user-gesture retry -> playback start.
- D: temporary interruption (`mute` then `unmute`) -> binding preserved -> flowing restored.
- E: terminal track end (`ended`) -> terminal branch -> no false in-place recovery.
- F: remount/reattach while active or pending playback -> explicit old-element teardown + replay-safe attach/play; transitional `AbortError` classified as reattach interruption branch.

## Authoritative Observation Surfaces
- `RTCPeerConnection.track` event for attach trigger truth;
- `HTMLMediaElement.srcObject` for binding assignment truth;
- `HTMLMediaElement.play()` promise outcomes for playback start truth;
- `MediaStreamTrack.mute` / `MediaStreamTrack.unmute` / `MediaStreamTrack.ended` and `readyState` for track-state truth;
- explicit remount ownership transfer state (`owner_key`, `current_element_key`, `reattach_revision`) for reattach truth.

## Acceptance Criteria
- stream-based and streamless attach paths both reach deterministic attached state;
- duplicate attach is no-op and does not produce duplicate playout side effects;
- blocked autoplay is classified as policy/user-gesture branch and resolved only through explicit action;
- `mute`/`unmute` never detach binding or mark terminal;
- `ended` always lands in terminal branch for current track object;
- remount/reattach path tears down old element explicitly and replays attach+play on new element;
- `AbortError` during replay is classified as transitional reattach interruption, not source-invalid fatal branch;
- runner emits explicit scenario proof and success marker.

## Expected Evidence Schema
Per scenario:
- `scenario_id`
- `executed_at`
- `runtime`
- `browser_engine`
- `track_kind`
- `has_stream`
- `initial_play_outcome`
- `retry_play_outcome`
- `mute_seen`
- `unmute_seen`
- `ended_seen`
- `old_element_torn_down`
- `duplicate_attach_prevented`
- `final_binding_owner_key`
- `result`
- `proof_refs`
- `verified_invariants`
- `notes`

Global proof fields:
- `stage`
- `executed_at`
- `runtime_class`
- `source_runner`
- `scenarios`

## Closure Criteria
Step 28.6 is closed when:
- baseline doc, sandbox runner, and evidence artifact are present;
- runner executes scenarios `A-F` successfully in local sandbox simulation;
- evidence captures deterministic outcomes for blocked autoplay recovery, streamless attach, temporary vs terminal track transitions, and remount replay behavior;
- manual runtime check output includes explicit success marker.

## Verification Type
- `manual runtime check`

## Manual Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_webrtc_remote_media_resilience_sandbox_smoke.py
```

Success marker:
- `WebRTC remote media resilience sandbox smoke: OK`

# Step 29.5 - Dimension/Resize Reconciliation Contract Baseline

## Goal
Define deterministic intrinsic-dimension reconciliation contract for remote video elements without collapsing intrinsic media-dimension updates into failure/recovery branches.

## Scope
Step 29.5 defines:
- canonical intrinsic-dimension truth surfaces for remote video;
- initial dimension-proof semantics at metadata-ready boundary;
- subsequent intrinsic-dimension update semantics on `resize`;
- explicit separation between intrinsic media dimensions and CSS/layout box resizing;
- non-equivalence between dimension change and failure/remount/reattach triggers.

Step 29.5 is contract-definition only and does not introduce runtime behavior changes.

## Intrinsic Dimension Truth Surfaces
- intrinsic width source: `HTMLVideoElement.videoWidth`;
- intrinsic height source: `HTMLVideoElement.videoHeight`;
- initial dimension proof event: `HTMLMediaElement.loadedmetadata`;
- subsequent dimension update event: `HTMLVideoElement.resize`;
- supporting readiness surface: `HTMLMediaElement.readyState`.

## Initial Dimension-Proof Semantics
- before metadata-ready boundary, intrinsic dimensions may remain unknown/unproven;
- `readyState == HAVE_NOTHING` is treated as dimension-unproven branch where intrinsic dimensions may be `0`;
- initial dimension proof is established when metadata boundary is reached and intrinsic dimensions are known.

## Dimension Update Semantics
- `resize` is canonical runtime update surface for intrinsic dimension changes;
- intrinsic dimension change is a normal runtime update and not a failure signal by itself;
- intrinsic dimension updates require explicit reconciliation of runtime dimension snapshot.

## Intrinsic vs CSS/Layout Boundary
- canonical dimension truth for this contract is intrinsic media dimensions only (`videoWidth`/`videoHeight`);
- CSS/layout box resize is non-authoritative for intrinsic media-dimension truth;
- this step does not redefine UI container layout policy and does not use CSS box size as media-dimension source of truth.

## Failure/Recovery Non-Equivalence
- intrinsic dimension change is not terminal by default;
- intrinsic dimension change is not a reattach/remount trigger by default;
- intrinsic dimension change is not frame-progress proof and not freeze proof;
- dimension reconciliation remains orthogonal to starvation/recovery and progress-observability contracts.

## Classification States
Canonical branches:
- `dimension_unproven`
- `dimension_initial_proven`
- `dimension_update_observed`
- `dimension_reconciled`
- `dimension_invalid_snapshot`
- `terminal_out_of_scope`

## Scope Boundary
- Step 29.5 covers intrinsic dimension/resize reconciliation only.
- First-frame readiness threshold remains owned by Step 29.2.
- Frame-progress/freeze observability remains owned by Step 29.3.
- Waiting/stalled resume recovery remains owned by Step 29.4.

## Invariants
- intrinsic dimensions are canonical truth for this step;
- dimensions may be unproven before metadata-ready;
- `resize` is non-terminal intrinsic update signal;
- dimension updates are not failure/reattach triggers by default;
- intrinsic dimension reconciliation remains separate from progress/freeze/starvation classification.

## Closure Criteria
Step 29.5 is closed when:
- baseline doc/module/checker are present;
- intrinsic truth surfaces and metadata/resize boundaries are explicit;
- intrinsic-vs-layout boundary and non-equivalence to failure are explicit;
- dependency alignment with Steps 29.1-29.4 is checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_remote_video_first_frame_readiness_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_frame_progress_freeze_detection_observability_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_waiting_stalled_resume_recovery_contract_baseline.py
.venv_tmpcheck/bin/python tools/check_webrtc_dimension_resize_reconciliation_contract_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

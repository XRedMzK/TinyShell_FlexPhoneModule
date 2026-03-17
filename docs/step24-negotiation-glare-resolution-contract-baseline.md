# Step 24.3 - Negotiation + Glare-Resolution Contract Baseline

## Goal
Define deterministic negotiation and glare-resolution contract over standard WebRTC/JSEP signaling state machine, including role semantics, collision handling, rollback policy, and out-of-order signaling actions.

## Scope
Step 24.3 defines:
- canonical negotiation roles (`polite`, `impolite`);
- negotiation owner rules and ownership prerequisites;
- offer-collision detection baseline;
- `negotiationneeded` handling policy;
- signaling preconditions for SDP API calls (`setLocalDescription` / `setRemoteDescription`);
- deterministic action matrix for glare/late-answer/out-of-order signaling cases.

Step 24.3 is contract-definition only and does not modify runtime behavior.

## Negotiation Roles
- `polite`: on collision, perform rollback and accept incoming remote offer path.
- `impolite`: on collision, ignore conflicting incoming remote offer path.

Roles are negotiation semantics, not caller/callee identity.

## Negotiation Owner Rules
- single active negotiation owner per peer session;
- owner identity fields are explicit (`session_id`, `negotiation_epoch`, `owner_peer_id`, `owner_role`);
- local offer/answer commit requires owner;
- owner transfer is allowed only on glare path for polite peer.

## Offer-Collision Detection
Collision is detected when incoming offer arrives while:
- local signaling state indicates in-flight local offer path (`have-local-offer` / `have-local-pranswer`);
- or local negotiation is already in-flight;
- or non-stable offer-processing path is active.

## `negotiationneeded` Handling
- primary trigger for local renegotiation;
- start local offer only when signaling state is `stable`;
- parallel offer attempts are suppressed;
- repeated events during non-stable window are queued/coalesced.

## Signaling Preconditions for SDP API Calls
Preconditions are explicit for:
- `setLocalDescription(offer)` in `stable`;
- `setRemoteDescription(offer)` in `stable`;
- `setLocalDescription(answer)` in `have-remote-offer`;
- `setRemoteDescription(answer)` in `have-local-offer`;
- local rollback only from non-stable offer/answer states.

## Rollback Policy
- polite collision action: `rollback_then_apply_remote_offer`;
- impolite collision action: `ignore_incoming_offer`;
- rollback from `stable` is disallowed;
- rollback is valid only for collision/glare paths;
- post-rollback target signaling state is `stable`.

## Deterministic Case Actions
Canonical deterministic handling is defined for:
- glare offer collision;
- late answer after stable;
- duplicated answer;
- out-of-order offer in non-stable window;
- stale offer after rollback/epoch mismatch;
- signaling for closed/failed session.

## Invariants
- one active local negotiation attempt at a time;
- signaling state is source of truth for negotiation legality;
- collision handling is deterministic by role;
- rollback is not generic error-recovery hammer;
- glare resolution returns to stable/valid negotiation path;
- out-of-order signaling actions are deterministic;
- production runtime switch is out of scope for Step 24.3.

## Closure Criteria
Step 24.3 is closed when:
- doc/module/checker are present;
- role/collision/rollback policy is complete and checker-enforced;
- signaling preconditions and deterministic case actions are complete and checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_webrtc_negotiation_glare_resolution_contract.py
.venv_tmpcheck/bin/python -m compileall app tools
```

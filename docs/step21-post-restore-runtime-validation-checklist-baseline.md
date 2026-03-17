# Step 21.4 - Post-Restore Runtime Validation Checklist Baseline

## Goal
Define a runtime-oriented post-restore validation checklist that proves service admission, fail-closed behavior, auth/ws correctness, provisioning acceptance, and key observability signals without requiring replay/resurrection of transient Redis state.

## Runtime Validation Scope
Post-restore validation baseline covers:
- core service admission (`/health`, `/ready`);
- auth positive/negative runtime paths;
- WebSocket signaling positive/negative runtime paths;
- provisioning acceptance for Grafana file provisioning and Alertmanager config reload path;
- key observability signal presence after restore.

## Checklist Blocks

### A. Service Health and Admission
- startup/lifespan initialization completed;
- `GET /health` returns success;
- `GET /ready` returns success with dependencies present;
- dependency-loss check: `GET /ready` fail-closed (`503`) while `GET /health` remains alive.

### B. Auth Runtime Validation
- device register/bootstrap path succeeds;
- challenge issue succeeds;
- verify succeeds for fresh challenge;
- verify fails closed for stale/invalid/missing challenge state;
- token-protected path accepts only valid token state.

### C. WebSocket Runtime Validation
- authenticated WS connect succeeds;
- invalid/unauthenticated WS connect is rejected;
- reconnect semantics stay validation-driven (no stale/phantom state authority).

### D. Provisioning Acceptance Validation
- Grafana alerting resources accepted through file provisioning path;
- Alertmanager config validates before apply;
- Alertmanager startup/reload acceptance path succeeds.

### E. Key Observability Signals
- structured runtime logs remain present;
- `X-Request-ID` / `request_id` correlation remains present;
- key auth/ws/ready signals are observable;
- tracing exporter degradation remains non-fatal for runtime-path.

## Redis Recovery Awareness
- Checklist success does not require restoration of every transient Redis key or missed Pub/Sub fan-out event.
- Success criterion is convergence of valid clients and rejection of stale/invalid state.

## Invariants
- Step 21.4 validates runtime behavior and does not change production runtime-path.
- Step 21.4 follows Stage 20 provisioning compatibility path (file provisioning + Alertmanager reload).
- Step 21.4 reuses bounded-loss Redis semantics from Step 21.3.

## Closure Criteria
Step 21.4 is closed when manual runtime smoke confirms:
- `/health` and `/ready` admission expectations;
- auth positive and fail-closed negative outcomes;
- WS positive and reject outcomes;
- provisioning acceptance (Grafana file provisioning + Alertmanager config/reload);
- key observability signal presence;
- no reliance on replay of transient Redis Pub/Sub history.

## Verification Type
- `manual runtime check`

## Manual Smoke Harness
Primary harness:
- `server/tools/run_post_restore_runtime_validation_smoke.py`

Supporting harness for provisioning acceptance:
- `server/tools/run_alerting_provisioning_sandbox_smoke.py`

## Runtime Validation Command
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_post_restore_runtime_validation_smoke.py
```

Expected success markers include:
- `Health check: OK`
- `Readiness check: OK`
- `Auth positive/negative paths: OK`
- `WebSocket positive/negative paths: OK`
- `Observability snapshot checks: OK`
- `Readiness fail-closed with Redis down: OK`
- `Provisioning acceptance smoke: OK`
- `Post-restore runtime validation smoke: OK`

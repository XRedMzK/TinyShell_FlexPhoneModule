# Step 17.3 - Deployment Runbook Baseline

## Scope
- Define startup dependency policy.
- Define liveness/readiness/startup semantics.
- Define secrets contract for runtime and publish paths.
- Define a manual smoke checklist for runtime verification.

## Startup Dependency Policy
- Application startup is fail-fast for invalid mandatory runtime config.
- Mandatory runtime config must be provided via environment variables.
- Redis availability is checked by readiness (`/ready`), not by process liveness (`/health`).
- Tracing exporter degradation must not break auth/ws/reconcile runtime paths.

## Probe Semantics
- `GET /health`:
  - Purpose: liveness only.
  - Expected: `200` when process is alive.
  - Must not fail because Redis is unavailable.

- `GET /ready`:
  - Purpose: serving readiness.
  - Expected: `200` only when critical dependencies are available.
  - Fail-closed: returns `503` when `auth_challenge_redis` or `signaling_redis` is degraded.

- `startup probe` (container deployment recommendation):
  - Use for slow startup windows so liveness/readiness are not evaluated too early.

## Secrets Contract
### Required runtime
- `FLEXPHONE_AUTH_CHALLENGE_REDIS_URL`
- `FLEXPHONE_SIGNALING_REDIS_URL`
- `FLEXPHONE_AUTH_JWT_ISSUER`
- `FLEXPHONE_AUTH_JWT_AUDIENCE`
- `FLEXPHONE_AUTH_JWT_ALGORITHM`
- `FLEXPHONE_AUTH_JWT_SECRET` (or equivalent key material)

### Optional runtime
- `FLEXPHONE_OTEL_EXPORTER`
- `FLEXPHONE_OTEL_SERVICE_NAME`
- `FLEXPHONE_OTEL_OTLP_ENDPOINT`

### Required publish-only (desktop release path)
- `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`

## Operational Assumptions
- Backend clock is source of truth for `issued_at`, `expires_at`, `iat`, `exp`.
- Redis Pub/Sub loss is tolerated; correctness converges through shared Redis state + reconnect + startup reconciliation.
- Structured logging contract from Step 17.2 applies to runtime and degraded paths.

## Manual Runtime Smoke Checklist
1. Start backend with valid runtime env.
2. Verify `GET /health` -> `200`.
3. Verify `GET /ready` -> `200` (Redis available).
4. Register device, run `auth/challenge -> auth/verify`, confirm JWT issued.
5. Verify WS connect with valid token succeeds.
6. Verify WS connect without token fails closed.
7. Verify WS connect with expired token fails closed.
8. Stop Redis and verify `GET /ready` -> `503`.
9. Verify `GET /health` remains `200` while Redis is down.
10. Verify structured logs include `request_id`; include `trace_id/span_id` when span is active.
11. Verify tracing exporter degradation does not break auth/ws runtime path.

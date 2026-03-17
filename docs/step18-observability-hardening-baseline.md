# Step 18.1 - Observability Hardening Baseline

## Goal
Define a canonical observability contract for runtime diagnostics without changing runtime fail-closed/fail-open behavior implemented in previous steps.

## Signals Scope
- Traces
- Metrics (in-process counters baseline)
- Logs (structured JSON)

## Invariants
- Observability dependencies are non-fatal for runtime paths (`health/ready/auth/ws/reconcile`).
- `request_id` is mandatory for request-scoped logs.
- `trace_id` and `span_id` are present when an active span exists.
- `reason_code` is mandatory for reject/degraded/error paths.
- Runtime semantics from Step 17 are unchanged (including readiness fail-closed for Redis dependencies).

## Canonical Contract
### Resource Fields
- Required:
  - `service.name`
- Recommended (follow-up hardening):
  - `deployment.environment`
  - `service.version`
  - `service.instance.id`

### Correlation Fields
- `request_id`
- `trace_id`
- `span_id`
- `reason_code`
- `reason_class`

### Naming Surface
- Metric counters use dot-separated domain prefixes:
  - `health.*`
  - `ready.*`
  - `auth.*`
  - `ws.*`
  - `reconcile.*`
  - `http.requests.*` (path segment may be dynamic)
- Log events use dot-separated names, for example:
  - `http.request.completed|failed`
  - `auth.challenge.issued|rejected`
  - `auth.verify.succeeded|failed`
  - `ws.connect.accepted|rejected`
  - `ws.disconnect`
  - `runtime.ready.ok|degraded`
  - `reconcile.startup.*`
  - `reconcile.cleanup.*`

### Error Classification Baseline
- `operational`: runtime control-path results (`ok`, `http_error`, `peer_disconnected`, `reconcile_*`)
- `security`: auth/signature/token failures (`token_missing`, `token_expired`, `signature_mismatch`, etc.)
- `dependency`: storage/dependency degradation (`challenge_store_unavailable`, `session_store_unavailable`, `dependency_degraded`)

Canonical registry is implemented in:
- `server/app/observability_contract.py`
  - `CANONICAL_EVENT_NAMES`
  - `REASON_CLASS_BY_CODE`
  - `REASON_CLASSES`
  - `is_canonical_event_name()`
  - `is_canonical_counter_name()`

## Configuration Surface (Env-Driven)
- `FLEXPHONE_OTEL_EXPORTER` (`none|console|otlp`)
- `FLEXPHONE_OTEL_SERVICE_NAME`
- `FLEXPHONE_OTEL_OTLP_ENDPOINT`

Observability configuration remains externalized via environment variables.

## Build-Level Contract Check
Use the static contract checker:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

The checker validates:
- required env surface,
- OTel resource field wiring (`service.name`),
- structured log required keys and redaction surface,
- metric/event/reason naming conventions for literal values,
- presence and content of this baseline document.

Automated contract checks for Step 18.2:

```bash
cd server
.venv_tmpcheck/bin/python -m pytest -q -s tests/test_observability_contract.py tests/test_operational_logging.py
```

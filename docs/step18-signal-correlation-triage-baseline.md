# Step 18.3 - Signal Correlation & Triage Mapping Baseline

## Goal
Define one correlation contract across logs/traces/metrics and a baseline triage mapping that is stable for operational diagnostics.

## Correlation Contract
### Always Required
- `request_id`

### Required When Active Span Exists
- `trace_id`
- `span_id`

### Required For Reject/Error/Degraded Events
- `reason_code`
- `reason_class`

## Correlation Semantics
- `request_id` is an HTTP/runtime triage anchor and does not replace tracing context.
- `trace_id`/`span_id` link structured logs to tracing spans when a span is active.
- `reason_code` and `reason_class` carry operational meaning for routing triage.

## Resource & Naming Alignment
- Correlation fields align with Step 18.1 resource baseline (`service.name` required).
- Event names and reason taxonomy must stay aligned with Step 18.2 canonical registry:
  - `server/app/observability_contract.py`
- Triage routing mapping is defined in:
  - `server/app/observability_triage.py`

## Dashboard/Triage Mapping Baseline
- `dependency` -> `runtime-dependency-health`
- `security` -> `auth-security-rejections`
- `operational` -> `signaling-runtime-operations`

Domain hints:
- `runtime.ready.*` -> `runtime-dependency-health`
- `auth.*` -> `auth-security-rejections`
- `ws.*`, `reconcile.*`, `http.request.*` -> `signaling-runtime-operations`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Checker validates:
- presence of this doc and required sections,
- consistency of triage classes with reason taxonomy,
- required correlation fields in structured logging payload surface,
- mapping modules and naming surface compatibility.

# Step 19.1 - Reliability/SLO & Alerting Policy Baseline

## Goal
Define a reliability baseline that turns observability signals into actionable SLO policy and symptom-oriented alerting.

## SLI/SLO Scope
User-facing symptom SLI scope is limited to:
- `auth_availability`
- `ws_session_establishment`
- `readiness_availability` (operational SLO)

Rolling window baseline:
- `30d`

Targets:
- `auth_availability` = `99.9%`
- `ws_session_establishment` = `99.9%`
- `readiness_availability` = `99.5%`

## Reliability vs Security Boundary
- Reliability SLI bad events include runtime/dependency failures.
- Security-invalid paths are excluded from reliability SLI error accounting:
  - invalid token/signature,
  - invalid nickname/device mismatch,
  - challenge expired/consumed/not found misuse paths.

## Symptom-Based Alerting Invariants
- Paging is based on symptom SLI burn-rate breaches, not on every internal cause signal.
- Dependency signals (`Redis` degradation, storage unavailable, etc.) are triage/correlation signals unless they manifest as SLI burn.
- Observability dependency degradation (`otlp`/telemetry path) remains non-fatal to runtime-path.

## Burn-Rate Policy Baseline
For 99.9%-class SLO baseline:
- Fast page: burn rate `> 14.4` on `1h`, confirmed on `5m`.
- Slow page: burn rate `> 6` on `6h`, confirmed on `30m`.
- Budget erosion ticket: burn rate `> 1` on `3d`, confirmed on `6h`.

## Baseline Mapping Registry
Canonical policy mapping is implemented in:
- `server/app/reliability_alerting_baseline.py`
  - `SLI_BASELINE`
  - `SLO_BASELINE`
  - `BURN_RATE_ALERT_BASELINE`
  - `SLO_QUERY_MAPPING`
  - `validate_reliability_baseline_contract()`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Validation includes:
- presence/shape of Step 19.1 baseline artifacts,
- SLI/SLO/query mapping key consistency,
- error budget consistency (`error_budget = 1 - target`),
- burn-rate threshold/window/severity baseline checks,
- invariants for symptom-based alerting and non-fatal observability dependencies.

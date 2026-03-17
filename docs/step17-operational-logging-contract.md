# Step 17.2 - Structured Operational Logging Contract

## Scope
- JSON-only application logs for runtime triage.
- Correlation via `request_id` + `trace_id/span_id`.
- Stable `reason_code` contract for reject/degraded/error paths.

## Required Fields
- `ts`, `level`, `service`, `env`
- `event`, `message`, `component`, `reason_code`
- `request_id`, `trace_id`, `span_id`
- `route`, `method`

## Event Baseline
- `http.request.completed|failed`
- `auth.challenge.issued|rejected`
- `auth.verify.succeeded|failed`
- `ws.connect.accepted|rejected`
- `ws.disconnect`
- `reconcile.startup.started|completed`
- `reconcile.cleanup.started|completed`
- `runtime.ready.ok|degraded`

## Stable Reason Codes
- `ok`
- `http_error`
- `exception`
- `invalid_nickname`
- `device_not_registered`
- `wrong_device`
- `challenge_not_found`
- `challenge_expired`
- `challenge_consumed`
- `signature_mismatch`
- `token_missing`
- `token_invalid`
- `token_expired`
- `ws_rejected_preconnect`
- `dependency_ready`
- `dependency_degraded`
- `reconcile_started`
- `reconcile_completed`

## Redaction Rules
The following fields must be redacted before writing logs:
- `token`, `access_token`, `authorization`
- `password`, `secret`, `private_key`
- `challenge`, `signature`

## Non-Goals
- This baseline does not define log shipping/storage backend.
- This baseline does not replace trace exporters or metrics backends.

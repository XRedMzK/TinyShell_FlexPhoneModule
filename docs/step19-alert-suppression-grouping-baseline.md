# Step 19.4 - Alert Suppression & Grouping Baseline

## Goal
Define deploy-ready alert suppression baseline that reduces notification noise via grouping, inhibition and silence policy without changing runtime-path behavior.

## Grouping Baseline
Grouping policy is defined in:
- `server/app/reliability_alert_suppression_baseline.py`
  - `ALERT_GROUPING_BASELINE`

Grouping follows routing labels from Step 19.3 and uses severity-aware `group_by` sets:
- page alerts: narrow grouping (`service`, `component`, `severity`, `alert_class`, `routing_key`)
- ticket/info alerts: broader grouping for noise reduction

## Group Timing Controls
Timing policy is defined in:
- `ALERT_GROUP_TIMING_BASELINE`

Baseline timing controls:
- `group_wait`
- `group_interval`
- `repeat_interval`

Timing constraints:
- `group_wait <= group_interval <= repeat_interval`

## Inhibition Policy Baseline
Inhibition rules are defined in:
- `ALERT_INHIBITION_POLICY_BASELINE`

Invariants:
- inhibition uses explicit label-based parent/child mapping;
- `page -> ticket/info` suppression is allowed for same scope;
- `page -> page` inhibition is not allowed.

## Silence / Mute Policy Baseline
Silence policy is defined in:
- `ALERT_SILENCE_POLICY_BASELINE`

Policy requirements:
- each suppression policy requires `owner`, `reason`, and `time_bound`;
- suppression affects notifications only, not alert evaluation;
- page severity suppression must be explicitly time-bounded;
- recurring mute timing must not suppress page severity by default.

## Invariants
- Baseline extends Step 19.3 routing/escalation contract and does not change runtime instrumentation.
- Dedup behavior is defined as notification noise reduction, not exactly-once guarantee.
- Suppression policy must preserve symptom-based paging semantics from Step 19.1-19.3.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Validation includes:
- Step 19.4 doc presence and required sections,
- grouping label-set and timing consistency,
- inhibition safety checks (`page -> page` disallowed),
- silence ownership/time-bound/notifications-only constraints,
- doc-to-mapping contract alignment.

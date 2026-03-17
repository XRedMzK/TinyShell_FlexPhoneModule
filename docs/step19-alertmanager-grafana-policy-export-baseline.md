# Step 19.6 - Alertmanager/Grafana Policy Export Baseline

## Goal
Define deploy-ready policy export baseline for Alertmanager and Grafana so routing/grouping/inhibition/mute timing and delivery templates are exportable as config surface, not only in internal registries.

## Alertmanager Export Surface
Alertmanager export baseline is defined in:
- `server/app/reliability_alert_policy_export_baseline.py`
  - `ALERTMANAGER_EXPORT_BASELINE`
  - `ALERTMANAGER_ROUTE_EXPORT_BASELINE`
  - `ALERTMANAGER_RECEIVER_EXPORT_BASELINE`
  - `ALERTMANAGER_INHIBIT_EXPORT_BASELINE`
  - `ALERTMANAGER_TEMPLATE_EXPORT_BASELINE`

Exported resource scope:
- route entries per alert alias
- receiver mapping to notification targets
- inhibition rules
- template resources

## Grafana Export Surface
Grafana export baseline is defined in:
- `server/app/reliability_alert_policy_export_baseline.py`
  - `GRAFANA_EXPORT_BASELINE`
  - `GRAFANA_NOTIFICATION_POLICY_TREE_EXPORT_BASELINE`
  - `GRAFANA_CONTACT_POINT_EXPORT_BASELINE`
  - `GRAFANA_MUTE_TIMING_EXPORT_BASELINE`
  - `GRAFANA_TEMPLATE_EXPORT_BASELINE`

Exported resource scope:
- full notification policy tree
- contact points
- mute timing resources
- template resources

## Policy Tree Completeness
Export baseline requires full policy tree coverage:
- root node exists;
- each alert alias has exactly one export policy node;
- every non-root node has an existing parent.

## Static vs Runtime-Managed Suppression
Suppression export is split by surface:
- static export includes grouping/inhibition/mute timing baseline;
- runtime-managed surface remains for ephemeral silences.

Baseline constants:
- `STATIC_SUPPRESSION_EXPORT_BASELINE`
- `RUNTIME_MANAGED_SILENCE_BASELINE`

## Template Export Compatibility
Template export must remain compatible with Step 19.5 delivery schema:
- template required variables must be subset of `ALERT_TEMPLATE_VARIABLE_BASELINE`;
- template payload contract remains aligned with contact-point payload baseline.

## Invariants
- Step 19.6 extends Steps 19.1-19.5 policy contract and does not change runtime instrumentation/runtime-path behavior.
- Export mappings are deploy-ready configuration surface, not UI-only artifacts.
- Export baseline preserves symptom-based alert semantics and routing/severity contract from previous steps.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_observability_contract.py
```

Validation includes:
- Step 19.6 doc presence and required sections,
- Alertmanager/Grafana export completeness for aliases/policies,
- policy-tree parent/child consistency,
- grouping/inhibition/mute timing export consistency,
- template variable compatibility with Step 19.5,
- static-vs-runtime suppression separation and doc-to-mapping alignment.

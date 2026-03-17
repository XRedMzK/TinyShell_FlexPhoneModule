# Step 20.1 - Rendered Provisioning Artifacts Baseline

## Goal
Define deterministic rendered provisioning artifacts for Alertmanager and Grafana from Step 19.6 policy mappings, with build-level drift checks and no runtime-path change.

## Source of Truth and Rendered Layer
Source of truth remains mapping baselines from Step 19.6:
- `server/app/reliability_alert_policy_export_baseline.py`
- `server/app/reliability_alert_provisioning_artifacts_baseline.py`

Rendered files are derived artifacts:
- generated from mappings only;
- deterministic for identical input;
- never treated as primary policy source.

## Rendered Artifact Set
Artifact registry is defined in:
- `server/app/reliability_alert_provisioning_artifacts_baseline.py`
  - `RENDERED_PROVISIONING_ARTIFACTS_BASELINE`
  - `RENDERED_PROVISIONING_ARTIFACT_ORDER`

Rendered files:
- `server/generated/alertmanager/alertmanager.rendered.yml`
- `server/generated/grafana/provisioning/alerting/contact-points.rendered.yml`
- `server/generated/grafana/provisioning/alerting/policies.rendered.yml`
- `server/generated/grafana/provisioning/alerting/mute-timings.rendered.yml`
- `server/generated/grafana/provisioning/alerting/templates.rendered.yml`

## Drift-Check Contract
Drift contract is implemented in:
- `server/tools/check_alert_provisioning_artifacts.py`

Validation contract:
- render twice from same mapping -> identical bytes;
- baseline artifact set is complete (no missing rendered files);
- committed rendered files must match freshly rendered output;
- doc-to-mapping-to-artifact alignment remains consistent.

## Grafana Policy Tree Invariant
Rendered Grafana policies keep single-root tree semantics:
- exactly one root node;
- non-root nodes require existing parent;
- all policy routes map to known contact-point refs.

This is validated via:
- `validate_reliability_alert_provisioning_render_contract()`

## Alertmanager Linkage Invariants
Rendered Alertmanager config preserves linkage completeness:
- each route receiver must resolve to an existing receiver;
- inhibition rules remain aligned with suppression baseline;
- template references remain aligned with template export mapping.

## Invariants
- Step 20.1 materializes Step 19.6 policy mappings into files and does not change runtime instrumentation or runtime-path behavior.
- Rendered artifacts are deterministic and reproducible under build checks.
- Runtime-managed silences remain runtime-managed surface; static provisioning artifacts are separate.

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_alert_provisioning_artifacts.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- Step 20.1 doc presence and required sections;
- mapping/render baseline contracts;
- deterministic rendering and artifact drift checks;
- generated artifact completeness and newline/format sanity.

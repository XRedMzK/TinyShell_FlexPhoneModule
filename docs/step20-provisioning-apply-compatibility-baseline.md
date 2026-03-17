# Step 20.2 - Provisioning Apply/Compatibility Baseline

## Goal
Validate that rendered Alertmanager/Grafana artifacts from Step 20.1 are accepted by target provisioning/apply paths in an isolated local sandbox, without changing FlexPhone runtime-path.

## Scope
Step 20.2 verifies apply/compatibility only:
- Grafana file provisioning compatibility for rendered alerting resources.
- Alertmanager config validation and runtime reload compatibility.
- isolated sandbox execution only; no production wiring.

## Sandbox Inputs
Rendered artifacts (source: Step 20.1):
- `server/generated/alertmanager/alertmanager.rendered.yml`
- `server/generated/grafana/provisioning/alerting/contact-points.rendered.yml`
- `server/generated/grafana/provisioning/alerting/policies.rendered.yml`
- `server/generated/grafana/provisioning/alerting/mute-timings.rendered.yml`
- `server/generated/grafana/provisioning/alerting/templates.rendered.yml`

## Apply/Compatibility Contract
- Grafana reads rendered files from provisioning directory and starts without provisioning parse/apply errors.
- Grafana notification policy tree remains single-root and accepted as one policy-tree resource.
- Alertmanager config passes `amtool check-config`.
- Alertmanager starts with rendered config and accepts `POST /-/reload`.
- Validation is isolated from FlexPhone runtime-path.

## Platform Semantics Notes
- Grafana file-provisioning format is not equivalent to generic Alerting Provisioning HTTP API JSON payloads; this step checks file-provisioning compatibility.
- Alertmanager reload compatibility is validated via live reload endpoint and config check (`amtool`).

## Smoke Harness
Primary smoke harness:
- `server/tools/run_alerting_provisioning_sandbox_smoke.py`

Behavior:
- prepares temp sandbox layout with rendered files;
- runs `amtool check-config` in Alertmanager container image;
- starts Alertmanager + Grafana with Docker Compose sandbox;
- waits for readiness endpoints;
- executes Alertmanager reload;
- scans service logs for provisioning/config errors;
- prints deterministic PASS/FAIL summary;
- tears down sandbox containers.

## Invariants
- Step 20.2 extends Step 20.1 and does not modify runtime instrumentation or runtime-path behavior.
- Source of truth remains policy mapping + rendered artifacts; sandbox execution is validation-only.
- Failures in sandbox check must not change project runtime contract.

## Manual Runtime Check
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/run_alerting_provisioning_sandbox_smoke.py
```

Expected success markers:
- `amtool check-config: OK`
- `Alertmanager ready: OK`
- `Grafana ready: OK`
- `Alertmanager reload: OK`
- `Sandbox provisioning smoke: OK`

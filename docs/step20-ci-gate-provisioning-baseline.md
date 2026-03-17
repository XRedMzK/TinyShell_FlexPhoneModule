# Step 20.3 - CI Gate for Provisioning Artifacts Baseline

## Goal
Make Step 20.1 and Step 20.2 checks mandatory in CI so rendered provisioning artifacts drift or apply-compatibility regressions cannot be merged silently.

## CI Gate Scope
Step 20.3 introduces a dedicated CI job for provisioning artifacts:
- deterministic render + drift-check validation;
- artifact/checker compile sanity;
- isolated sandbox apply/compatibility smoke for Alertmanager/Grafana rendered files.

No production runtime-path changes are introduced by this step.

## Workflow Baseline
Workflow file:
- `.github/workflows/alerting-provisioning-ci.yml`

Job baseline:
- runs on Linux runner with Docker/Compose support;
- executes from `server/` directory;
- uses project scripts as source of truth for checks.

## Required CI Checks
The gate runs, in order:
1. `python -m compileall app tools`
2. `python tools/check_alert_provisioning_artifacts.py`
3. `python tools/run_alerting_provisioning_sandbox_smoke.py`

Acceptance criteria:
- all commands pass;
- any drift/apply/reload/provisioning parsing issue fails the pipeline.

## Isolation Invariant
- sandbox smoke uses temporary local layout and ephemeral containers only;
- no apply to production or shared runtime resources;
- no coupling with FlexPhone live runtime-path.

## Platform Compatibility Notes
- Grafana check in CI validates file-provisioning compatibility path (not HTTP alerting API update semantics).
- Alertmanager check includes both static config validation (`amtool check-config`) and runtime reload compatibility (`POST /-/reload`).

## Invariants
- Step 20.3 extends Steps 20.1-20.2 and preserves existing runtime contracts.
- Rendered artifacts remain derived from mapping source-of-truth; manual edits under `server/generated` remain disallowed without render-sync.
- CI gate is fail-fast and deterministic for the same repository state.

## Build-Level Verification
Step 20.3 verification:
- workflow present and wired with required commands;
- local contract checks stay green (`compileall`, `check_alert_provisioning_artifacts.py`);
- CI gate command surface matches Step 20.1/20.2 scripts exactly.

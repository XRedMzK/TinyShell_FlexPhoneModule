# Step 23.6 - Production Readiness + Rollback Contract Baseline

## Goal
Define production go/no-go and rollback contract for runtime cutover promotion, so transition to `durable_authoritative` is controlled by explicit criteria and reversible guardrails.

## Scope
Step 23.6 defines:
- promotion prerequisites for `dual_write_shadow` and `durable_authoritative`;
- rollback severity classes and trigger policy;
- protected deployment boundaries;
- rollback execution contract and post-rollback verification;
- required production evidence for promotion decision.

Step 23.6 is contract-definition only and does not perform production cutover.

## Promotion Go/No-Go Baseline
- Promotion to `dual_write_shadow` requires Step 23.1/23.2 readiness baseline and healthy dependency admission.
- Promotion to `durable_authoritative` requires completion and verification of Step 23.1-23.5.
- Promotion is blocked on unresolved shadow mismatch classes, replay/pending recovery instability, nondeterministic mode behavior, or missing protected deployment controls.

## Rollback Severity Classes
- `R1` observe only.
- `R2` freeze promotion.
- `R3` immediate rollback to previous safe mode.
- `R4` emergency rollback + incident procedure.

Severity mapping is deterministic and must not depend on ad-hoc operator judgment.

## Rollback Trigger Baseline
Canonical trigger classes include:
- sustained shadow-read mismatch;
- authoritative ownership boundary breach;
- reconnect/replay invariant breach;
- pending-recovery threshold breach;
- readiness degradation on signaling Redis dependency path;
- nondeterministic mode behavior;
- unpredictable durable recovery outcome.

## Rollback Execution Contract
- rollback initiator role is explicit (`oncall_or_release_operator`);
- mode switch is feature-flag controlled;
- in-flight sessions converge via reconnect/re-auth/reconciliation policy;
- post-rollback checks are mandatory (`health/ready`, signaling control-plane smoke, websocket reconnect validation, mismatch counter stability);
- incident evidence retention is mandatory.

## Protected Deployment Boundaries
- GitHub environment protection is required;
- manual approval is required;
- branch restrictions are required;
- wait timer or custom protection rule is allowed;
- unprotected direct promotion is forbidden.

## Required Production Evidence
Promotion decision requires:
- baseline checker set (`23.2`, `23.3`, `23.5`, `23.6`);
- runtime cutover CI workflow evidence;
- baseline docs for Step 23 contracts (`23.1-23.6`);
- post-rollback verification checklist presence.

## Invariants
- promotion is allowed only by explicit go/no-go criteria;
- rollback uses predefined targets and trigger classes;
- readiness fail-closed dependency guard remains intact;
- Pub/Sub at-most-once risk is accounted for in production cutover policy;
- production promotion without protected boundaries is forbidden.

## Closure Criteria
Step 23.6 is closed when:
- production readiness/rollback doc, module, and checker are present;
- promotion prerequisites and no-go conditions are explicit per target mode;
- rollback severity classes/triggers/actions are explicit and checker-enforced;
- protected deployment boundary contract is explicit and checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_runtime_cutover_production_readiness_rollback_contract.py
.venv_tmpcheck/bin/python -m compileall app tools
```

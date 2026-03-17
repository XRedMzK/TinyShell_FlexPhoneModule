# Step 21.2 - Source-of-Truth / Backup-Restore Inventory Baseline

## Goal
Define a strict inventory baseline for recovery: what is canonical and recoverable, what must be re-injected from external config/secrets, what is conditionally persistent, and what is transient bounded-loss state.

## Inventory Classes

### Class A - Git-Managed Canonical State
Recover via repository checkout and deterministic render/check path.

Includes:
- application code and contracts/docs/runbooks;
- mapping/baseline modules;
- CI workflows;
- deterministic rendered provisioning artifacts.

### Class B - External Env/Secrets State
Recover via operator-controlled env/secret injection, not from Git.

Includes:
- runtime env configuration;
- secret material (JWT signing keys, webhook credentials, admin credentials, SMTP credentials, Redis URLs, etc.).

### Class C - Persistent Operational State (Conditional)
Restore only if production depends on non-provisioned persistent service data.

Includes:
- Grafana DB/plugin data and any non-provisioned resources.

### Class D - Transient Bounded-Loss Runtime State
Explicitly outside backup/restore scope.

Includes:
- Redis auth challenge/session/presence runtime keys;
- Pub/Sub transient delivery state;
- in-flight ephemeral coordination state.

Recovery is convergence-based:
- `reconnect/re-auth/startup reconciliation`.

## Restore Ownership Boundaries
- `repo/build` owns recovery of Git canonical state.
- `ops/secrets` owns external env/secret re-injection.
- `ops/runtime` owns conditional persistent service-data restore.
- `app/runtime` owns bounded-loss convergence for transient runtime state.

## Inventory Matrix Baseline
| Inventory class | Examples | Source of truth | Backup requirement | Restore method | Owner |
| --- | --- | --- | --- | --- | --- |
| Git canonical | code/docs/mapping/CI/rendered deterministic artifacts | Git | required via repo remote | checkout + render/check | repo/build |
| Env/secrets | Redis URLs, JWT/signing secrets, webhook/SMTP/admin credentials | external config/secret system | required outside repo | re-injection at deploy/startup | ops/secrets |
| Persistent service data | Grafana DB/plugins when non-provisioned data is used | service storage | conditional | DB/file restore before service startup | ops/runtime |
| Transient runtime | Redis auth/signaling keys, Pub/Sub state, in-flight sessions | none (bounded-loss) | out of scope | convergence via restart/re-auth/reconnect | app/runtime |

## Normative Restore Statements
- Git is canonical for repository-managed code/contracts/mapping/CI and deterministic rendered provisioning artifacts.
- Rendered artifacts are derived: mapping remains authoritative semantic source; restore may use either committed rendered files or re-render + checker validation.
- Env/secrets are not repository-managed restore targets and must be restored through operator-controlled external injection.
- Redis-backed auth/signaling runtime state is transient bounded-loss state and is out of backup/restore scope.
- Grafana persistent DB/plugin state is a restore target only if runtime depends on non-provisioned resources.
- Alertmanager restore is satisfied by valid config restoration and startup/reload acceptance.

## Invariants
- Step 21.2 does not change production runtime-path.
- Step 21.2 does not redefine Stage 20 provisioning/rendering source-of-truth contract.
- Step 21.2 keeps file-provisioning semantics separate from HTTP provisioning API semantics.
- Backup scope covers only canonical and intentionally persistent state.

## Closure Criteria
Step 21.2 is closed when:
- inventory classes and ownership boundaries are explicit and checker-validated;
- inventory matrix is documented and aligned with mapping/check artifacts;
- bounded-loss transient-state boundary is explicit and checker-validated.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_recovery_restore_inventory_baseline.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- Step 21.2 doc required sections;
- inventory class/matrix/ownership contract consistency;
- bounded-loss transient-state boundary;
- linkage to existing Stage 20/21 artifacts.

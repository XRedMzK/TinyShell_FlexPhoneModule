# Step 23.3 - Dual-Write / Shadow-Read Runtime Contract Baseline

## Goal
Define dual-write / shadow-read runtime contract for durable signaling cutover, so transitional behavior is deterministic and semantic divergence is explicitly blocked.

## Scope
Step 23.3 defines:
- dual-write write-order and success boundary for authoritative runtime transitions;
- shadow-read observer-only boundary and semantic equivalence proof dimensions;
- mismatch class/action mapping and promotion blockers;
- promotion and rollback rules for transition from `dual_write_shadow` to `durable_authoritative`.

Step 23.3 is contract-definition only and does not execute production runtime cutover.

## Dual-Write Write Contract
In mode `dual_write_shadow`, authoritative transition write order is canonical:
- `durable_stream_append`
- `legacy_pubsub_publish`

Write contract rules:
- transition success requires both durable append and legacy publish;
- legacy publish success alone is not sufficient for authoritative transition correctness;
- runtime outcome source remains legacy apply path in `dual_write_shadow`.

## Shadow-Read Contract
Shadow-read boundary:
- role is `observer_non_authoritative`;
- shadow-read does not mutate production runtime outcome in `dual_write_shadow`;
- shadow-read validates semantic equivalence against durable replay/apply result;
- mismatch is treated as cutover blocker.

## Semantic Equivalence Proof Contract
Shadow-read equivalence dimensions are fixed:
- `event_identity`
- `ordering_within_scope`
- `apply_terminal_state`
- `dedup_result`
- `reconnect_replay_outcome`

Each authoritative transition must prove equivalence across all dimensions before promotion to `durable_authoritative`.

## Mismatch Classes and Actions
Canonical mismatch classes:
- `legacy_ok_durable_append_fail` -> `block_cutover_progression`
- `durable_ok_legacy_publish_fail` -> `block_cutover_progression`
- `legacy_ok_durable_read_mismatch` -> `block_cutover_progression`
- `legacy_ok_durable_apply_duplicate_mismatch` -> `block_cutover_progression`
- `legacy_ok_shadow_read_timeout` -> `block_promotion_wait_for_recovery`
- `legacy_and_durable_divergent_terminal_state` -> `rollback_to_pubsub_legacy`

## Promotion Rules to Durable Authoritative
Promotion from `dual_write_shadow` to `durable_authoritative` requires:
- shadow equivalence pass;
- no unresolved mismatch blockers;
- pending recovery pass;
- replay reconciliation pass;
- durable append success on authoritative transitions.

## Rollback Rules
Rollback baseline:
- rollback is allowed from `dual_write_shadow` to `pubsub_legacy`;
- divergent terminal-state mismatch may trigger rollback;
- rollback must preserve committed authoritative durable state.

## Invariants
- dual-write runtime outcome source remains legacy apply path;
- Pub/Sub is not authoritative for correctness;
- shadow-read remains observer-only;
- promotion requires semantic equivalence;
- production-path switch is out of scope in Step 23.3.

## Closure Criteria
Step 23.3 is closed when:
- doc, module, and checker are present;
- dual-write / shadow-read contract is complete for all authoritative transitions from Step 23.2;
- mismatch/action and promotion/rollback rules are explicit and checker-enforced;
- checker and compileall pass.

## Verification Type
- `build check`

## Build-Level Validation
Run:

```bash
cd server
.venv_tmpcheck/bin/python tools/check_durable_signaling_dual_write_shadow_read_contract.py
.venv_tmpcheck/bin/python -m compileall app tools
```

Validation covers:
- required Step 23.3 doc sections;
- authoritative transition coverage and dual-write mode consistency with Step 23.2;
- shadow-read equivalence dimensions and mismatch class/action mapping completeness;
- promotion and rollback rule consistency with Step 23.1 and Step 22.3 contracts.

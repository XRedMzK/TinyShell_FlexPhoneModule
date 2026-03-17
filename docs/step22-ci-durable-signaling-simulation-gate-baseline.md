# Step 22.5 - CI Durable Signaling Simulation Gate Baseline

## Goal
Make durable signaling correctness from Steps 22.2-22.4 mandatory in CI via deterministic simulation gate, not by ad-hoc local smoke only.

## Scope
Step 22.5 adds CI gate for authoritative durable signaling scenarios in isolated disposable environment:
- append + live delivery;
- disconnect + replay;
- pending recovery (`read_without_ack -> claim -> ack`);
- duplicate apply dedup no-op.

No production runtime-path changes are introduced.

## CI Workflow Baseline
Workflow file:
- `.github/workflows/durable-signaling-ci.yml`

Job baseline:
- `durable-signaling-simulation-gate`
- Ubuntu runner
- isolated Redis service container
- server working-directory
- deterministic script-driven checks.

## Required CI Steps
1. `python -m compileall app tools`
2. `python tools/check_signaling_event_inventory_baseline.py`
3. `python tools/check_signaling_durable_event_model_baseline.py`
4. `python tools/run_durable_signaling_ci_simulation.py`

Simulation runner uses:
- `FLEXPHONE_DURABLE_SIM_REDIS_URL` from CI service container endpoint.

## Service Topology
- Redis is provided by GitHub Actions service container.
- backend app is started by runner script in CI job context.
- no external/prod endpoints or secrets are used.

## Deterministic Proof Set
Simulation output must include:
- `event_id`
- `stream_entry_id`
- `consumer_group`
- `live_delivery`
- `replay_delivery`
- `pending_before`/`pending_after_recovery_ack`
- `dedup_hits`

Gate fails if any required scenario/invariant fails.

## Invariants
- CI validates recoverability/correctness contract, not full replay of all transient Pub/Sub history.
- replay source for authoritative events is durable stream path.
- idempotent apply must hold under duplicate delivery attempts.
- pending recovery must be observable and ack-completable.
- gate remains production-path-neutral.

## Closure Criteria
Step 22.5 is closed when:
- baseline doc, workflow, and CI simulation runner are present;
- CI workflow defines isolated Redis service container and deterministic simulation job;
- compile + baseline checkers + simulation runner pass;
- progress log records 22.5 completion and Stage 22 closure.

## Verification Type
- `build check`

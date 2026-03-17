from __future__ import annotations

import os
from typing import Any

from run_runtime_cutover_sandbox_smoke import (
    RuntimeCutoverSandboxSmokeError,
    run_runtime_cutover_sandbox_smoke,
)


VALID_MODES = {"pubsub_legacy", "dual_write_shadow", "durable_authoritative", "all"}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _assert_pass_status(errors: list[str], label: str, payload: Any) -> None:
    if not isinstance(payload, dict):
        _fail(errors, f"{label}: payload must be object")
        return
    if payload.get("status") != "PASS":
        _fail(errors, f"{label}: expected status=PASS, got {payload.get('status')}")


def _validate_mode_contract(mode: str, proof: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    modes = proof.get("modes")
    summary = proof.get("summary")

    if not isinstance(modes, dict):
        _fail(errors, "proof.modes must be object")
        return errors
    _assert_pass_status(errors, "summary", summary)

    if mode in {"pubsub_legacy", "all"}:
        _assert_pass_status(errors, "modes.pubsub_legacy", modes.get("pubsub_legacy"))
        _assert_pass_status(errors, "modes.rollback_dual_to_legacy", modes.get("rollback_dual_to_legacy"))

    if mode in {"dual_write_shadow", "all"}:
        shadow = modes.get("dual_write_shadow")
        _assert_pass_status(errors, "modes.dual_write_shadow", shadow)
        if isinstance(shadow, dict):
            if shadow.get("primary_truth_source") != "legacy_primary_apply_path":
                _fail(
                    errors,
                    "modes.dual_write_shadow.primary_truth_source must be legacy_primary_apply_path",
                )
            if shadow.get("forced_mismatch_class") != "legacy_ok_durable_append_fail":
                _fail(
                    errors,
                    "modes.dual_write_shadow.forced_mismatch_class must be legacy_ok_durable_append_fail",
                )
            if shadow.get("forced_mismatch_action") != "block_cutover_progression":
                _fail(
                    errors,
                    "modes.dual_write_shadow.forced_mismatch_action must be block_cutover_progression",
                )
            if shadow.get("promotion_blocked") is not True:
                _fail(errors, "modes.dual_write_shadow.promotion_blocked must be true")

    if mode in {"durable_authoritative", "all"}:
        durable = modes.get("durable_authoritative")
        _assert_pass_status(errors, "modes.durable_authoritative", durable)
        if isinstance(durable, dict):
            for scenario_name in ("scenario_a", "scenario_b", "scenario_c", "scenario_d"):
                _assert_pass_status(errors, f"modes.durable_authoritative.{scenario_name}", durable.get(scenario_name))
        _assert_pass_status(errors, "modes.rollback_durable_to_shadow", modes.get("rollback_durable_to_shadow"))

    return errors


def run_ci_simulation() -> int:
    mode = os.getenv("FLEXPHONE_CUTOVER_CI_MODE", "all").strip()
    redis_url = os.getenv("FLEXPHONE_CUTOVER_CI_REDIS_URL", "redis://127.0.0.1:6379/0").strip()
    if mode not in VALID_MODES:
        print(
            "Runtime cutover CI simulation: FAILED - "
            f"unsupported FLEXPHONE_CUTOVER_CI_MODE={mode!r}; expected one of {sorted(VALID_MODES)}"
        )
        return 1

    print(f"Runtime cutover CI simulation mode={mode} redis_url={redis_url}")
    proof_obj = run_runtime_cutover_sandbox_smoke(redis_url=redis_url, return_proof=True)
    if not isinstance(proof_obj, dict):
        print("Runtime cutover CI simulation: FAILED - runner did not return proof payload")
        return 1

    errors = _validate_mode_contract(mode, proof_obj)
    if errors:
        print("Runtime cutover CI simulation: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print(f"Runtime cutover CI simulation mode={mode}: OK")
    return 0


def main() -> int:
    try:
        return run_ci_simulation()
    except RuntimeCutoverSandboxSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"Runtime cutover CI simulation: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Runtime cutover CI simulation: FAILED (unexpected) - {exc!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

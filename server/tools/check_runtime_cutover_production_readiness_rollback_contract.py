from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_23_6_PATH = ROOT.parent / "docs" / "step23-production-readiness-rollback-contract-baseline.md"
DOC_23_5_PATH = ROOT.parent / "docs" / "step23-ci-runtime-cutover-mode-gate-baseline.md"
WORKFLOW_23_5_PATH = ROOT.parent / ".github" / "workflows" / "runtime-cutover-ci.yml"

REQUIRED_DOC_23_6_PHRASES = (
    "## Goal",
    "## Scope",
    "## Promotion Go/No-Go Baseline",
    "## Rollback Severity Classes",
    "## Rollback Trigger Baseline",
    "## Rollback Execution Contract",
    "## Protected Deployment Boundaries",
    "## Required Production Evidence",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "runtime_cutover_production_readiness_rollback_contract.py",
    ROOT / "app" / "runtime_cutover_ci_gate_baseline.py",
    ROOT / "app" / "durable_signaling_runtime_cutover_baseline.py",
    ROOT / "app" / "durable_signaling_dual_write_shadow_read_contract.py",
    ROOT / "tools" / "run_runtime_cutover_ci_simulation.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: runtime-cutover-ci",
    "runtime-cutover-mode-gate",
    "matrix:",
    "mode: [pubsub_legacy, dual_write_shadow, durable_authoritative]",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_23_6_PATH.exists():
        _fail(errors, f"Missing Step 23.6 baseline doc: {DOC_23_6_PATH}")
        return

    text = DOC_23_6_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_23_6_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 23.6 baseline doc: {phrase}")

    if not DOC_23_5_PATH.exists():
        _fail(errors, f"Missing Step 23.5 dependency doc: {DOC_23_5_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_23_5_PATH.exists():
        _fail(errors, f"Missing Step 23.5 workflow dependency: {WORKFLOW_23_5_PATH}")
        return

    text = WORKFLOW_23_5_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked production-readiness path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.runtime_cutover_production_readiness_rollback_contract import (
            validate_runtime_cutover_production_readiness_rollback_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 23.6 baseline module: {exc}")
        return

    errors.extend(validate_runtime_cutover_production_readiness_rollback_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("runtime-cutover-production-readiness-rollback-contract-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("runtime-cutover-production-readiness-rollback-contract-check: OK")
    print(f"- checked Step 23.6 doc: {DOC_23_6_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

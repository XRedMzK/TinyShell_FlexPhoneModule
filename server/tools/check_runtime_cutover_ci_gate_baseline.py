from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_23_5_PATH = ROOT.parent / "docs" / "step23-ci-runtime-cutover-mode-gate-baseline.md"
WORKFLOW_23_5_PATH = ROOT.parent / ".github" / "workflows" / "runtime-cutover-ci.yml"
DOC_23_4_PATH = ROOT.parent / "docs" / "step23-runtime-cutover-sandbox-smoke-baseline.md"

REQUIRED_DOC_23_5_PHRASES = (
    "## Goal",
    "## Scope",
    "## CI Topology",
    "## Gate Scenarios",
    "## Fail Conditions",
    "## Invariants",
    "## Workflow Baseline",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "tools" / "run_runtime_cutover_ci_simulation.py",
    ROOT / "tools" / "run_runtime_cutover_sandbox_smoke.py",
    ROOT / "tools" / "check_durable_signaling_runtime_path_inventory.py",
    ROOT / "tools" / "check_durable_signaling_dual_write_shadow_read_contract.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: runtime-cutover-ci",
    "runtime-cutover-mode-gate",
    "matrix:",
    "mode: [pubsub_legacy, dual_write_shadow, durable_authoritative]",
    "FLEXPHONE_CUTOVER_CI_MODE",
    "python tools/run_runtime_cutover_ci_simulation.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_23_5_PATH.exists():
        _fail(errors, f"Missing Step 23.5 baseline doc: {DOC_23_5_PATH}")
        return

    doc_text = DOC_23_5_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_23_5_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 23.5 baseline doc: {phrase}")

    if not DOC_23_4_PATH.exists():
        _fail(errors, f"Missing Step 23.4 dependency doc: {DOC_23_4_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_23_5_PATH.exists():
        _fail(errors, f"Missing Step 23.5 workflow: {WORKFLOW_23_5_PATH}")
        return

    workflow_text = WORKFLOW_23_5_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow_text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked CI gate path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.runtime_cutover_ci_gate_baseline import (
            validate_runtime_cutover_ci_gate_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 23.5 baseline module: {exc}")
        return

    errors.extend(validate_runtime_cutover_ci_gate_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("runtime-cutover-ci-gate-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("runtime-cutover-ci-gate-baseline-check: OK")
    print(f"- checked Step 23.5 doc: {DOC_23_5_PATH}")
    print(f"- checked Step 23.5 workflow: {WORKFLOW_23_5_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

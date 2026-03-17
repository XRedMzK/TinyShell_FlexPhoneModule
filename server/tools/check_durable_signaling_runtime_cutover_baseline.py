from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_23_1_PATH = ROOT.parent / "docs" / "step23-durable-signaling-runtime-cutover-baseline.md"
DOC_22_2_PATH = ROOT.parent / "docs" / "step22-signaling-event-inventory-baseline.md"
DOC_22_3_PATH = ROOT.parent / "docs" / "step22-signaling-durable-event-model-baseline.md"

REQUIRED_DOC_23_1_PHRASES = (
    "## Goal",
    "## Scope",
    "## Rollout Modes",
    "## Feature Flag and Runtime Switch Boundary",
    "## Event Migration Matrix Baseline",
    "## Rollback and Abort Boundaries",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "signaling.py",
    ROOT / "app" / "main.py",
    ROOT / "app" / "signaling_event_inventory_baseline.py",
    ROOT / "app" / "signaling_durable_event_model_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_23_1_PATH.exists():
        _fail(errors, f"Missing Step 23.1 baseline doc: {DOC_23_1_PATH}")
        return

    doc_text = DOC_23_1_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_23_1_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 23.1 baseline doc: {phrase}")

    if not DOC_22_2_PATH.exists():
        _fail(errors, f"Missing Step 22.2 dependency doc: {DOC_22_2_PATH}")
    if not DOC_22_3_PATH.exists():
        _fail(errors, f"Missing Step 22.3 dependency doc: {DOC_22_3_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked cutover baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.durable_signaling_runtime_cutover_baseline import (
            validate_durable_signaling_runtime_cutover_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 23.1 baseline module: {exc}")
        return

    errors.extend(validate_durable_signaling_runtime_cutover_baseline_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("durable-signaling-runtime-cutover-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("durable-signaling-runtime-cutover-baseline-check: OK")
    print(f"- checked Step 23.1 doc: {DOC_23_1_PATH}")
    print(f"- checked runtime cutover baseline module under: {ROOT / 'app'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

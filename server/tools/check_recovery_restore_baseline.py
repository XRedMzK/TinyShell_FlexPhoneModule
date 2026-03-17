from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_21_1_PATH = ROOT.parent / "docs" / "step21-recovery-restore-baseline.md"

REQUIRED_DOC_21_1_PHRASES = (
    "## Goal",
    "## Recovery Scope",
    "## Source-of-Truth Inventory Boundaries",
    "## Bounded-Loss Assumptions",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Stage 21 Substep Contract",
    "## Non-Goals",
    "## Build-Level Validation",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_21_1_PATH.exists():
        _fail(errors, f"Missing Step 21.1 baseline doc: {DOC_21_1_PATH}")
        return

    doc_text = DOC_21_1_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_21_1_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 21.1 baseline doc: {phrase}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.recovery_restore_baseline import validate_recovery_restore_baseline_contract
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 21.1 baseline module: {exc}")
        return

    errors.extend(validate_recovery_restore_baseline_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_mapping_contract(errors)

    if errors:
        print("recovery-restore-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("recovery-restore-baseline-check: OK")
    print(f"- checked Step 21.1 doc: {DOC_21_1_PATH}")
    print(f"- checked recovery baseline module under: {ROOT / 'app'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

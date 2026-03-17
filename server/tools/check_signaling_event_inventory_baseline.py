from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_22_2_PATH = ROOT.parent / "docs" / "step22-signaling-event-inventory-baseline.md"

REQUIRED_DOC_22_2_PHRASES = (
    "## Goal",
    "## Classification Principle",
    "## Inventory Classes",
    "## Classification Questions",
    "## Canonical Event Inventory",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "signaling.py",
    ROOT / "app" / "main.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_22_2_PATH.exists():
        _fail(errors, f"Missing Step 22.2 baseline doc: {DOC_22_2_PATH}")
        return

    doc_text = DOC_22_2_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_22_2_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 22.2 baseline doc: {phrase}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked signaling path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.signaling_event_inventory_baseline import (
            validate_signaling_event_inventory_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 22.2 baseline module: {exc}")
        return

    errors.extend(validate_signaling_event_inventory_baseline_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("signaling-event-inventory-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("signaling-event-inventory-baseline-check: OK")
    print(f"- checked Step 22.2 doc: {DOC_22_2_PATH}")
    print(f"- checked signaling inventory baseline module under: {ROOT / 'app'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

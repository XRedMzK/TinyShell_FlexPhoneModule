from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_25_2_PATH = ROOT.parent / "docs" / "step25-media-control-state-inventory-ownership-matrix-baseline.md"
DOC_25_1_PATH = ROOT.parent / "docs" / "step25-incall-media-control-quality-observability-baseline.md"

REQUIRED_DOC_25_2_PHRASES = (
    "## Goal",
    "## Scope",
    "## Canonical Control Surfaces",
    "## Desired vs Effective State Distinction",
    "## Operation Ownership Matrix",
    "## Allowed State Relations",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_incall_media_control_quality_observability_baseline.py",
    ROOT / "app" / "webrtc_media_control_state_inventory.py",
    ROOT / "tools" / "check_webrtc_incall_media_control_quality_observability_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_25_2_PATH.exists():
        _fail(errors, f"Missing Step 25.2 baseline doc: {DOC_25_2_PATH}")
        return

    text = DOC_25_2_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_25_2_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 25.2 baseline doc: {phrase}")

    if not DOC_25_1_PATH.exists():
        _fail(errors, f"Missing Step 25.1 dependency doc: {DOC_25_1_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 25.2 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_media_control_state_inventory import (
            validate_webrtc_media_control_state_inventory,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 25.2 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_media_control_state_inventory())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-media-control-state-inventory-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-media-control-state-inventory-check: OK")
    print(f"- checked Step 25.2 doc: {DOC_25_2_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

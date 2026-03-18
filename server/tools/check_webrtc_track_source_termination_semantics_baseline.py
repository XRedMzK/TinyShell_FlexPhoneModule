from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_26_3_PATH = ROOT.parent / "docs" / "step26-track-source-termination-semantics-baseline.md"
DOC_26_2_PATH = (
    ROOT.parent
    / "docs"
    / "step26-media-device-inventory-permission-gated-visibility-contract-baseline.md"
)

REQUIRED_DOC_26_3_PHRASES = (
    "## Goal",
    "## Scope",
    "## Authoritative Signal Model",
    "## Terminal Cause Matrix",
    "## Direct Stop vs Event-Driven Terminal Paths",
    "## Temporary Interruption Semantics",
    "## Deterministic Teardown and Reconciliation Actions",
    "## Capture-Side Scope Boundary",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_capture_source_device_permission_resilience_baseline.py",
    ROOT / "app" / "webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py",
    ROOT / "app" / "webrtc_track_source_termination_semantics_baseline.py",
    ROOT / "tools" / "check_webrtc_capture_source_device_permission_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_26_3_PATH.exists():
        _fail(errors, f"Missing Step 26.3 baseline doc: {DOC_26_3_PATH}")
        return

    text = DOC_26_3_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_26_3_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 26.3 baseline doc: {phrase}")

    if not DOC_26_2_PATH.exists():
        _fail(errors, f"Missing Step 26.2 dependency doc: {DOC_26_2_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 26.3 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_track_source_termination_semantics_baseline import (
            validate_webrtc_track_source_termination_semantics_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 26.3 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_track_source_termination_semantics_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-track-source-termination-semantics-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-track-source-termination-semantics-baseline-check: OK")
    print(f"- checked Step 26.3 doc: {DOC_26_3_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_26_5_PATH = ROOT.parent / "docs" / "step26-device-change-reconciliation-baseline.md"
DOC_26_4_PATH = (
    ROOT.parent
    / "docs"
    / "step26-screen-share-capture-lifecycle-source-reselection-contract-baseline.md"
)

REQUIRED_DOC_26_5_PHRASES = (
    "## Goal",
    "## Scope",
    "## Devicechange Advisory Trigger Model",
    "## Authoritative Reconciliation Surface",
    "## Capture-Side Slot Reconciliation Rules",
    "## Fallback Refresh Trigger Set",
    "## Display-Capture Exclusion from Device Reconciliation",
    "## Deterministic Reconciliation Flow",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_capture_source_device_permission_resilience_baseline.py",
    ROOT / "app" / "webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py",
    ROOT / "app" / "webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py",
    ROOT / "app" / "webrtc_device_change_reconciliation_baseline.py",
    ROOT / "tools" / "check_webrtc_capture_source_device_permission_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_26_5_PATH.exists():
        _fail(errors, f"Missing Step 26.5 baseline doc: {DOC_26_5_PATH}")
        return

    text = DOC_26_5_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_26_5_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 26.5 baseline doc: {phrase}")

    if not DOC_26_4_PATH.exists():
        _fail(errors, f"Missing Step 26.4 dependency doc: {DOC_26_4_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 26.5 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_device_change_reconciliation_baseline import (
            validate_webrtc_device_change_reconciliation_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 26.5 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_device_change_reconciliation_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-device-change-reconciliation-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-device-change-reconciliation-baseline-check: OK")
    print(f"- checked Step 26.5 doc: {DOC_26_5_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

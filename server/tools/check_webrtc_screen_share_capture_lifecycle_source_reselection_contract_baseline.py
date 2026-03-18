from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_26_4_PATH = (
    ROOT.parent
    / "docs"
    / "step26-screen-share-capture-lifecycle-source-reselection-contract-baseline.md"
)
DOC_26_3_PATH = ROOT.parent / "docs" / "step26-track-source-termination-semantics-baseline.md"

REQUIRED_DOC_26_4_PHRASES = (
    "## Goal",
    "## Scope",
    "## Authoritative Screen-Share Acquisition Surface",
    "## Non-Enumerable Display-Source Model",
    "## Source Selection and Reselection Semantics",
    "## Display Lifecycle Semantics",
    "## Direct Stop vs Event-Driven Terminal Paths",
    "## Sender Handoff Boundaries (`replaceTrack`)",
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
    ROOT / "app" / "webrtc_mute_unmute_source_switch_transceiver_direction_contract.py",
    ROOT / "app" / "webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_capture_source_device_permission_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_track_source_termination_semantics_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_26_4_PATH.exists():
        _fail(errors, f"Missing Step 26.4 baseline doc: {DOC_26_4_PATH}")
        return

    text = DOC_26_4_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_26_4_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 26.4 baseline doc: {phrase}")

    if not DOC_26_3_PATH.exists():
        _fail(errors, f"Missing Step 26.3 dependency doc: {DOC_26_3_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 26.4 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline import (
            validate_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 26.4 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-screen-share-capture-lifecycle-source-reselection-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-screen-share-capture-lifecycle-source-reselection-baseline-check: OK")
    print(f"- checked Step 26.4 doc: {DOC_26_4_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

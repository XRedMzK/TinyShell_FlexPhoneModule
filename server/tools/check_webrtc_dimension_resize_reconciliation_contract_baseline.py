from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_29_5_PATH = ROOT.parent / "docs" / "step29-dimension-resize-reconciliation-contract-baseline.md"
DOC_29_4_PATH = ROOT.parent / "docs" / "step29-waiting-stalled-resume-recovery-contract-baseline.md"

REQUIRED_DOC_29_5_PHRASES = (
    "## Goal",
    "## Scope",
    "## Intrinsic Dimension Truth Surfaces",
    "## Initial Dimension-Proof Semantics",
    "## Dimension Update Semantics",
    "## Intrinsic vs CSS/Layout Boundary",
    "## Failure/Recovery Non-Equivalence",
    "## Classification States",
    "## Scope Boundary",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py",
    ROOT / "app" / "webrtc_remote_video_first_frame_readiness_contract_baseline.py",
    ROOT / "app" / "webrtc_frame_progress_freeze_detection_observability_contract_baseline.py",
    ROOT / "app" / "webrtc_waiting_stalled_resume_recovery_contract_baseline.py",
    ROOT / "app" / "webrtc_dimension_resize_reconciliation_contract_baseline.py",
    ROOT / "app" / "webrtc_remote_track_attach_ownership_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_video_first_frame_readiness_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_frame_progress_freeze_detection_observability_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_waiting_stalled_resume_recovery_contract_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_29_5_PATH.exists():
        _fail(errors, f"Missing Step 29.5 baseline doc: {DOC_29_5_PATH}")
        return

    text = DOC_29_5_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_29_5_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 29.5 baseline doc: {phrase}")

    if not DOC_29_4_PATH.exists():
        _fail(errors, f"Missing Step 29.4 dependency doc: {DOC_29_4_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 29.5 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_dimension_resize_reconciliation_contract_baseline import (
            validate_webrtc_dimension_resize_reconciliation_contract_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 29.5 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_dimension_resize_reconciliation_contract_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-dimension-resize-reconciliation-contract-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-dimension-resize-reconciliation-contract-check: OK")
    print(f"- checked Step 29.5 doc: {DOC_29_5_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

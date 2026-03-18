from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_29_1_PATH = (
    ROOT.parent
    / "docs"
    / "step29-remote-video-first-frame-render-stall-dimension-change-resilience-baseline.md"
)
DOC_28_7_PATH = ROOT.parent / "docs" / "step28-remote-media-resilience-ci-gate-baseline.md"

REQUIRED_DOC_29_1_PHRASES = (
    "## Goal",
    "## Scope",
    "## Authoritative Remote Video Surfaces",
    "## First-Frame and Frame-Progress Truth Model",
    "## Waiting/Stalled Recovery Model",
    "## Dimension-Change Reconciliation Model",
    "## Scope Boundary",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Stage 29 Draft",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_remote_media_resilience_ci_gate_baseline.py",
    ROOT / "app" / "webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_media_resilience_ci_gate_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_29_1_PATH.exists():
        _fail(errors, f"Missing Step 29.1 baseline doc: {DOC_29_1_PATH}")
        return

    text = DOC_29_1_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_29_1_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 29.1 baseline doc: {phrase}")

    if not DOC_28_7_PATH.exists():
        _fail(errors, f"Missing Step 28.7 dependency doc: {DOC_28_7_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Stage 29 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline import (
            validate_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 29.1 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-remote-video-first-frame-render-stall-dimension-change-resilience-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-remote-video-first-frame-render-stall-dimension-change-resilience-baseline-check: OK")
    print(f"- checked Step 29.1 doc: {DOC_29_1_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

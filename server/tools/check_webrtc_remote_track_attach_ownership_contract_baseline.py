from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_28_2_PATH = ROOT.parent / "docs" / "step28-remote-track-attach-ownership-contract-baseline.md"
DOC_28_1_PATH = ROOT.parent / "docs" / "step28-remote-media-attach-autoplay-track-state-resilience-baseline.md"

REQUIRED_DOC_28_2_PHRASES = (
    "## Goal",
    "## Scope",
    "## Authoritative Ownership Model",
    "## ontrack Attach Contract",
    "## Attach Target and Binding State",
    "## Duplicate-Attach Guard",
    "## Stable Remount/Reattach Semantics",
    "## Scope Boundary",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py",
    ROOT / "app" / "webrtc_remote_track_attach_ownership_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_28_2_PATH.exists():
        _fail(errors, f"Missing Step 28.2 baseline doc: {DOC_28_2_PATH}")
        return

    text = DOC_28_2_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_28_2_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 28.2 baseline doc: {phrase}")

    if not DOC_28_1_PATH.exists():
        _fail(errors, f"Missing Step 28.1 dependency doc: {DOC_28_1_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Stage 28.2 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_remote_track_attach_ownership_contract_baseline import (
            validate_webrtc_remote_track_attach_ownership_contract_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 28.2 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_remote_track_attach_ownership_contract_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-remote-track-attach-ownership-contract-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-remote-track-attach-ownership-contract-baseline-check: OK")
    print(f"- checked Step 28.2 doc: {DOC_28_2_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

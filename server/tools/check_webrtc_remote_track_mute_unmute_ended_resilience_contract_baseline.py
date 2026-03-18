from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_28_4_PATH = (
    ROOT.parent / "docs" / "step28-remote-track-mute-unmute-ended-resilience-contract-baseline.md"
)
DOC_28_3_PATH = (
    ROOT.parent / "docs" / "step28-autoplay-play-promise-user-gesture-recovery-contract-baseline.md"
)

REQUIRED_DOC_28_4_PHRASES = (
    "## Goal",
    "## Scope",
    "## Lifecycle Model",
    "## Temporary vs Terminal Semantics",
    "## enabled vs muted Separation",
    "## Event-Driven Runtime Model",
    "## UI and Binding Boundaries",
    "## Scope Boundary",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py",
    ROOT / "app" / "webrtc_remote_track_attach_ownership_contract_baseline.py",
    ROOT / "app" / "webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline.py",
    ROOT / "app" / "webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_track_attach_ownership_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_28_4_PATH.exists():
        _fail(errors, f"Missing Step 28.4 baseline doc: {DOC_28_4_PATH}")
        return

    text = DOC_28_4_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_28_4_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 28.4 baseline doc: {phrase}")

    if not DOC_28_3_PATH.exists():
        _fail(errors, f"Missing Step 28.3 dependency doc: {DOC_28_3_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 28.4 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline import (
            validate_webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 28.4 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-remote-track-mute-unmute-ended-resilience-contract-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-remote-track-mute-unmute-ended-resilience-contract-check: OK")
    print(f"- checked Step 28.4 doc: {DOC_28_4_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

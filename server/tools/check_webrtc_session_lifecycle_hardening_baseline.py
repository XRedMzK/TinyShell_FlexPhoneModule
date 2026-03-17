from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_24_1_PATH = ROOT.parent / "docs" / "step24-webrtc-session-lifecycle-hardening-baseline.md"
DOC_23_6_PATH = ROOT.parent / "docs" / "step23-production-readiness-rollback-contract-baseline.md"

REQUIRED_DOC_24_1_PHRASES = (
    "## Goal",
    "## Scope",
    "## Ownership Boundaries",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Stage 24 Draft",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "signaling.py",
    ROOT / "app" / "main.py",
    ROOT / "app" / "webrtc_session_lifecycle_hardening_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_24_1_PATH.exists():
        _fail(errors, f"Missing Step 24.1 baseline doc: {DOC_24_1_PATH}")
        return

    text = DOC_24_1_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_24_1_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 24.1 baseline doc: {phrase}")

    if not DOC_23_6_PATH.exists():
        _fail(errors, f"Missing Step 23.6 dependency doc: {DOC_23_6_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked lifecycle baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_session_lifecycle_hardening_baseline import (
            validate_webrtc_session_lifecycle_hardening_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 24.1 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_session_lifecycle_hardening_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-session-lifecycle-hardening-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-session-lifecycle-hardening-baseline-check: OK")
    print(f"- checked Step 24.1 doc: {DOC_24_1_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

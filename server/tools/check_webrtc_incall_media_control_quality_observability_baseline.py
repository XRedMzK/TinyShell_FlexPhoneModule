from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_25_1_PATH = ROOT.parent / "docs" / "step25-incall-media-control-quality-observability-baseline.md"
DOC_24_6_PATH = ROOT.parent / "docs" / "step24-lifecycle-ci-gate-baseline.md"

REQUIRED_DOC_25_1_PHRASES = (
    "## Goal",
    "## Scope",
    "## Ownership Boundaries",
    "## Operation Matrix Baseline",
    "## Remote-Visible Semantics",
    "## Quality Observability Surface",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Stage 25 Draft",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_session_lifecycle_hardening_baseline.py",
    ROOT / "app" / "webrtc_incall_media_control_quality_observability_baseline.py",
    ROOT / "tools" / "check_webrtc_lifecycle_ci_gate_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_25_1_PATH.exists():
        _fail(errors, f"Missing Step 25.1 baseline doc: {DOC_25_1_PATH}")
        return

    text = DOC_25_1_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_25_1_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 25.1 baseline doc: {phrase}")

    if not DOC_24_6_PATH.exists():
        _fail(errors, f"Missing Stage 24 dependency doc: {DOC_24_6_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Stage 25 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_incall_media_control_quality_observability_baseline import (
            validate_webrtc_incall_media_control_quality_observability_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 25.1 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_incall_media_control_quality_observability_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-incall-media-control-quality-observability-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-incall-media-control-quality-observability-baseline-check: OK")
    print(f"- checked Step 25.1 doc: {DOC_25_1_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_21_3_PATH = ROOT.parent / "docs" / "step21-redis-recovery-semantics-baseline.md"

REQUIRED_DOC_21_3_PHRASES = (
    "## Goal",
    "## Redis State Classification",
    "## Recovery Event Baseline",
    "## Auth Challenge Recovery Semantics",
    "## Signaling Recovery Semantics",
    "## Startup Reconciliation Assumptions",
    "## Expected Convergence Path",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "auth_challenge_store.py",
    ROOT / "app" / "signaling.py",
    ROOT / "app" / "main.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_21_3_PATH.exists():
        _fail(errors, f"Missing Step 21.3 baseline doc: {DOC_21_3_PATH}")
        return

    doc_text = DOC_21_3_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_21_3_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 21.3 baseline doc: {phrase}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Redis semantics path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.recovery_restore_redis_semantics_baseline import (
            validate_recovery_restore_redis_semantics_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 21.3 baseline module: {exc}")
        return

    errors.extend(validate_recovery_restore_redis_semantics_baseline_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("recovery-restore-redis-semantics-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("recovery-restore-redis-semantics-check: OK")
    print(f"- checked Step 21.3 doc: {DOC_21_3_PATH}")
    print(f"- checked linked paths under: {ROOT / 'app'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

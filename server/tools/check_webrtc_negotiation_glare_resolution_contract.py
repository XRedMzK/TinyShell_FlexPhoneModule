from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_24_3_PATH = ROOT.parent / "docs" / "step24-negotiation-glare-resolution-contract-baseline.md"
DOC_24_2_PATH = ROOT.parent / "docs" / "step24-peer-session-state-inventory-transition-matrix-baseline.md"

REQUIRED_DOC_24_3_PHRASES = (
    "## Goal",
    "## Scope",
    "## Negotiation Roles",
    "## Negotiation Owner Rules",
    "## Offer-Collision Detection",
    "## `negotiationneeded` Handling",
    "## Signaling Preconditions for SDP API Calls",
    "## Rollback Policy",
    "## Deterministic Case Actions",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_session_lifecycle_hardening_baseline.py",
    ROOT / "app" / "webrtc_peer_session_state_inventory.py",
    ROOT / "app" / "webrtc_negotiation_glare_resolution_contract.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_24_3_PATH.exists():
        _fail(errors, f"Missing Step 24.3 baseline doc: {DOC_24_3_PATH}")
        return

    text = DOC_24_3_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_24_3_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 24.3 baseline doc: {phrase}")

    if not DOC_24_2_PATH.exists():
        _fail(errors, f"Missing Step 24.2 dependency doc: {DOC_24_2_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked negotiation baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_negotiation_glare_resolution_contract import (
            validate_webrtc_negotiation_glare_resolution_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 24.3 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_negotiation_glare_resolution_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-negotiation-glare-resolution-contract-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-negotiation-glare-resolution-contract-check: OK")
    print(f"- checked Step 24.3 doc: {DOC_24_3_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

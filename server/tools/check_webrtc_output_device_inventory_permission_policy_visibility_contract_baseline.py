from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_27_2_PATH = (
    ROOT.parent
    / "docs"
    / "step27-output-device-inventory-permission-policy-visibility-contract-baseline.md"
)
DOC_27_1_PATH = ROOT.parent / "docs" / "step27-audio-output-remote-playout-route-resilience-baseline.md"

REQUIRED_DOC_27_2_PHRASES = (
    "## Goal",
    "## Scope",
    "## Authoritative Inventory Surface",
    "## Permission and Policy Visibility Semantics",
    "## Default vs Non-Default Sink Semantics",
    "## Visibility Paths",
    "## Identity and Metadata Rules",
    "## Scope and Boundary",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_audio_output_remote_playout_route_resilience_baseline.py",
    ROOT / "app" / "webrtc_output_device_inventory_permission_policy_visibility_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_audio_output_remote_playout_route_resilience_baseline.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_27_2_PATH.exists():
        _fail(errors, f"Missing Step 27.2 baseline doc: {DOC_27_2_PATH}")
        return

    text = DOC_27_2_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_27_2_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 27.2 baseline doc: {phrase}")

    if not DOC_27_1_PATH.exists():
        _fail(errors, f"Missing Step 27.1 dependency doc: {DOC_27_1_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 27.2 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_output_device_inventory_permission_policy_visibility_contract_baseline import (
            validate_webrtc_output_device_inventory_permission_policy_visibility_contract_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 27.2 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_output_device_inventory_permission_policy_visibility_contract_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-output-device-inventory-permission-policy-visibility-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-output-device-inventory-permission-policy-visibility-check: OK")
    print(f"- checked Step 27.2 doc: {DOC_27_2_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

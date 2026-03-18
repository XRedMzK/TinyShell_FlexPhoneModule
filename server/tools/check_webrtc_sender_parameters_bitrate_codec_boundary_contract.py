from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_25_4_PATH = ROOT.parent / "docs" / "step25-sender-parameters-bitrate-codec-boundary-contract-baseline.md"
DOC_25_3_PATH = ROOT.parent / "docs" / "step25-mute-unmute-source-switch-transceiver-direction-contract-baseline.md"

REQUIRED_DOC_25_4_PHRASES = (
    "## Goal",
    "## Scope",
    "## Sender Control Surface Baseline",
    "## Allowed Runtime Update Classes",
    "## Bitrate and Encoding Ownership Boundaries",
    "## Codec and Negotiation Envelope Boundaries",
    "## Desired vs Effective Sender Parameters",
    "## Deterministic Case Actions",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_incall_media_control_quality_observability_baseline.py",
    ROOT / "app" / "webrtc_media_control_state_inventory.py",
    ROOT / "app" / "webrtc_mute_unmute_source_switch_transceiver_direction_contract.py",
    ROOT / "app" / "webrtc_sender_parameters_bitrate_codec_boundary_contract.py",
    ROOT / "tools" / "check_webrtc_mute_unmute_source_switch_transceiver_direction_contract.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_25_4_PATH.exists():
        _fail(errors, f"Missing Step 25.4 baseline doc: {DOC_25_4_PATH}")
        return

    text = DOC_25_4_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_25_4_PHRASES:
        if phrase not in text:
            _fail(errors, f"Missing phrase in Step 25.4 baseline doc: {phrase}")

    if not DOC_25_3_PATH.exists():
        _fail(errors, f"Missing Step 25.3 dependency doc: {DOC_25_3_PATH}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked Step 25.4 baseline path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_sender_parameters_bitrate_codec_boundary_contract import (
            validate_webrtc_sender_parameters_bitrate_codec_boundary_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 25.4 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_sender_parameters_bitrate_codec_boundary_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-sender-parameters-bitrate-codec-boundary-contract-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-sender-parameters-bitrate-codec-boundary-contract-check: OK")
    print(f"- checked Step 25.4 doc: {DOC_25_4_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

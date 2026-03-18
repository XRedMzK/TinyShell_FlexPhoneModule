from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_25_7_PATH = ROOT.parent / "docs" / "step25-incall-media-control-ci-gate-baseline.md"
WORKFLOW_25_7_PATH = ROOT.parent / ".github" / "workflows" / "webrtc-incall-media-control-ci.yml"
DOC_25_6_PATH = ROOT.parent / "docs" / "step25-incall-media-control-sandbox-smoke-baseline.md"

REQUIRED_DOC_25_7_PHRASES = (
    "## Goal",
    "## Scope",
    "## CI Topology",
    "## Scenario Matrix Source",
    "## Mandatory Assertions",
    "## Fail Conditions",
    "## Invariants",
    "## Workflow Baseline",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_incall_media_control_ci_gate_baseline.py",
    ROOT / "tools" / "run_webrtc_incall_media_control_sandbox_smoke.py",
    ROOT / "tools" / "run_webrtc_incall_media_control_ci_simulation.py",
    ROOT / "tools" / "check_webrtc_incall_media_control_quality_observability_baseline.py",
    ROOT / "tools" / "check_webrtc_media_control_state_inventory.py",
    ROOT / "tools" / "check_webrtc_mute_unmute_source_switch_transceiver_direction_contract.py",
    ROOT / "tools" / "check_webrtc_sender_parameters_bitrate_codec_boundary_contract.py",
    ROOT / "tools" / "check_webrtc_incall_quality_observability_baseline.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: webrtc-incall-media-control-ci",
    "webrtc-incall-media-control-gate",
    "python tools/check_webrtc_incall_media_control_quality_observability_baseline.py",
    "python tools/check_webrtc_media_control_state_inventory.py",
    "python tools/check_webrtc_mute_unmute_source_switch_transceiver_direction_contract.py",
    "python tools/check_webrtc_sender_parameters_bitrate_codec_boundary_contract.py",
    "python tools/check_webrtc_incall_quality_observability_baseline.py",
    "python tools/check_webrtc_incall_media_control_ci_gate_baseline.py",
    "python tools/run_webrtc_incall_media_control_ci_simulation.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_25_7_PATH.exists():
        _fail(errors, f"Missing Step 25.7 baseline doc: {DOC_25_7_PATH}")
        return

    doc_text = DOC_25_7_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_25_7_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 25.7 baseline doc: {phrase}")

    if not DOC_25_6_PATH.exists():
        _fail(errors, f"Missing Step 25.6 dependency doc: {DOC_25_6_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_25_7_PATH.exists():
        _fail(errors, f"Missing Step 25.7 workflow: {WORKFLOW_25_7_PATH}")
        return

    workflow_text = WORKFLOW_25_7_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow_text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked in-call media-control CI gate path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_incall_media_control_ci_gate_baseline import (
            validate_webrtc_incall_media_control_ci_gate_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 25.7 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_incall_media_control_ci_gate_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-incall-media-control-ci-gate-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-incall-media-control-ci-gate-baseline-check: OK")
    print(f"- checked Step 25.7 doc: {DOC_25_7_PATH}")
    print(f"- checked Step 25.7 workflow: {WORKFLOW_25_7_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_26_7_PATH = ROOT.parent / "docs" / "step26-capture-resilience-ci-gate-baseline.md"
WORKFLOW_26_7_PATH = ROOT.parent / ".github" / "workflows" / "webrtc-capture-resilience-ci.yml"
DOC_26_6_PATH = ROOT.parent / "docs" / "step26-capture-resilience-sandbox-smoke-baseline.md"

REQUIRED_DOC_26_7_PHRASES = (
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
    ROOT / "app" / "webrtc_capture_resilience_ci_gate_baseline.py",
    ROOT / "tools" / "run_webrtc_capture_resilience_sandbox_smoke.py",
    ROOT / "tools" / "run_webrtc_capture_resilience_ci_simulation.py",
    ROOT / "tools" / "check_webrtc_capture_source_device_permission_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_track_source_termination_semantics_baseline.py",
    ROOT / "tools" / "check_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_device_change_reconciliation_baseline.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: webrtc-capture-resilience-ci",
    "webrtc-capture-resilience-gate",
    "python tools/check_webrtc_capture_source_device_permission_resilience_baseline.py",
    "python tools/check_webrtc_media_device_inventory_permission_gated_visibility_contract_baseline.py",
    "python tools/check_webrtc_track_source_termination_semantics_baseline.py",
    "python tools/check_webrtc_screen_share_capture_lifecycle_source_reselection_contract_baseline.py",
    "python tools/check_webrtc_device_change_reconciliation_baseline.py",
    "python tools/check_webrtc_capture_resilience_ci_gate_baseline.py",
    "python tools/run_webrtc_capture_resilience_ci_simulation.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_26_7_PATH.exists():
        _fail(errors, f"Missing Step 26.7 baseline doc: {DOC_26_7_PATH}")
        return

    doc_text = DOC_26_7_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_26_7_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 26.7 baseline doc: {phrase}")

    if not DOC_26_6_PATH.exists():
        _fail(errors, f"Missing Step 26.6 dependency doc: {DOC_26_6_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_26_7_PATH.exists():
        _fail(errors, f"Missing Step 26.7 workflow: {WORKFLOW_26_7_PATH}")
        return

    workflow_text = WORKFLOW_26_7_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow_text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked capture resilience CI gate path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_capture_resilience_ci_gate_baseline import (
            validate_webrtc_capture_resilience_ci_gate_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 26.7 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_capture_resilience_ci_gate_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-capture-resilience-ci-gate-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-capture-resilience-ci-gate-baseline-check: OK")
    print(f"- checked Step 26.7 doc: {DOC_26_7_PATH}")
    print(f"- checked Step 26.7 workflow: {WORKFLOW_26_7_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

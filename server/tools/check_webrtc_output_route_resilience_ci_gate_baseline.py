from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_27_7_PATH = ROOT.parent / "docs" / "step27-output-route-resilience-ci-gate-baseline.md"
WORKFLOW_27_7_PATH = ROOT.parent / ".github" / "workflows" / "webrtc-output-route-resilience-ci.yml"
DOC_27_6_PATH = ROOT.parent / "docs" / "step27-output-route-resilience-sandbox-smoke-baseline.md"
EVIDENCE_27_6_PATH = ROOT.parent / "docs" / "evidence" / "step27-output-route-resilience-sandbox-smoke-evidence.json"

REQUIRED_DOC_27_7_PHRASES = (
    "## Goal",
    "## Scope",
    "## CI Contract vs Real Runtime",
    "## Dependency Closure",
    "## Manual Smoke Evidence Contract",
    "## Mandatory Transition Invariants",
    "## Outcome Model",
    "## Fail Conditions",
    "## Workflow Baseline",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "webrtc_output_route_resilience_ci_gate_baseline.py",
    ROOT / "tools" / "run_webrtc_output_route_resilience_sandbox_smoke.py",
    ROOT / "tools" / "run_webrtc_output_route_resilience_ci_gate.py",
    ROOT / "tools" / "check_webrtc_output_devicechange_reconciliation_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_output_device_loss_fallback_rebinding_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_sink_selection_apply_semantics_error_class_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_output_device_inventory_permission_policy_visibility_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_audio_output_remote_playout_route_resilience_baseline.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: webrtc-output-route-resilience-ci",
    "webrtc-output-route-resilience-gate",
    "python tools/check_webrtc_output_route_resilience_ci_gate_baseline.py",
    "python tools/run_webrtc_output_route_resilience_ci_gate.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_27_7_PATH.exists():
        _fail(errors, f"Missing Step 27.7 baseline doc: {DOC_27_7_PATH}")
        return

    doc_text = DOC_27_7_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_27_7_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 27.7 baseline doc: {phrase}")

    if not DOC_27_6_PATH.exists():
        _fail(errors, f"Missing Step 27.6 dependency doc: {DOC_27_6_PATH}")

    if not EVIDENCE_27_6_PATH.exists():
        _fail(errors, f"Missing Step 27.6 smoke evidence manifest: {EVIDENCE_27_6_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_27_7_PATH.exists():
        _fail(errors, f"Missing Step 27.7 workflow: {WORKFLOW_27_7_PATH}")
        return

    workflow_text = WORKFLOW_27_7_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow_text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked output-route CI gate path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_output_route_resilience_ci_gate_baseline import (
            validate_webrtc_output_route_resilience_ci_gate_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 27.7 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_output_route_resilience_ci_gate_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-output-route-resilience-ci-gate-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-output-route-resilience-ci-gate-baseline-check: OK")
    print(f"- checked Step 27.7 doc: {DOC_27_7_PATH}")
    print(f"- checked Step 27.7 workflow: {WORKFLOW_27_7_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

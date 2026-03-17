from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_24_6_PATH = ROOT.parent / "docs" / "step24-lifecycle-ci-gate-baseline.md"
WORKFLOW_24_6_PATH = ROOT.parent / ".github" / "workflows" / "webrtc-lifecycle-ci.yml"
DOC_24_5_PATH = ROOT.parent / "docs" / "step24-lifecycle-sandbox-smoke-baseline.md"

REQUIRED_DOC_24_6_PHRASES = (
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
    ROOT / "tools" / "run_webrtc_lifecycle_sandbox_smoke.py",
    ROOT / "tools" / "run_webrtc_lifecycle_ci_simulation.py",
    ROOT / "tools" / "check_webrtc_session_lifecycle_hardening_baseline.py",
    ROOT / "tools" / "check_webrtc_peer_session_state_inventory.py",
    ROOT / "tools" / "check_webrtc_negotiation_glare_resolution_contract.py",
    ROOT / "tools" / "check_webrtc_reconnect_ice_restart_pending_recovery_contract.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: webrtc-lifecycle-ci",
    "webrtc-lifecycle-gate",
    "matrix:",
    "scenario: [A_happy_path_lifecycle, B_glare_collision_roles, C_transient_disconnect_recovery, D_failed_ice_restart_recovery, E_late_signaling_ignored, F_close_during_pending_recovery]",
    "FLEXPHONE_WEBRTC_LIFECYCLE_CI_SCENARIO",
    "python tools/run_webrtc_lifecycle_ci_simulation.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_24_6_PATH.exists():
        _fail(errors, f"Missing Step 24.6 baseline doc: {DOC_24_6_PATH}")
        return

    doc_text = DOC_24_6_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_24_6_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 24.6 baseline doc: {phrase}")

    if not DOC_24_5_PATH.exists():
        _fail(errors, f"Missing Step 24.5 dependency doc: {DOC_24_5_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_24_6_PATH.exists():
        _fail(errors, f"Missing Step 24.6 workflow: {WORKFLOW_24_6_PATH}")
        return

    workflow_text = WORKFLOW_24_6_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow_text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked lifecycle CI gate path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_lifecycle_ci_gate_baseline import (
            validate_webrtc_lifecycle_ci_gate_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 24.6 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_lifecycle_ci_gate_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-lifecycle-ci-gate-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-lifecycle-ci-gate-baseline-check: OK")
    print(f"- checked Step 24.6 doc: {DOC_24_6_PATH}")
    print(f"- checked Step 24.6 workflow: {WORKFLOW_24_6_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

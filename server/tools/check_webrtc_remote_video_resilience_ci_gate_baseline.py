from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_29_7_PATH = ROOT.parent / "docs" / "step29-remote-video-resilience-ci-gate-baseline.md"
WORKFLOW_29_7_PATH = ROOT.parent / ".github" / "workflows" / "webrtc-remote-video-resilience-ci.yml"
DOC_29_6_PATH = ROOT.parent / "docs" / "step29-remote-video-resilience-sandbox-smoke-baseline.md"
EVIDENCE_29_6_PATH = (
    ROOT.parent / "docs" / "evidence" / "step29-remote-video-resilience-sandbox-smoke-evidence.json"
)

REQUIRED_DOC_29_7_PHRASES = (
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
    ROOT / "app" / "webrtc_remote_media_resilience_ci_gate_baseline.py",
    ROOT / "app" / "webrtc_remote_video_resilience_ci_gate_baseline.py",
    ROOT / "tools" / "run_webrtc_remote_video_resilience_sandbox_smoke.py",
    ROOT / "tools" / "run_webrtc_remote_video_resilience_ci_gate.py",
    ROOT / "tools" / "check_webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_video_first_frame_readiness_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_frame_progress_freeze_detection_observability_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_waiting_stalled_resume_recovery_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_dimension_resize_reconciliation_contract_baseline.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: webrtc-remote-video-resilience-ci",
    "webrtc-remote-video-resilience-gate",
    "python tools/check_webrtc_remote_video_resilience_ci_gate_baseline.py",
    "python tools/run_webrtc_remote_video_resilience_ci_gate.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_29_7_PATH.exists():
        _fail(errors, f"Missing Step 29.7 baseline doc: {DOC_29_7_PATH}")
        return

    doc_text = DOC_29_7_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_29_7_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 29.7 baseline doc: {phrase}")

    if not DOC_29_6_PATH.exists():
        _fail(errors, f"Missing Step 29.6 dependency doc: {DOC_29_6_PATH}")

    if not EVIDENCE_29_6_PATH.exists():
        _fail(errors, f"Missing Step 29.6 smoke evidence manifest: {EVIDENCE_29_6_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_29_7_PATH.exists():
        _fail(errors, f"Missing Step 29.7 workflow: {WORKFLOW_29_7_PATH}")
        return

    workflow_text = WORKFLOW_29_7_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow_text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked remote-video CI gate path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_remote_video_resilience_ci_gate_baseline import (
            validate_webrtc_remote_video_resilience_ci_gate_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 29.7 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_remote_video_resilience_ci_gate_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-remote-video-resilience-ci-gate-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-remote-video-resilience-ci-gate-baseline-check: OK")
    print(f"- checked Step 29.7 doc: {DOC_29_7_PATH}")
    print(f"- checked Step 29.7 workflow: {WORKFLOW_29_7_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

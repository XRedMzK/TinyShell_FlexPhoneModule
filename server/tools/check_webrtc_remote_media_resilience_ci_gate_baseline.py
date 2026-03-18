from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_28_7_PATH = ROOT.parent / "docs" / "step28-remote-media-resilience-ci-gate-baseline.md"
WORKFLOW_28_7_PATH = ROOT.parent / ".github" / "workflows" / "webrtc-remote-media-resilience-ci.yml"
DOC_28_6_PATH = ROOT.parent / "docs" / "step28-remote-media-resilience-sandbox-smoke-baseline.md"
EVIDENCE_28_6_PATH = (
    ROOT.parent / "docs" / "evidence" / "step28-remote-media-resilience-sandbox-smoke-evidence.json"
)

REQUIRED_DOC_28_7_PHRASES = (
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
    ROOT / "app" / "webrtc_remote_media_resilience_ci_gate_baseline.py",
    ROOT / "tools" / "run_webrtc_remote_media_resilience_sandbox_smoke.py",
    ROOT / "tools" / "run_webrtc_remote_media_resilience_ci_gate.py",
    ROOT / "tools" / "check_webrtc_remote_media_attach_autoplay_track_state_resilience_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_track_attach_ownership_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_autoplay_play_promise_user_gesture_recovery_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_remote_track_mute_unmute_ended_resilience_contract_baseline.py",
    ROOT / "tools" / "check_webrtc_media_element_remount_reattach_recovery_contract_baseline.py",
)

REQUIRED_WORKFLOW_SNIPPETS = (
    "name: webrtc-remote-media-resilience-ci",
    "webrtc-remote-media-resilience-gate",
    "python tools/check_webrtc_remote_media_resilience_ci_gate_baseline.py",
    "python tools/run_webrtc_remote_media_resilience_ci_gate.py",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_28_7_PATH.exists():
        _fail(errors, f"Missing Step 28.7 baseline doc: {DOC_28_7_PATH}")
        return

    doc_text = DOC_28_7_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_28_7_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 28.7 baseline doc: {phrase}")

    if not DOC_28_6_PATH.exists():
        _fail(errors, f"Missing Step 28.6 dependency doc: {DOC_28_6_PATH}")

    if not EVIDENCE_28_6_PATH.exists():
        _fail(errors, f"Missing Step 28.6 smoke evidence manifest: {EVIDENCE_28_6_PATH}")


def _check_workflow(errors: list[str]) -> None:
    if not WORKFLOW_28_7_PATH.exists():
        _fail(errors, f"Missing Step 28.7 workflow: {WORKFLOW_28_7_PATH}")
        return

    workflow_text = WORKFLOW_28_7_PATH.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow_text:
            _fail(errors, f"Missing workflow snippet: {snippet}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked remote-media CI gate path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.webrtc_remote_media_resilience_ci_gate_baseline import (
            validate_webrtc_remote_media_resilience_ci_gate_baseline,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 28.7 baseline module: {exc}")
        return

    errors.extend(validate_webrtc_remote_media_resilience_ci_gate_baseline())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_workflow(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("webrtc-remote-media-resilience-ci-gate-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("webrtc-remote-media-resilience-ci-gate-baseline-check: OK")
    print(f"- checked Step 28.7 doc: {DOC_28_7_PATH}")
    print(f"- checked Step 28.7 workflow: {WORKFLOW_28_7_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

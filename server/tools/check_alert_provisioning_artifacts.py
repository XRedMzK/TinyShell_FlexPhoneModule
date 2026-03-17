from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_20_1_PATH = ROOT.parent / "docs" / "step20-rendered-provisioning-artifacts-baseline.md"

REQUIRED_DOC_20_1_PHRASES = (
    "## Goal",
    "## Source of Truth and Rendered Layer",
    "## Rendered Artifact Set",
    "## Drift-Check Contract",
    "## Grafana Policy Tree Invariant",
    "## Alertmanager Linkage Invariants",
    "## Invariants",
    "## Build-Level Validation",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_20_1_PATH.exists():
        _fail(errors, f"Missing Step 20.1 baseline doc: {DOC_20_1_PATH}")
        return

    doc_text = DOC_20_1_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_20_1_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 20.1 baseline doc: {phrase}")


def _check_mapping_contracts(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.reliability_alert_policy_export_baseline import (
            validate_reliability_alert_policy_export_baseline_contract,
        )
        from app.reliability_alert_provisioning_artifacts_baseline import (
            RENDERED_PROVISIONING_ARTIFACT_ORDER,
            RENDERED_PROVISIONING_ARTIFACTS_BASELINE,
            validate_reliability_alert_provisioning_artifacts_baseline_contract,
        )
        from app.reliability_alert_provisioning_render import (
            render_reliability_alert_provisioning_artifacts,
            validate_reliability_alert_provisioning_render_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 20.1 baseline modules: {exc}")
        return

    errors.extend(validate_reliability_alert_policy_export_baseline_contract())
    errors.extend(validate_reliability_alert_provisioning_artifacts_baseline_contract())
    errors.extend(validate_reliability_alert_provisioning_render_contract())

    rendered_once = render_reliability_alert_provisioning_artifacts()
    rendered_twice = render_reliability_alert_provisioning_artifacts()
    if rendered_once != rendered_twice:
        _fail(errors, "Rendered artifacts are not deterministic for identical source mappings")

    expected_paths = {
        RENDERED_PROVISIONING_ARTIFACTS_BASELINE[artifact_id].relative_path
        for artifact_id in RENDERED_PROVISIONING_ARTIFACT_ORDER
    }
    if set(rendered_once.keys()) != expected_paths:
        _fail(errors, "Rendered artifact keys must match baseline artifact paths")

    for relative_path, rendered_payload in sorted(rendered_once.items()):
        file_path = ROOT / relative_path
        if not file_path.exists():
            _fail(errors, f"Missing rendered artifact file: {file_path}")
            continue

        committed_payload = file_path.read_text(encoding="utf-8")
        if committed_payload != rendered_payload:
            _fail(errors, f"Rendered artifact drift detected: {file_path}")
        if not committed_payload.endswith("\n"):
            _fail(errors, f"Rendered artifact must end with newline: {file_path}")


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_mapping_contracts(errors)

    if errors:
        print("alert-provisioning-artifacts-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("alert-provisioning-artifacts-check: OK")
    print(f"- checked Step 20.1 doc: {DOC_20_1_PATH}")
    print(f"- checked rendered artifacts under: {ROOT / 'generated'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

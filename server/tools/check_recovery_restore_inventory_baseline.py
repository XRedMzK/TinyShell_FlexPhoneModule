from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_21_2_PATH = ROOT.parent / "docs" / "step21-source-of-truth-backup-restore-inventory-baseline.md"

REQUIRED_DOC_21_2_PHRASES = (
    "## Goal",
    "## Inventory Classes",
    "## Restore Ownership Boundaries",
    "## Inventory Matrix Baseline",
    "## Normative Restore Statements",
    "## Invariants",
    "## Closure Criteria",
    "## Verification Type",
    "## Build-Level Validation",
)

REQUIRED_LINKED_PATHS = (
    ROOT / "app" / "reliability_alert_policy_export_baseline.py",
    ROOT / "app" / "reliability_alert_provisioning_artifacts_baseline.py",
    ROOT / "app" / "reliability_alert_provisioning_render.py",
    ROOT / "generated" / "alertmanager" / "alertmanager.rendered.yml",
    ROOT / "generated" / "grafana" / "provisioning" / "alerting" / "contact-points.rendered.yml",
    ROOT / "generated" / "grafana" / "provisioning" / "alerting" / "policies.rendered.yml",
    ROOT / "generated" / "grafana" / "provisioning" / "alerting" / "mute-timings.rendered.yml",
    ROOT / "generated" / "grafana" / "provisioning" / "alerting" / "templates.rendered.yml",
    ROOT / ".env.example",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _check_doc(errors: list[str]) -> None:
    if not DOC_21_2_PATH.exists():
        _fail(errors, f"Missing Step 21.2 baseline doc: {DOC_21_2_PATH}")
        return

    doc_text = DOC_21_2_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_DOC_21_2_PHRASES:
        if phrase not in doc_text:
            _fail(errors, f"Missing phrase in Step 21.2 baseline doc: {phrase}")


def _check_linked_paths(errors: list[str]) -> None:
    for path in REQUIRED_LINKED_PATHS:
        if not path.exists():
            _fail(errors, f"Missing linked recovery inventory path: {path}")


def _check_mapping_contract(errors: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from app.recovery_restore_inventory_baseline import (
            validate_recovery_restore_inventory_baseline_contract,
        )
    except Exception as exc:  # pragma: no cover - defensive import check
        _fail(errors, f"Failed to import Step 21.2 baseline module: {exc}")
        return

    errors.extend(validate_recovery_restore_inventory_baseline_contract())


def main() -> int:
    errors: list[str] = []
    _check_doc(errors)
    _check_linked_paths(errors)
    _check_mapping_contract(errors)

    if errors:
        print("recovery-restore-inventory-baseline-check: FAILED")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("recovery-restore-inventory-baseline-check: OK")
    print(f"- checked Step 21.2 doc: {DOC_21_2_PATH}")
    print(f"- checked linked paths under: {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

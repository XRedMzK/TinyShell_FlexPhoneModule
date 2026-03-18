from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from run_webrtc_output_route_resilience_sandbox_smoke import (
    OUTPUT_ROUTE_SMOKE_SCENARIO_IDS,
)

from app.webrtc_output_route_resilience_ci_gate_baseline import (
    CI_OUTPUT_ROUTE_EVIDENCE_SCHEMA_REQUIRED_FIELDS,
    CI_OUTPUT_ROUTE_OUTCOME_MODEL,
    CI_OUTPUT_ROUTE_REQUIRED_INVARIANTS,
)


EVIDENCE_PATH = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "step27-output-route-resilience-sandbox-smoke-evidence.json"
CI_SUCCESS_MARKER = "WebRTC output-route resilience CI gate: OK"
CI_UNSUPPORTED_MARKER = "WebRTC output-route resilience CI gate: UNSUPPORTED"


def _validate_manifest_structure(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("manifest.scenarios must be a list")
        return errors

    scenario_map: dict[str, dict[str, Any]] = {}
    for entry in scenarios:
        if not isinstance(entry, dict):
            errors.append("manifest.scenarios entries must be objects")
            continue

        for field in CI_OUTPUT_ROUTE_EVIDENCE_SCHEMA_REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"scenario entry missing required field: {field}")

        scenario_id = entry.get("scenario_id")
        if not isinstance(scenario_id, str):
            errors.append("scenario_id must be string")
            continue

        result = entry.get("result")
        if result not in CI_OUTPUT_ROUTE_OUTCOME_MODEL:
            errors.append(
                f"{scenario_id}: result must be one of {CI_OUTPUT_ROUTE_OUTCOME_MODEL}, got {result!r}"
            )

        proof_refs = entry.get("proof_refs")
        if not isinstance(proof_refs, list) or not proof_refs:
            errors.append(f"{scenario_id}: proof_refs must be non-empty list")

        verified = entry.get("verified_invariants")
        if not isinstance(verified, list):
            errors.append(f"{scenario_id}: verified_invariants must be list")

        scenario_map[scenario_id] = entry

    expected_ids = set(OUTPUT_ROUTE_SMOKE_SCENARIO_IDS)
    if set(scenario_map.keys()) != expected_ids:
        errors.append(f"scenario ID set mismatch, expected {sorted(expected_ids)}")

    for scenario_id, required_markers in CI_OUTPUT_ROUTE_REQUIRED_INVARIANTS.items():
        scenario = scenario_map.get(scenario_id)
        if scenario is None:
            continue
        verified = scenario.get("verified_invariants")
        if not isinstance(verified, list):
            continue
        for marker in required_markers:
            if marker not in verified:
                errors.append(f"{scenario_id}: missing invariant marker {marker!r}")

    return errors


def run_ci_gate() -> int:
    if not EVIDENCE_PATH.exists():
        print(f"WebRTC output-route resilience CI gate: FAIL - missing evidence manifest: {EVIDENCE_PATH}")
        return 1

    try:
        payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WebRTC output-route resilience CI gate: FAIL - invalid JSON evidence: {exc}")
        return 1

    if not isinstance(payload, dict):
        print("WebRTC output-route resilience CI gate: FAIL - evidence root must be object")
        return 1

    errors = _validate_manifest_structure(payload)
    if errors:
        print("WebRTC output-route resilience CI gate: FAIL")
        for issue in errors:
            print(f"- {issue}")
        return 1

    scenario_results = {s["scenario_id"]: s["result"] for s in payload["scenarios"]}
    has_fail = any(result == "FAIL" for result in scenario_results.values())
    has_unsupported = any(result == "UNSUPPORTED" for result in scenario_results.values())

    if has_fail:
        print("WebRTC output-route resilience CI gate: FAIL - smoke evidence contains FAIL scenario")
        return 1

    if has_unsupported:
        print(CI_UNSUPPORTED_MARKER)
        return 2

    print(CI_SUCCESS_MARKER)
    return 0


def main() -> int:
    try:
        return run_ci_gate()
    except Exception as exc:  # pragma: no cover - defensive harness
        print(f"WebRTC output-route resilience CI gate: FAIL (unexpected) - {exc!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

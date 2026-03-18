from __future__ import annotations


CI_OUTPUT_ROUTE_SCENARIO_IDS = (
    "A_non_default_apply_happy_path",
    "B_stale_sink_loss_fallback_default",
    "C_passive_rebind_after_return",
    "D_interactive_rebind_rotated_id",
    "E_explicit_reconcile_without_devicechange",
    "F_error_class_sanity",
)

CI_OUTPUT_ROUTE_DEPENDENCY_STEPS = (
    "26.7",
    "27.1",
    "27.2",
    "27.3",
    "27.4",
    "27.5",
    "27.6",
)

CI_OUTPUT_ROUTE_REQUIRED_INVARIANTS = {
    "A_non_default_apply_happy_path": (
        "non_default_apply_success",
        "preferred_equals_effective_non_default",
    ),
    "B_stale_sink_loss_fallback_default": (
        "stale_sink_detected",
        "fallback_to_default",
        "preferred_preserved",
    ),
    "C_passive_rebind_after_return": (
        "pending_rebind_detected",
        "passive_rebind_success",
    ),
    "D_interactive_rebind_rotated_id": (
        "persisted_id_revalidated",
        "rotated_id_applied",
    ),
    "E_explicit_reconcile_without_devicechange": (
        "explicit_reconcile_without_devicechange",
        "enumerate_snapshot_authoritative",
    ),
    "F_error_class_sanity": (
        "not_found_and_abort_not_success",
        "not_allowed_separate_permission_branch",
    ),
}

CI_OUTPUT_ROUTE_EVIDENCE_SCHEMA_REQUIRED_FIELDS = (
    "scenario_id",
    "executed_at",
    "runtime_class",
    "result",
    "proof_refs",
    "verified_invariants",
    "notes",
)

CI_OUTPUT_ROUTE_OUTCOME_MODEL = (
    "PASS",
    "FAIL",
    "UNSUPPORTED",
)

CI_OUTPUT_ROUTE_FAIL_CONDITIONS = (
    "dependency_checker_missing_or_failed",
    "baseline_artifact_missing",
    "smoke_evidence_manifest_missing",
    "required_scenario_missing",
    "required_invariant_marker_missing",
    "unsupported_treated_as_pass",
    "compile_or_import_failure",
)

CI_OUTPUT_ROUTE_INVARIANTS = {
    "ci_validates_contract_and_evidence_not_real_browser_routing": True,
    "devicechange_hint_enumerate_truth_enforced": True,
    "manual_smoke_evidence_required": True,
    "unsupported_is_explicit_non_pass_outcome": True,
    "fail_closed_behavior_required": True,
    "production_runtime_path_unchanged": True,
}

WORKFLOW_BASELINE_27_7 = {
    "workflow_path": ".github/workflows/webrtc-output-route-resilience-ci.yml",
    "job_name": "webrtc-output-route-resilience-gate",
    "runner_script": "server/tools/run_webrtc_output_route_resilience_ci_gate.py",
}


def validate_webrtc_output_route_resilience_ci_gate_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_audio_output_remote_playout_route_resilience_baseline import (
        OUTPUT_RECONCILIATION_MODEL,
        STAGE27_SUBSTEP_DRAFT,
        STAGE27_VERIFICATION_TYPES,
    )
    from app.webrtc_output_device_inventory_permission_policy_visibility_contract_baseline import (
        OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE,
    )
    from app.webrtc_sink_selection_apply_semantics_error_class_contract_baseline import (
        APPLY_ERROR_CLASS_MATRIX,
    )
    from app.webrtc_output_device_loss_fallback_rebinding_contract_baseline import (
        DETERMINISTIC_TRANSITION_RULES_27_4,
        OUTPUT_DEVICE_LOSS_REBIND_CONTRACT_INVARIANTS_27_4,
    )
    from app.webrtc_output_devicechange_reconciliation_contract_baseline import (
        OUTPUT_DEVICECHANGE_RECONCILE_INVARIANTS_27_5,
        OUTPUT_ORDER_SENSITIVE_DIFF_RULES_27_5,
    )
    from tools.run_webrtc_output_route_resilience_sandbox_smoke import (
        OUTPUT_ROUTE_SMOKE_SCENARIO_IDS,
    )

    required_steps = (
        "26.7",
        "27.1",
        "27.2",
        "27.3",
        "27.4",
        "27.5",
        "27.6",
    )
    if CI_OUTPUT_ROUTE_DEPENDENCY_STEPS != required_steps:
        errors.append("CI_OUTPUT_ROUTE_DEPENDENCY_STEPS must match mandatory dependency closure")

    if tuple(OUTPUT_ROUTE_SMOKE_SCENARIO_IDS) != CI_OUTPUT_ROUTE_SCENARIO_IDS:
        errors.append("CI_OUTPUT_ROUTE_SCENARIO_IDS must match 27.6 smoke scenario IDs")

    if set(CI_OUTPUT_ROUTE_REQUIRED_INVARIANTS.keys()) != set(CI_OUTPUT_ROUTE_SCENARIO_IDS):
        errors.append("CI_OUTPUT_ROUTE_REQUIRED_INVARIANTS must cover all required scenarios")

    required_fields = (
        "scenario_id",
        "executed_at",
        "runtime_class",
        "result",
        "proof_refs",
        "verified_invariants",
        "notes",
    )
    if CI_OUTPUT_ROUTE_EVIDENCE_SCHEMA_REQUIRED_FIELDS != required_fields:
        errors.append("CI_OUTPUT_ROUTE_EVIDENCE_SCHEMA_REQUIRED_FIELDS must match canonical schema")

    required_outcomes = (
        "PASS",
        "FAIL",
        "UNSUPPORTED",
    )
    if CI_OUTPUT_ROUTE_OUTCOME_MODEL != required_outcomes:
        errors.append("CI_OUTPUT_ROUTE_OUTCOME_MODEL must include PASS/FAIL/UNSUPPORTED")

    if len(CI_OUTPUT_ROUTE_FAIL_CONDITIONS) < 7:
        errors.append("CI_OUTPUT_ROUTE_FAIL_CONDITIONS must include full failure-class baseline")

    required_invariants = {
        "ci_validates_contract_and_evidence_not_real_browser_routing": True,
        "devicechange_hint_enumerate_truth_enforced": True,
        "manual_smoke_evidence_required": True,
        "unsupported_is_explicit_non_pass_outcome": True,
        "fail_closed_behavior_required": True,
        "production_runtime_path_unchanged": True,
    }
    if CI_OUTPUT_ROUTE_INVARIANTS != required_invariants:
        errors.append("CI_OUTPUT_ROUTE_INVARIANTS must match canonical invariant set")

    required_workflow = {
        "workflow_path": ".github/workflows/webrtc-output-route-resilience-ci.yml",
        "job_name": "webrtc-output-route-resilience-gate",
        "runner_script": "server/tools/run_webrtc_output_route_resilience_ci_gate.py",
    }
    if WORKFLOW_BASELINE_27_7 != required_workflow:
        errors.append("WORKFLOW_BASELINE_27_7 must match workflow baseline")

    if STAGE27_SUBSTEP_DRAFT.get("27.7") != "output_route_resilience_ci_gate_baseline":
        errors.append("Stage 27 draft must keep 27.7 CI gate milestone")

    if STAGE27_VERIFICATION_TYPES.get("27.7") != "build check":
        errors.append("Stage 27 verification map must keep 27.7 as build check")

    if OUTPUT_RECONCILIATION_MODEL.get("devicechange_required_for_correctness") is not False:
        errors.append("27.1 reconciliation model must keep devicechange non-required")

    if OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("27.2 inventory authority must keep enumerateDevices")

    required_apply_error_map = {
        "NotAllowedError": "apply_blocked_by_policy_or_permission",
        "NotFoundError": "sink_id_missing_or_stale",
        "AbortError": "sink_switch_failed_at_apply_stage",
    }
    if APPLY_ERROR_CLASS_MATRIX != required_apply_error_map:
        errors.append("27.3 apply error matrix must keep canonical error classes")

    if (
        DETERMINISTIC_TRANSITION_RULES_27_4.get("bound_plus_stale_detected")
        != "attempt_default_fallback_then_pending_rebind"
    ):
        errors.append("27.4 transitions must keep stale->fallback->pending_rebind path")

    if (
        OUTPUT_DEVICE_LOSS_REBIND_CONTRACT_INVARIANTS_27_4.get(
            "successful_fallback_sets_effective_default_and_preserves_preference"
        )
        is not True
    ):
        errors.append("27.4 invariants must keep fallback preference-preservation")

    if OUTPUT_ORDER_SENSITIVE_DIFF_RULES_27_5.get("snapshot_diff_is_order_sensitive") is not True:
        errors.append("27.5 must keep order-sensitive snapshot diff")

    if OUTPUT_DEVICECHANGE_RECONCILE_INVARIANTS_27_5.get("devicechange_hint_enumerate_truth") is not True:
        errors.append("27.5 invariants must keep devicechange-hint/enumerate-truth semantics")

    return errors

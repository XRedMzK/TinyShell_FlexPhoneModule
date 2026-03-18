from __future__ import annotations


OUTPUT_RECONCILE_REASON_ENUM_27_5 = (
    "devicechange_hint",
    "startup_bootstrap",
    "visibility_regain",
    "apply_failure_not_found",
    "apply_failure_abort",
    "post_select_success",
    "post_apply_success",
    "manual_reconcile",
)

OUTPUT_DEVICE_INVENTORY_SNAPSHOT_SCHEMA_27_5 = {
    "visible_audiooutput_devices": "ordered_list_of_visible_audiooutput_entries",
    "visible_audiooutput_ids_ordered": "ordered_list_of_sink_ids",
    "inventory_revision_hash": "deterministic_hash_of_ordered_snapshot",
    "default_route_revision": "deterministic_default_route_marker",
}

OUTPUT_RECONCILE_TRIGGER_MODEL_27_5 = {
    "devicechange_is_advisory_trigger": True,
    "enumerate_devices_snapshot_is_authoritative": True,
    "devicechange_delivery_required_for_correctness": False,
    "explicit_reconcile_without_devicechange_required": True,
    "event_payload_non_authoritative": True,
}

OUTPUT_ORDER_SENSITIVE_DIFF_RULES_27_5 = {
    "snapshot_diff_is_order_sensitive": True,
    "inventory_order_change_is_reconcile_relevant": True,
    "set_only_comparison_allowed": False,
}

OUTPUT_STALE_SINK_TRIGGER_BOUNDARIES_27_5 = {
    "preferred_non_default_missing_in_snapshot_is_stale": True,
    "effective_non_default_missing_in_snapshot_is_stale": True,
    "effective_default_empty_string_is_not_stale": True,
    "not_allowed_branch_not_stale_branch": True,
}

OUTPUT_DEFAULT_ROUTE_BRANCH_RULES_27_5 = {
    "effective_default_route_has_separate_branch": True,
    "default_route_change_without_stale_sink_supported": True,
    "default_route_change_triggers_fallback_branch": False,
}

OUTPUT_SINGLE_FLIGHT_RECONCILE_POLICY_27_5 = {
    "single_flight_required": True,
    "rerun_requested_flag_supported": True,
    "trigger_during_active_sets_rerun_only": True,
    "post_pass_single_rerun_if_requested": True,
    "process_event_as_delta_log": False,
}

OUTPUT_DETERMINISTIC_RECONCILE_FLOW_27_5 = {
    "acquire_fresh_snapshot_each_pass": True,
    "compute_inventory_changed": True,
    "compute_inventory_order_changed": True,
    "compute_preferred_stale": True,
    "compute_effective_stale": True,
    "compute_default_route_revision_changed": True,
    "effective_stale_routes_to_27_4_fallback": True,
    "pending_rebind_and_preferred_visible_routes_to_passive_rebind": True,
}

OUTPUT_DEVICECHANGE_RECONCILE_INVARIANTS_27_5 = {
    "devicechange_hint_enumerate_truth": True,
    "ordered_snapshot_model_required": True,
    "stale_and_default_route_branches_separate": True,
    "single_flight_reconcile_required": True,
    "event_payload_optional_non_authoritative": True,
    "production_runtime_change_allowed_in_27_5": False,
}

STAGE27_CLOSURE_CRITERIA_27_5 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "ordered_snapshot_trigger_and_single_flight_rules_defined",
    "stale_and_default_route_boundary_rules_explicit",
    "dependency_alignment_with_27_1_27_2_27_3_27_4_checker_enforced",
    "checker_and_compileall_pass",
)


def validate_webrtc_output_devicechange_reconciliation_contract_baseline() -> list[str]:
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
        OUTPUT_ROUTE_STATE_SCHEMA_27_4,
        STALE_SINK_DETECTION_RULES_27_4,
    )

    required_reason_enum = (
        "devicechange_hint",
        "startup_bootstrap",
        "visibility_regain",
        "apply_failure_not_found",
        "apply_failure_abort",
        "post_select_success",
        "post_apply_success",
        "manual_reconcile",
    )
    if OUTPUT_RECONCILE_REASON_ENUM_27_5 != required_reason_enum:
        errors.append("OUTPUT_RECONCILE_REASON_ENUM_27_5 must match canonical reconcile reasons")

    required_snapshot_schema = {
        "visible_audiooutput_devices": "ordered_list_of_visible_audiooutput_entries",
        "visible_audiooutput_ids_ordered": "ordered_list_of_sink_ids",
        "inventory_revision_hash": "deterministic_hash_of_ordered_snapshot",
        "default_route_revision": "deterministic_default_route_marker",
    }
    if OUTPUT_DEVICE_INVENTORY_SNAPSHOT_SCHEMA_27_5 != required_snapshot_schema:
        errors.append("OUTPUT_DEVICE_INVENTORY_SNAPSHOT_SCHEMA_27_5 must match canonical snapshot schema")

    required_trigger_model = {
        "devicechange_is_advisory_trigger": True,
        "enumerate_devices_snapshot_is_authoritative": True,
        "devicechange_delivery_required_for_correctness": False,
        "explicit_reconcile_without_devicechange_required": True,
        "event_payload_non_authoritative": True,
    }
    if OUTPUT_RECONCILE_TRIGGER_MODEL_27_5 != required_trigger_model:
        errors.append("OUTPUT_RECONCILE_TRIGGER_MODEL_27_5 must match canonical trigger model")

    required_order_diff_rules = {
        "snapshot_diff_is_order_sensitive": True,
        "inventory_order_change_is_reconcile_relevant": True,
        "set_only_comparison_allowed": False,
    }
    if OUTPUT_ORDER_SENSITIVE_DIFF_RULES_27_5 != required_order_diff_rules:
        errors.append("OUTPUT_ORDER_SENSITIVE_DIFF_RULES_27_5 must match canonical diff rules")

    required_stale_boundaries = {
        "preferred_non_default_missing_in_snapshot_is_stale": True,
        "effective_non_default_missing_in_snapshot_is_stale": True,
        "effective_default_empty_string_is_not_stale": True,
        "not_allowed_branch_not_stale_branch": True,
    }
    if OUTPUT_STALE_SINK_TRIGGER_BOUNDARIES_27_5 != required_stale_boundaries:
        errors.append(
            "OUTPUT_STALE_SINK_TRIGGER_BOUNDARIES_27_5 must match canonical stale trigger boundaries"
        )

    required_default_route_rules = {
        "effective_default_route_has_separate_branch": True,
        "default_route_change_without_stale_sink_supported": True,
        "default_route_change_triggers_fallback_branch": False,
    }
    if OUTPUT_DEFAULT_ROUTE_BRANCH_RULES_27_5 != required_default_route_rules:
        errors.append("OUTPUT_DEFAULT_ROUTE_BRANCH_RULES_27_5 must match default-route branch rules")

    required_single_flight = {
        "single_flight_required": True,
        "rerun_requested_flag_supported": True,
        "trigger_during_active_sets_rerun_only": True,
        "post_pass_single_rerun_if_requested": True,
        "process_event_as_delta_log": False,
    }
    if OUTPUT_SINGLE_FLIGHT_RECONCILE_POLICY_27_5 != required_single_flight:
        errors.append("OUTPUT_SINGLE_FLIGHT_RECONCILE_POLICY_27_5 must match single-flight policy")

    required_reconcile_flow = {
        "acquire_fresh_snapshot_each_pass": True,
        "compute_inventory_changed": True,
        "compute_inventory_order_changed": True,
        "compute_preferred_stale": True,
        "compute_effective_stale": True,
        "compute_default_route_revision_changed": True,
        "effective_stale_routes_to_27_4_fallback": True,
        "pending_rebind_and_preferred_visible_routes_to_passive_rebind": True,
    }
    if OUTPUT_DETERMINISTIC_RECONCILE_FLOW_27_5 != required_reconcile_flow:
        errors.append("OUTPUT_DETERMINISTIC_RECONCILE_FLOW_27_5 must match canonical reconcile flow")

    required_invariants = {
        "devicechange_hint_enumerate_truth": True,
        "ordered_snapshot_model_required": True,
        "stale_and_default_route_branches_separate": True,
        "single_flight_reconcile_required": True,
        "event_payload_optional_non_authoritative": True,
        "production_runtime_change_allowed_in_27_5": False,
    }
    if OUTPUT_DEVICECHANGE_RECONCILE_INVARIANTS_27_5 != required_invariants:
        errors.append(
            "OUTPUT_DEVICECHANGE_RECONCILE_INVARIANTS_27_5 must match canonical invariant set"
        )

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "ordered_snapshot_trigger_and_single_flight_rules_defined",
        "stale_and_default_route_boundary_rules_explicit",
        "dependency_alignment_with_27_1_27_2_27_3_27_4_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE27_CLOSURE_CRITERIA_27_5 != required_closure:
        errors.append("STAGE27_CLOSURE_CRITERIA_27_5 must match closure criteria")

    if STAGE27_SUBSTEP_DRAFT.get("27.5") != "output_devicechange_reconciliation_contract":
        errors.append("Stage 27 draft must define 27.5 output-devicechange reconciliation milestone")

    if STAGE27_VERIFICATION_TYPES.get("27.5") != "build check":
        errors.append("Stage 27 verification map must keep 27.5 as build check")

    if OUTPUT_RECONCILIATION_MODEL.get("authoritative_reconcile_source") != "fresh_enumerate_devices_snapshot":
        errors.append("27.1 reconcile model must keep fresh enumerate snapshot authoritative")

    if OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE.get("inventory_api") != "MediaDevices.enumerateDevices":
        errors.append("27.2 inventory model must keep enumerateDevices authoritative")

    required_apply_errors_27_3 = {
        "NotAllowedError": "apply_blocked_by_policy_or_permission",
        "NotFoundError": "sink_id_missing_or_stale",
        "AbortError": "sink_switch_failed_at_apply_stage",
    }
    if APPLY_ERROR_CLASS_MATRIX != required_apply_errors_27_3:
        errors.append("27.3 apply error matrix must keep canonical error mapping")

    if OUTPUT_ROUTE_STATE_SCHEMA_27_4.get("effective_sink_id") != "str_empty_string_means_default":
        errors.append("27.4 state schema must keep effective_sink_id default-empty-string semantics")

    if STALE_SINK_DETECTION_RULES_27_4.get("authoritative_detection_surface") != "fresh_enumerate_devices_snapshot":
        errors.append("27.4 stale detection must use fresh enumerate snapshot")

    if (
        DETERMINISTIC_TRANSITION_RULES_27_4.get("bound_plus_stale_detected")
        != "attempt_default_fallback_then_pending_rebind"
    ):
        errors.append("27.4 transition rules must keep stale->fallback->pending_rebind path")

    return errors

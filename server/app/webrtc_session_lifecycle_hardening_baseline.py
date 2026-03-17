from __future__ import annotations


STAGE24_NAME = "WebRTC Session Lifecycle Hardening Baseline"

STAGE24_SCOPE = (
    "peer_connection_state_machine_contract",
    "negotiation_and_glare_resolution_contract",
    "reconnect_and_ice_restart_recovery_contract",
    "session_cleanup_and_termination_contract",
    "lifecycle_sandbox_smoke_and_ci_gate_scope",
)

SIGNALING_MEDIA_OWNERSHIP_BOUNDARIES = {
    "signaling_layer_ownership": (
        "authoritative_signaling_event_delivery",
        "session_metadata_exchange",
        "reconnect_reconciliation_input",
    ),
    "lifecycle_layer_ownership": (
        "peer_connection_state_transitions",
        "negotiation_owner_selection",
        "ice_restart_policy_and_triggers",
        "session_stale_cleanup_policy",
    ),
    "media_layer_ownership": (
        "rtp_media_flow",
        "track_level_runtime_state",
        "transport_quality_observation",
    ),
    "ownership_overlap_forbidden": True,
}

STAGE24_INVARIANTS = {
    "single_active_negotiation_owner_per_session": True,
    "deterministic_glare_resolution_required": True,
    "explicit_policy_for_disconnected_failed_closed": True,
    "ice_restart_trigger_policy_explicit": True,
    "no_zombie_sessions_after_reconnect_or_abandon": True,
    "failed_recovery_has_clean_terminate_fallback": True,
    "lifecycle_correctness_not_dependent_on_pubsub_delivery": True,
    "production_runtime_change_allowed_in_24_1": False,
}

STAGE24_CLOSURE_CRITERIA_24_1 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "scope_invariants_boundaries_defined",
    "closure_criteria_and_verification_types_defined",
    "checker_and_compileall_pass",
)

STAGE24_VERIFICATION_TYPES = {
    "24.1": "build check",
    "24.2": "build check",
    "24.3": "build check",
    "24.4": "build check",
    "24.5": "manual runtime check",
    "24.6": "build check",
}

STAGE24_SUBSTEP_DRAFT = {
    "24.1": "session_lifecycle_hardening_baseline_definition",
    "24.2": "peer_session_state_inventory_and_transition_matrix",
    "24.3": "negotiation_and_glare_resolution_contract",
    "24.4": "reconnect_ice_restart_and_pending_recovery_contract",
    "24.5": "lifecycle_sandbox_smoke_baseline",
    "24.6": "lifecycle_ci_gate_baseline",
}


def validate_webrtc_session_lifecycle_hardening_baseline() -> list[str]:
    errors: list[str] = []

    if STAGE24_NAME != "WebRTC Session Lifecycle Hardening Baseline":
        errors.append("STAGE24_NAME must match canonical stage name")

    required_scope = (
        "peer_connection_state_machine_contract",
        "negotiation_and_glare_resolution_contract",
        "reconnect_and_ice_restart_recovery_contract",
        "session_cleanup_and_termination_contract",
        "lifecycle_sandbox_smoke_and_ci_gate_scope",
    )
    if STAGE24_SCOPE != required_scope:
        errors.append("STAGE24_SCOPE must match canonical lifecycle hardening scope")

    required_boundaries = {
        "signaling_layer_ownership": (
            "authoritative_signaling_event_delivery",
            "session_metadata_exchange",
            "reconnect_reconciliation_input",
        ),
        "lifecycle_layer_ownership": (
            "peer_connection_state_transitions",
            "negotiation_owner_selection",
            "ice_restart_policy_and_triggers",
            "session_stale_cleanup_policy",
        ),
        "media_layer_ownership": (
            "rtp_media_flow",
            "track_level_runtime_state",
            "transport_quality_observation",
        ),
        "ownership_overlap_forbidden": True,
    }
    if SIGNALING_MEDIA_OWNERSHIP_BOUNDARIES != required_boundaries:
        errors.append("SIGNALING_MEDIA_OWNERSHIP_BOUNDARIES must match canonical ownership boundaries")

    required_invariants = {
        "single_active_negotiation_owner_per_session": True,
        "deterministic_glare_resolution_required": True,
        "explicit_policy_for_disconnected_failed_closed": True,
        "ice_restart_trigger_policy_explicit": True,
        "no_zombie_sessions_after_reconnect_or_abandon": True,
        "failed_recovery_has_clean_terminate_fallback": True,
        "lifecycle_correctness_not_dependent_on_pubsub_delivery": True,
        "production_runtime_change_allowed_in_24_1": False,
    }
    if STAGE24_INVARIANTS != required_invariants:
        errors.append("STAGE24_INVARIANTS must match canonical lifecycle invariants")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "scope_invariants_boundaries_defined",
        "closure_criteria_and_verification_types_defined",
        "checker_and_compileall_pass",
    )
    if STAGE24_CLOSURE_CRITERIA_24_1 != required_closure:
        errors.append("STAGE24_CLOSURE_CRITERIA_24_1 must match baseline closure criteria")

    required_verification_types = {
        "24.1": "build check",
        "24.2": "build check",
        "24.3": "build check",
        "24.4": "build check",
        "24.5": "manual runtime check",
        "24.6": "build check",
    }
    if STAGE24_VERIFICATION_TYPES != required_verification_types:
        errors.append("STAGE24_VERIFICATION_TYPES must match baseline verification map")

    required_substeps = {
        "24.1": "session_lifecycle_hardening_baseline_definition",
        "24.2": "peer_session_state_inventory_and_transition_matrix",
        "24.3": "negotiation_and_glare_resolution_contract",
        "24.4": "reconnect_ice_restart_and_pending_recovery_contract",
        "24.5": "lifecycle_sandbox_smoke_baseline",
        "24.6": "lifecycle_ci_gate_baseline",
    }
    if STAGE24_SUBSTEP_DRAFT != required_substeps:
        errors.append("STAGE24_SUBSTEP_DRAFT must match baseline stage draft")

    return errors

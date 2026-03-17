from __future__ import annotations


STAGE25_NAME = "In-Call Media Control and Quality Observability Baseline"

STAGE25_SCOPE = (
    "media_control_ownership_contract",
    "renegotiation_vs_non_renegotiation_operation_matrix",
    "remote_visible_media_semantics_contract",
    "sender_parameters_and_encoding_boundaries",
    "quality_observability_metric_surface",
    "sandbox_smoke_and_ci_gate_scope",
)

MEDIA_CONTROL_OWNERSHIP_BOUNDARIES = {
    "ui_control_owner": (
        "mute_unmute_intent",
        "camera_toggle_intent",
        "source_switch_intent",
    ),
    "lifecycle_owner": (
        "operation_admissibility_against_peer_state",
        "renegotiation_decision_boundary",
        "terminal_session_control_rejection",
    ),
    "media_runtime_owner": (
        "track_enabled_state",
        "sender_track_binding",
        "transceiver_direction_state",
        "sender_parameters_application",
    ),
    "observability_owner": (
        "getstats_sampling",
        "quality_metric_projection",
        "quality_severity_classification",
    ),
    "ownership_overlap_forbidden": True,
}

MEDIA_CONTROL_OPERATION_MATRIX = {
    "mic_mute_unmute": {
        "canonical_api": "MediaStreamTrack.enabled",
        "requires_renegotiation": False,
        "allowed_in_terminal_session": False,
    },
    "camera_mute_unmute": {
        "canonical_api": "MediaStreamTrack.enabled",
        "requires_renegotiation": False,
        "allowed_in_terminal_session": False,
    },
    "source_switch_same_kind": {
        "canonical_api": "RTCRtpSender.replaceTrack",
        "requires_renegotiation": False,
        "allowed_in_terminal_session": False,
    },
    "transceiver_direction_change": {
        "canonical_api": "RTCRtpTransceiver.direction",
        "requires_renegotiation": True,
        "allowed_in_terminal_session": False,
    },
    "sender_encoding_update": {
        "canonical_api": "RTCRtpSender.setParameters",
        "requires_renegotiation": False,
        "allowed_in_terminal_session": False,
    },
}

REMOTE_VISIBLE_MEDIA_SEMANTICS = {
    "track_enabled_false_means_intentional_mute": True,
    "track_muted_state_distinct_from_enabled_state": True,
    "remote_visibility_source_of_truth_is_sender_and_transceiver_state": True,
    "terminal_session_rejects_late_media_control_signals": True,
}

QUALITY_OBSERVABILITY_SURFACE = {
    "stats_source": "RTCPeerConnection.getStats",
    "required_metrics": (
        "candidate_pair.currentRoundTripTime",
        "candidate_pair.availableOutgoingBitrate",
        "candidate_pair.availableIncomingBitrate",
        "outbound_rtp.packetsSent",
        "outbound_rtp.bytesSent",
        "outbound_rtp.framesEncoded",
        "inbound_rtp.packetsLost",
        "inbound_rtp.jitter",
        "inbound_rtp.bytesReceived",
    ),
    "required_stat_types": (
        "candidate-pair",
        "outbound-rtp",
        "inbound-rtp",
    ),
}

STAGE25_INVARIANTS = {
    "media_control_operation_has_single_canonical_owner": True,
    "renegotiation_requirement_is_explicit_per_operation": True,
    "mute_switch_updates_do_not_require_ad_hoc_signaling_paths": True,
    "terminal_session_rejects_media_control_mutation": True,
    "quality_metrics_must_be_observable_from_getstats_surface": True,
    "production_runtime_change_allowed_in_25_1": False,
}

STAGE25_CLOSURE_CRITERIA_25_1 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "scope_invariants_boundaries_defined",
    "closure_criteria_and_verification_types_defined",
    "checker_and_compileall_pass",
)

STAGE25_VERIFICATION_TYPES = {
    "25.1": "build check",
    "25.2": "build check",
    "25.3": "build check",
    "25.4": "build check",
    "25.5": "build check",
    "25.6": "manual runtime check",
    "25.7": "build check",
}

STAGE25_SUBSTEP_DRAFT = {
    "25.1": "incall_media_control_and_quality_observability_baseline_definition",
    "25.2": "media_control_state_inventory_and_ownership_matrix",
    "25.3": "mute_unmute_source_switch_and_transceiver_direction_contract",
    "25.4": "sender_parameters_bitrate_and_codec_boundary_contract",
    "25.5": "incall_quality_observability_baseline",
    "25.6": "incall_media_control_sandbox_smoke_baseline",
    "25.7": "incall_media_control_ci_gate_baseline",
}


def validate_webrtc_incall_media_control_quality_observability_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_session_lifecycle_hardening_baseline import (
        STAGE24_SUBSTEP_DRAFT,
        STAGE24_VERIFICATION_TYPES,
    )

    if STAGE25_NAME != "In-Call Media Control and Quality Observability Baseline":
        errors.append("STAGE25_NAME must match canonical stage name")

    required_scope = (
        "media_control_ownership_contract",
        "renegotiation_vs_non_renegotiation_operation_matrix",
        "remote_visible_media_semantics_contract",
        "sender_parameters_and_encoding_boundaries",
        "quality_observability_metric_surface",
        "sandbox_smoke_and_ci_gate_scope",
    )
    if STAGE25_SCOPE != required_scope:
        errors.append("STAGE25_SCOPE must match canonical baseline scope")

    required_ownership = {
        "ui_control_owner": (
            "mute_unmute_intent",
            "camera_toggle_intent",
            "source_switch_intent",
        ),
        "lifecycle_owner": (
            "operation_admissibility_against_peer_state",
            "renegotiation_decision_boundary",
            "terminal_session_control_rejection",
        ),
        "media_runtime_owner": (
            "track_enabled_state",
            "sender_track_binding",
            "transceiver_direction_state",
            "sender_parameters_application",
        ),
        "observability_owner": (
            "getstats_sampling",
            "quality_metric_projection",
            "quality_severity_classification",
        ),
        "ownership_overlap_forbidden": True,
    }
    if MEDIA_CONTROL_OWNERSHIP_BOUNDARIES != required_ownership:
        errors.append("MEDIA_CONTROL_OWNERSHIP_BOUNDARIES must match canonical ownership boundaries")

    required_operations = {
        "mic_mute_unmute",
        "camera_mute_unmute",
        "source_switch_same_kind",
        "transceiver_direction_change",
        "sender_encoding_update",
    }
    if set(MEDIA_CONTROL_OPERATION_MATRIX.keys()) != required_operations:
        errors.append("MEDIA_CONTROL_OPERATION_MATRIX must define canonical operation set")

    for operation_name, operation_spec in MEDIA_CONTROL_OPERATION_MATRIX.items():
        if "canonical_api" not in operation_spec:
            errors.append(f"{operation_name}: canonical_api is required")
        if "requires_renegotiation" not in operation_spec:
            errors.append(f"{operation_name}: requires_renegotiation is required")
        if "allowed_in_terminal_session" not in operation_spec:
            errors.append(f"{operation_name}: allowed_in_terminal_session is required")
        if operation_spec.get("allowed_in_terminal_session") is not False:
            errors.append(f"{operation_name}: terminal session mutation must remain disallowed")

    if MEDIA_CONTROL_OPERATION_MATRIX["mic_mute_unmute"]["requires_renegotiation"] is not False:
        errors.append("mic_mute_unmute must not require renegotiation")
    if MEDIA_CONTROL_OPERATION_MATRIX["camera_mute_unmute"]["requires_renegotiation"] is not False:
        errors.append("camera_mute_unmute must not require renegotiation")
    if MEDIA_CONTROL_OPERATION_MATRIX["source_switch_same_kind"]["requires_renegotiation"] is not False:
        errors.append("source_switch_same_kind must not require renegotiation")
    if MEDIA_CONTROL_OPERATION_MATRIX["transceiver_direction_change"]["requires_renegotiation"] is not True:
        errors.append("transceiver_direction_change must require renegotiation")

    required_remote_semantics = {
        "track_enabled_false_means_intentional_mute": True,
        "track_muted_state_distinct_from_enabled_state": True,
        "remote_visibility_source_of_truth_is_sender_and_transceiver_state": True,
        "terminal_session_rejects_late_media_control_signals": True,
    }
    if REMOTE_VISIBLE_MEDIA_SEMANTICS != required_remote_semantics:
        errors.append("REMOTE_VISIBLE_MEDIA_SEMANTICS must match canonical media semantics baseline")

    required_quality_surface = {
        "stats_source": "RTCPeerConnection.getStats",
        "required_metrics": (
            "candidate_pair.currentRoundTripTime",
            "candidate_pair.availableOutgoingBitrate",
            "candidate_pair.availableIncomingBitrate",
            "outbound_rtp.packetsSent",
            "outbound_rtp.bytesSent",
            "outbound_rtp.framesEncoded",
            "inbound_rtp.packetsLost",
            "inbound_rtp.jitter",
            "inbound_rtp.bytesReceived",
        ),
        "required_stat_types": (
            "candidate-pair",
            "outbound-rtp",
            "inbound-rtp",
        ),
    }
    if QUALITY_OBSERVABILITY_SURFACE != required_quality_surface:
        errors.append("QUALITY_OBSERVABILITY_SURFACE must match canonical quality metric surface")

    required_invariants = {
        "media_control_operation_has_single_canonical_owner": True,
        "renegotiation_requirement_is_explicit_per_operation": True,
        "mute_switch_updates_do_not_require_ad_hoc_signaling_paths": True,
        "terminal_session_rejects_media_control_mutation": True,
        "quality_metrics_must_be_observable_from_getstats_surface": True,
        "production_runtime_change_allowed_in_25_1": False,
    }
    if STAGE25_INVARIANTS != required_invariants:
        errors.append("STAGE25_INVARIANTS must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "scope_invariants_boundaries_defined",
        "closure_criteria_and_verification_types_defined",
        "checker_and_compileall_pass",
    )
    if STAGE25_CLOSURE_CRITERIA_25_1 != required_closure:
        errors.append("STAGE25_CLOSURE_CRITERIA_25_1 must match baseline closure criteria")

    required_verification_types = {
        "25.1": "build check",
        "25.2": "build check",
        "25.3": "build check",
        "25.4": "build check",
        "25.5": "build check",
        "25.6": "manual runtime check",
        "25.7": "build check",
    }
    if STAGE25_VERIFICATION_TYPES != required_verification_types:
        errors.append("STAGE25_VERIFICATION_TYPES must match baseline verification map")

    required_substeps = {
        "25.1": "incall_media_control_and_quality_observability_baseline_definition",
        "25.2": "media_control_state_inventory_and_ownership_matrix",
        "25.3": "mute_unmute_source_switch_and_transceiver_direction_contract",
        "25.4": "sender_parameters_bitrate_and_codec_boundary_contract",
        "25.5": "incall_quality_observability_baseline",
        "25.6": "incall_media_control_sandbox_smoke_baseline",
        "25.7": "incall_media_control_ci_gate_baseline",
    }
    if STAGE25_SUBSTEP_DRAFT != required_substeps:
        errors.append("STAGE25_SUBSTEP_DRAFT must match baseline stage draft")

    if STAGE24_SUBSTEP_DRAFT.get("24.6") != "lifecycle_ci_gate_baseline":
        errors.append("Stage 24 dependency must keep lifecycle_ci_gate_baseline as 24.6")
    if STAGE24_VERIFICATION_TYPES.get("24.6") != "build check":
        errors.append("Stage 24 dependency must keep build check verification for 24.6")

    return errors

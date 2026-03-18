from __future__ import annotations


SENDER_PARAMETER_CONTROL_SURFACE_BASELINE = {
    "operation_scope": ("sender_encoding_update",),
    "authoritative_api_read": "RTCRtpSender.getParameters",
    "authoritative_api_write": "RTCRtpSender.setParameters",
    "authoritative_owner": "media_runtime_owner",
    "terminal_session_mutation_allowed": False,
}

ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES = {
    "bitrate_tuning": {
        "parameter_path": "encodings[].maxBitrate",
        "default_renegotiation_required": False,
        "requires_envelope_validation": True,
    },
    "encoding_activation_toggle": {
        "parameter_path": "encodings[].active",
        "default_renegotiation_required": False,
        "requires_envelope_validation": True,
    },
    "degradation_preference_update": {
        "parameter_path": "degradationPreference",
        "default_renegotiation_required": False,
        "requires_envelope_validation": True,
    },
}

BITRATE_ENCODING_OWNERSHIP_BOUNDARIES = {
    "sender_parameters_authoritative_for_bitrate_encoding": True,
    "track_enabled_surface_not_authoritative_for_bitrate": True,
    "transceiver_direction_surface_not_authoritative_for_bitrate": True,
    "ui_intent_not_effective_without_sender_apply": True,
}

CODEC_NEGOTIATION_ENVELOPE_BOUNDARIES = {
    "sender_parameter_update_not_substitute_for_offer_answer": True,
    "out_of_envelope_codec_change_requires_renegotiation": True,
    "unsupported_codec_update_fail_closed": True,
    "codec_preference_negotiation_surface_distinct_from_sender_runtime_tuning": True,
}

DESIRED_EFFECTIVE_SENDER_PARAMETER_SEMANTICS = {
    "desired_sender_parameter_source": "policy_or_ui_intent",
    "effective_sender_parameter_source": "getParameters_after_apply",
    "desired_effective_must_be_distinct": True,
    "apply_requires_read_modify_write_cycle": True,
}

DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS = {
    "sender_parameter_update_supported": "set_parameters_and_verify_effective_state",
    "sender_parameter_update_out_of_envelope": "reject_and_require_renegotiation",
    "sender_parameter_update_unsupported": "reject_and_keep_previous_effective_parameters",
    "sender_parameter_update_terminal_session": "reject_terminal_session_mutation",
    "sender_parameter_update_late_after_session_close": "ignore_and_log_late_update",
}

SENDER_PARAMETER_CONTRACT_INVARIANTS = {
    "single_authoritative_sender_surface_for_encoding_updates": True,
    "bitrate_encoding_control_not_mixed_with_track_enable_semantics": True,
    "sender_tuning_not_mixed_with_direction_negotiation_semantics": True,
    "codec_envelope_boundary_enforced": True,
    "unsupported_or_out_of_envelope_updates_fail_closed": True,
    "production_runtime_change_allowed_in_25_4": False,
}


def validate_webrtc_sender_parameters_bitrate_codec_boundary_contract() -> list[str]:
    errors: list[str] = []

    from app.webrtc_incall_media_control_quality_observability_baseline import (
        MEDIA_CONTROL_OPERATION_MATRIX,
        STAGE25_SUBSTEP_DRAFT,
    )
    from app.webrtc_media_control_state_inventory import (
        ALLOWED_STATE_RELATIONS,
        MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX,
    )
    from app.webrtc_mute_unmute_source_switch_transceiver_direction_contract import (
        RENEGOTIATION_REQUIREMENT_MATRIX,
        TRANSCEIVER_DIRECTION_CONTRACT,
    )

    if STAGE25_SUBSTEP_DRAFT.get("25.4") != "sender_parameters_bitrate_and_codec_boundary_contract":
        errors.append("Stage 25.1 substep draft must define 25.4 boundary contract milestone")

    required_control_surface = {
        "operation_scope": ("sender_encoding_update",),
        "authoritative_api_read": "RTCRtpSender.getParameters",
        "authoritative_api_write": "RTCRtpSender.setParameters",
        "authoritative_owner": "media_runtime_owner",
        "terminal_session_mutation_allowed": False,
    }
    if SENDER_PARAMETER_CONTROL_SURFACE_BASELINE != required_control_surface:
        errors.append("SENDER_PARAMETER_CONTROL_SURFACE_BASELINE must match canonical sender surface baseline")

    required_update_classes = {
        "bitrate_tuning",
        "encoding_activation_toggle",
        "degradation_preference_update",
    }
    if set(ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES.keys()) != required_update_classes:
        errors.append("ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES must define canonical update classes")
    for class_name, class_spec in ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES.items():
        if not class_spec.get("parameter_path"):
            errors.append(f"{class_name}: parameter_path is required")
        if class_spec.get("default_renegotiation_required") is not False:
            errors.append(f"{class_name}: default_renegotiation_required must be false")
        if class_spec.get("requires_envelope_validation") is not True:
            errors.append(f"{class_name}: requires_envelope_validation must be true")

    required_ownership_boundaries = {
        "sender_parameters_authoritative_for_bitrate_encoding": True,
        "track_enabled_surface_not_authoritative_for_bitrate": True,
        "transceiver_direction_surface_not_authoritative_for_bitrate": True,
        "ui_intent_not_effective_without_sender_apply": True,
    }
    if BITRATE_ENCODING_OWNERSHIP_BOUNDARIES != required_ownership_boundaries:
        errors.append("BITRATE_ENCODING_OWNERSHIP_BOUNDARIES must match canonical ownership boundaries")

    required_codec_boundaries = {
        "sender_parameter_update_not_substitute_for_offer_answer": True,
        "out_of_envelope_codec_change_requires_renegotiation": True,
        "unsupported_codec_update_fail_closed": True,
        "codec_preference_negotiation_surface_distinct_from_sender_runtime_tuning": True,
    }
    if CODEC_NEGOTIATION_ENVELOPE_BOUNDARIES != required_codec_boundaries:
        errors.append("CODEC_NEGOTIATION_ENVELOPE_BOUNDARIES must match canonical codec boundary rules")

    required_semantics = {
        "desired_sender_parameter_source": "policy_or_ui_intent",
        "effective_sender_parameter_source": "getParameters_after_apply",
        "desired_effective_must_be_distinct": True,
        "apply_requires_read_modify_write_cycle": True,
    }
    if DESIRED_EFFECTIVE_SENDER_PARAMETER_SEMANTICS != required_semantics:
        errors.append("DESIRED_EFFECTIVE_SENDER_PARAMETER_SEMANTICS must match canonical semantics baseline")

    required_case_actions = {
        "sender_parameter_update_supported": "set_parameters_and_verify_effective_state",
        "sender_parameter_update_out_of_envelope": "reject_and_require_renegotiation",
        "sender_parameter_update_unsupported": "reject_and_keep_previous_effective_parameters",
        "sender_parameter_update_terminal_session": "reject_terminal_session_mutation",
        "sender_parameter_update_late_after_session_close": "ignore_and_log_late_update",
    }
    if DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS != required_case_actions:
        errors.append("DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS must match canonical case action set")

    required_invariants = {
        "single_authoritative_sender_surface_for_encoding_updates": True,
        "bitrate_encoding_control_not_mixed_with_track_enable_semantics": True,
        "sender_tuning_not_mixed_with_direction_negotiation_semantics": True,
        "codec_envelope_boundary_enforced": True,
        "unsupported_or_out_of_envelope_updates_fail_closed": True,
        "production_runtime_change_allowed_in_25_4": False,
    }
    if SENDER_PARAMETER_CONTRACT_INVARIANTS != required_invariants:
        errors.append("SENDER_PARAMETER_CONTRACT_INVARIANTS must match canonical invariant set")

    # Cross-check against Step 25.1 operation matrix.
    sender_op_25_1 = MEDIA_CONTROL_OPERATION_MATRIX.get("sender_encoding_update")
    if sender_op_25_1 is None:
        errors.append("Step 25.1 operation matrix must define sender_encoding_update")
    else:
        if sender_op_25_1.get("canonical_api") != SENDER_PARAMETER_CONTROL_SURFACE_BASELINE["authoritative_api_write"]:
            errors.append("sender_encoding_update canonical_api must align with 25.4 sender write API")
        if sender_op_25_1.get("requires_renegotiation") is not False:
            errors.append("sender_encoding_update default renegotiation requirement must remain false in 25.1")

    # Cross-check against Step 25.2 ownership matrix.
    sender_op_25_2 = MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX.get("sender_encoding_update")
    if sender_op_25_2 is None:
        errors.append("Step 25.2 ownership matrix must define sender_encoding_update")
    else:
        if sender_op_25_2.canonical_api != SENDER_PARAMETER_CONTROL_SURFACE_BASELINE["authoritative_api_write"]:
            errors.append("sender_encoding_update canonical_api must align with 25.4 sender contract")
        if sender_op_25_2.authoritative_owner != SENDER_PARAMETER_CONTROL_SURFACE_BASELINE["authoritative_owner"]:
            errors.append("sender_encoding_update authoritative_owner must align with 25.4 sender contract")

    if ALLOWED_STATE_RELATIONS.get("set_parameters_affects_sender_only_not_track_enabled_state") is not True:
        errors.append("Step 25.2 must preserve sender-vs-track boundary relation for setParameters")

    # Cross-check against Step 25.3 direction semantics.
    if RENEGOTIATION_REQUIREMENT_MATRIX.get("transceiver_direction_change") is not True:
        errors.append("Step 25.3 must preserve renegotiation requirement for transceiver_direction_change")
    if TRANSCEIVER_DIRECTION_CONTRACT.get("authoritative_control_surface") != "RTCRtpTransceiver.direction":
        errors.append("Step 25.3 direction control surface must remain RTCRtpTransceiver.direction")

    return errors

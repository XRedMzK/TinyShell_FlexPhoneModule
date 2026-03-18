from __future__ import annotations


MUTE_UNMUTE_CONTRACT = {
    "operation_scope": ("mic_mute_unmute", "camera_mute_unmute"),
    "authoritative_control_surface": "MediaStreamTrack.enabled",
    "authoritative_owner": "media_runtime_owner",
    "user_mute_intent_source": "local_ui_control_state",
    "source_mute_signal_source": "MediaStreamTrack.muted_or_mute_event",
    "user_mute_not_equal_source_mute": True,
    "renegotiation_required": False,
    "terminal_session_mutation_allowed": False,
}

SOURCE_SWITCH_CONTRACT = {
    "operation_scope": ("source_switch_same_kind",),
    "authoritative_control_surface": "RTCRtpSender.replaceTrack",
    "authoritative_owner": "media_runtime_owner",
    "eligible_track_kind_relation": "same_kind_required",
    "default_renegotiation_required": False,
    "renegotiation_required_on_envelope_break": True,
    "terminal_session_mutation_allowed": False,
}

TRANSCEIVER_DIRECTION_CONTRACT = {
    "operation_scope": ("transceiver_direction_change",),
    "authoritative_control_surface": "RTCRtpTransceiver.direction",
    "authoritative_owner": "lifecycle_owner",
    "desired_state_field": "direction",
    "effective_state_field": "currentDirection",
    "desired_not_equal_effective": True,
    "renegotiation_required": True,
    "terminal_session_mutation_allowed": False,
}

RENEGOTIATION_REQUIREMENT_MATRIX = {
    "mic_mute_unmute": False,
    "camera_mute_unmute": False,
    "source_switch_same_kind": False,
    "transceiver_direction_change": True,
}

DETERMINISTIC_OPERATION_CASE_ACTIONS = {
    "mic_user_mute_request": "set_track_enabled_false",
    "mic_user_unmute_request": "set_track_enabled_true",
    "camera_user_mute_request": "set_track_enabled_false",
    "camera_user_unmute_request": "set_track_enabled_true",
    "source_muted_event_observed": "mark_source_muted_without_flipping_user_intent",
    "source_switch_success": "replace_track_commit_and_keep_call_active",
    "source_switch_invalid_kind": "reject_switch_and_keep_previous_track",
    "source_switch_late_abort": "ignore_abort_and_log_without_state_corruption",
    "direction_change_request": "set_direction_and_start_negotiation",
    "direction_change_negotiation_committed": "update_current_direction_effective_state",
    "direction_change_negotiation_failed": "rollback_requested_direction_and_log",
}

OWNERSHIP_BOUNDARY_RULES = {
    "ui_intent_not_authoritative_without_surface_apply": True,
    "track_surface_authoritative_for_user_mute": True,
    "sender_surface_authoritative_for_source_switch": True,
    "transceiver_surface_authoritative_for_direction_change": True,
    "source_mute_signal_observational_not_ui_authoritative": True,
}

MUTE_SWITCH_DIRECTION_INVARIANTS = {
    "single_authoritative_surface_per_operation": True,
    "enabled_vs_muted_semantics_must_remain_distinct": True,
    "replace_track_not_treated_as_mute_toggle": True,
    "direction_currentDirection_semantics_must_remain_distinct": True,
    "terminal_session_rejects_operation_mutation": True,
    "production_runtime_change_allowed_in_25_3": False,
}


def validate_webrtc_mute_unmute_source_switch_transceiver_direction_contract() -> list[str]:
    errors: list[str] = []

    from app.webrtc_incall_media_control_quality_observability_baseline import (
        MEDIA_CONTROL_OPERATION_MATRIX,
        STAGE25_SUBSTEP_DRAFT,
    )
    from app.webrtc_media_control_state_inventory import (
        ALLOWED_STATE_RELATIONS,
        DESIRED_EFFECTIVE_STATE_DISTINCTION,
        MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX,
    )

    if STAGE25_SUBSTEP_DRAFT.get("25.3") != "mute_unmute_source_switch_and_transceiver_direction_contract":
        errors.append("Stage 25.1 substep draft must define 25.3 contract milestone")

    expected_mute_contract = {
        "operation_scope": ("mic_mute_unmute", "camera_mute_unmute"),
        "authoritative_control_surface": "MediaStreamTrack.enabled",
        "authoritative_owner": "media_runtime_owner",
        "user_mute_intent_source": "local_ui_control_state",
        "source_mute_signal_source": "MediaStreamTrack.muted_or_mute_event",
        "user_mute_not_equal_source_mute": True,
        "renegotiation_required": False,
        "terminal_session_mutation_allowed": False,
    }
    if MUTE_UNMUTE_CONTRACT != expected_mute_contract:
        errors.append("MUTE_UNMUTE_CONTRACT must match canonical mute/unmute baseline")

    expected_source_switch_contract = {
        "operation_scope": ("source_switch_same_kind",),
        "authoritative_control_surface": "RTCRtpSender.replaceTrack",
        "authoritative_owner": "media_runtime_owner",
        "eligible_track_kind_relation": "same_kind_required",
        "default_renegotiation_required": False,
        "renegotiation_required_on_envelope_break": True,
        "terminal_session_mutation_allowed": False,
    }
    if SOURCE_SWITCH_CONTRACT != expected_source_switch_contract:
        errors.append("SOURCE_SWITCH_CONTRACT must match canonical source-switch baseline")

    expected_direction_contract = {
        "operation_scope": ("transceiver_direction_change",),
        "authoritative_control_surface": "RTCRtpTransceiver.direction",
        "authoritative_owner": "lifecycle_owner",
        "desired_state_field": "direction",
        "effective_state_field": "currentDirection",
        "desired_not_equal_effective": True,
        "renegotiation_required": True,
        "terminal_session_mutation_allowed": False,
    }
    if TRANSCEIVER_DIRECTION_CONTRACT != expected_direction_contract:
        errors.append("TRANSCEIVER_DIRECTION_CONTRACT must match canonical direction-change baseline")

    expected_renegotiation_matrix = {
        "mic_mute_unmute": False,
        "camera_mute_unmute": False,
        "source_switch_same_kind": False,
        "transceiver_direction_change": True,
    }
    if RENEGOTIATION_REQUIREMENT_MATRIX != expected_renegotiation_matrix:
        errors.append("RENEGOTIATION_REQUIREMENT_MATRIX must match canonical renegotiation requirements")

    required_actions = {
        "mic_user_mute_request",
        "mic_user_unmute_request",
        "camera_user_mute_request",
        "camera_user_unmute_request",
        "source_muted_event_observed",
        "source_switch_success",
        "source_switch_invalid_kind",
        "source_switch_late_abort",
        "direction_change_request",
        "direction_change_negotiation_committed",
        "direction_change_negotiation_failed",
    }
    if set(DETERMINISTIC_OPERATION_CASE_ACTIONS.keys()) != required_actions:
        errors.append("DETERMINISTIC_OPERATION_CASE_ACTIONS must define canonical case action set")

    required_ownership_rules = {
        "ui_intent_not_authoritative_without_surface_apply": True,
        "track_surface_authoritative_for_user_mute": True,
        "sender_surface_authoritative_for_source_switch": True,
        "transceiver_surface_authoritative_for_direction_change": True,
        "source_mute_signal_observational_not_ui_authoritative": True,
    }
    if OWNERSHIP_BOUNDARY_RULES != required_ownership_rules:
        errors.append("OWNERSHIP_BOUNDARY_RULES must match canonical ownership boundary rules")

    required_invariants = {
        "single_authoritative_surface_per_operation": True,
        "enabled_vs_muted_semantics_must_remain_distinct": True,
        "replace_track_not_treated_as_mute_toggle": True,
        "direction_currentDirection_semantics_must_remain_distinct": True,
        "terminal_session_rejects_operation_mutation": True,
        "production_runtime_change_allowed_in_25_3": False,
    }
    if MUTE_SWITCH_DIRECTION_INVARIANTS != required_invariants:
        errors.append("MUTE_SWITCH_DIRECTION_INVARIANTS must match canonical invariant set")

    # Cross-check against 25.1 operation matrix.
    for operation_name, expected_renegotiation in RENEGOTIATION_REQUIREMENT_MATRIX.items():
        op_from_25_1 = MEDIA_CONTROL_OPERATION_MATRIX.get(operation_name, {})
        if op_from_25_1.get("requires_renegotiation") != expected_renegotiation:
            errors.append(f"{operation_name}: renegotiation requirement must align with 25.1 baseline matrix")

    # Cross-check against 25.2 ownership matrix.
    mute_op = MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX.get("mic_mute_unmute")
    camera_op = MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX.get("camera_mute_unmute")
    source_switch_op = MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX.get("source_switch_same_kind")
    direction_op = MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX.get("transceiver_direction_change")
    if mute_op is None or camera_op is None or source_switch_op is None or direction_op is None:
        errors.append("Step 25.2 ownership matrix must define mic/camera/switch/direction operations")
    else:
        if mute_op.canonical_api != MUTE_UNMUTE_CONTRACT["authoritative_control_surface"]:
            errors.append("mic_mute_unmute canonical_api must align with 25.3 mute contract")
        if camera_op.canonical_api != MUTE_UNMUTE_CONTRACT["authoritative_control_surface"]:
            errors.append("camera_mute_unmute canonical_api must align with 25.3 mute contract")
        if source_switch_op.canonical_api != SOURCE_SWITCH_CONTRACT["authoritative_control_surface"]:
            errors.append("source_switch_same_kind canonical_api must align with 25.3 source-switch contract")
        if direction_op.canonical_api != TRANSCEIVER_DIRECTION_CONTRACT["authoritative_control_surface"]:
            errors.append("transceiver_direction_change canonical_api must align with 25.3 direction contract")
        if mute_op.authoritative_owner != MUTE_UNMUTE_CONTRACT["authoritative_owner"]:
            errors.append("mic_mute_unmute authoritative_owner must align with 25.3 mute contract")
        if source_switch_op.authoritative_owner != SOURCE_SWITCH_CONTRACT["authoritative_owner"]:
            errors.append("source_switch authoritative_owner must align with 25.3 source-switch contract")
        if direction_op.authoritative_owner != TRANSCEIVER_DIRECTION_CONTRACT["authoritative_owner"]:
            errors.append("direction authoritative_owner must align with 25.3 direction contract")

    # Cross-check required distinction/relations remain explicit.
    if DESIRED_EFFECTIVE_STATE_DISTINCTION.get("track_enabled_vs_track_muted", {}).get("must_not_be_conflated") is not True:
        errors.append("25.2 must preserve track_enabled_vs_track_muted distinction")
    if (
        DESIRED_EFFECTIVE_STATE_DISTINCTION.get("transceiver_direction_vs_current_direction", {}).get(
            "must_not_be_conflated"
        )
        is not True
    ):
        errors.append("25.2 must preserve direction vs currentDirection distinction")
    if ALLOWED_STATE_RELATIONS.get("source_mute_does_not_equal_user_mute") is not True:
        errors.append("25.2 must preserve source_mute_does_not_equal_user_mute relation")
    if ALLOWED_STATE_RELATIONS.get("direction_change_requires_negotiation_to_affect_currentDirection") is not True:
        errors.append("25.2 must preserve direction/currentDirection negotiation relation")

    return errors

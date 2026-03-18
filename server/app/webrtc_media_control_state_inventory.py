from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaControlSurfaceSpec:
    surface_name: str
    ownership_domain: str
    desired_state_fields: tuple[str, ...]
    effective_state_fields: tuple[str, ...]
    control_capability: tuple[str, ...]
    observable_only: bool


@dataclass(frozen=True)
class MediaControlOperationOwnershipSpec:
    operation_name: str
    desired_state_surface: str
    effective_state_surface: str
    authoritative_owner: str
    canonical_api: str
    renegotiation_required: bool
    terminal_mutation_allowed: bool


CANONICAL_MEDIA_CONTROL_SURFACES = (
    "local_ui_control_state",
    "local_media_stream_track_state",
    "local_rtp_sender_state",
    "local_rtp_transceiver_state",
    "remote_visible_media_state",
    "quality_stats_surface",
)

MEDIA_CONTROL_STATE_INVENTORY_BASELINE: dict[str, MediaControlSurfaceSpec] = {
    "local_ui_control_state": MediaControlSurfaceSpec(
        surface_name="local_ui_control_state",
        ownership_domain="ui_control_owner",
        desired_state_fields=("audio_user_muted", "video_user_muted", "selected_media_source_id"),
        effective_state_fields=("control_intent_committed",),
        control_capability=("emit_control_intent",),
        observable_only=False,
    ),
    "local_media_stream_track_state": MediaControlSurfaceSpec(
        surface_name="local_media_stream_track_state",
        ownership_domain="media_runtime_owner",
        desired_state_fields=("track_enabled_target",),
        effective_state_fields=("enabled", "muted", "readyState"),
        control_capability=("set_track_enabled",),
        observable_only=False,
    ),
    "local_rtp_sender_state": MediaControlSurfaceSpec(
        surface_name="local_rtp_sender_state",
        ownership_domain="media_runtime_owner",
        desired_state_fields=("target_track_binding", "target_sender_parameters"),
        effective_state_fields=("track_id", "encoding_parameters_applied"),
        control_capability=("replace_track", "set_parameters"),
        observable_only=False,
    ),
    "local_rtp_transceiver_state": MediaControlSurfaceSpec(
        surface_name="local_rtp_transceiver_state",
        ownership_domain="lifecycle_owner",
        desired_state_fields=("direction",),
        effective_state_fields=("currentDirection", "mid"),
        control_capability=("set_direction_with_negotiation"),
        observable_only=False,
    ),
    "remote_visible_media_state": MediaControlSurfaceSpec(
        surface_name="remote_visible_media_state",
        ownership_domain="media_runtime_owner",
        desired_state_fields=("none",),
        effective_state_fields=("remote_track_flow_state", "remote_direction_effective_state"),
        control_capability=("derived_from_sender_and_transceiver",),
        observable_only=True,
    ),
    "quality_stats_surface": MediaControlSurfaceSpec(
        surface_name="quality_stats_surface",
        ownership_domain="observability_owner",
        desired_state_fields=("sampling_policy",),
        effective_state_fields=("rtc_stats_report", "candidate_pair_metrics", "rtp_metrics"),
        control_capability=("read_getstats",),
        observable_only=True,
    ),
}

MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX: dict[str, MediaControlOperationOwnershipSpec] = {
    "mic_mute_unmute": MediaControlOperationOwnershipSpec(
        operation_name="mic_mute_unmute",
        desired_state_surface="local_ui_control_state",
        effective_state_surface="local_media_stream_track_state",
        authoritative_owner="media_runtime_owner",
        canonical_api="MediaStreamTrack.enabled",
        renegotiation_required=False,
        terminal_mutation_allowed=False,
    ),
    "camera_mute_unmute": MediaControlOperationOwnershipSpec(
        operation_name="camera_mute_unmute",
        desired_state_surface="local_ui_control_state",
        effective_state_surface="local_media_stream_track_state",
        authoritative_owner="media_runtime_owner",
        canonical_api="MediaStreamTrack.enabled",
        renegotiation_required=False,
        terminal_mutation_allowed=False,
    ),
    "source_switch_same_kind": MediaControlOperationOwnershipSpec(
        operation_name="source_switch_same_kind",
        desired_state_surface="local_ui_control_state",
        effective_state_surface="local_rtp_sender_state",
        authoritative_owner="media_runtime_owner",
        canonical_api="RTCRtpSender.replaceTrack",
        renegotiation_required=False,
        terminal_mutation_allowed=False,
    ),
    "transceiver_direction_change": MediaControlOperationOwnershipSpec(
        operation_name="transceiver_direction_change",
        desired_state_surface="local_rtp_transceiver_state",
        effective_state_surface="local_rtp_transceiver_state",
        authoritative_owner="lifecycle_owner",
        canonical_api="RTCRtpTransceiver.direction",
        renegotiation_required=True,
        terminal_mutation_allowed=False,
    ),
    "sender_encoding_update": MediaControlOperationOwnershipSpec(
        operation_name="sender_encoding_update",
        desired_state_surface="local_rtp_sender_state",
        effective_state_surface="local_rtp_sender_state",
        authoritative_owner="media_runtime_owner",
        canonical_api="RTCRtpSender.setParameters",
        renegotiation_required=False,
        terminal_mutation_allowed=False,
    ),
}

DESIRED_EFFECTIVE_STATE_DISTINCTION = {
    "track_enabled_vs_track_muted": {
        "desired_state_field": "track_enabled_target",
        "effective_state_fields": ("enabled", "muted"),
        "must_not_be_conflated": True,
    },
    "transceiver_direction_vs_current_direction": {
        "desired_state_field": "direction",
        "effective_state_fields": ("currentDirection",),
        "must_not_be_conflated": True,
    },
    "ui_intent_vs_remote_visibility": {
        "desired_state_field": "audio_user_muted/video_user_muted",
        "effective_state_fields": ("remote_track_flow_state",),
        "must_not_be_conflated": True,
    },
}

ALLOWED_STATE_RELATIONS = {
    "user_mute_controls_track_enabled": True,
    "source_mute_does_not_equal_user_mute": True,
    "replace_track_updates_sender_binding": True,
    "direction_change_requires_negotiation_to_affect_currentDirection": True,
    "set_parameters_affects_sender_only_not_track_enabled_state": True,
    "stats_surface_is_observability_only": True,
}

MEDIA_CONTROL_STATE_INVARIANTS = {
    "single_authoritative_owner_per_operation": True,
    "desired_and_effective_states_explicitly_separated": True,
    "enabled_vs_muted_distinction_required": True,
    "direction_vs_currentDirection_distinction_required": True,
    "sender_parameters_distinct_from_track_state": True,
    "terminal_session_rejects_mutation_operations": True,
    "production_runtime_change_allowed_in_25_2": False,
}


def validate_webrtc_media_control_state_inventory() -> list[str]:
    errors: list[str] = []

    from app.webrtc_incall_media_control_quality_observability_baseline import (
        MEDIA_CONTROL_OPERATION_MATRIX,
        MEDIA_CONTROL_OWNERSHIP_BOUNDARIES,
        STAGE25_SUBSTEP_DRAFT,
    )

    if tuple(MEDIA_CONTROL_STATE_INVENTORY_BASELINE.keys()) != CANONICAL_MEDIA_CONTROL_SURFACES:
        errors.append("MEDIA_CONTROL_STATE_INVENTORY_BASELINE keys must match canonical surface order")

    allowed_owners = {
        "ui_control_owner",
        "lifecycle_owner",
        "media_runtime_owner",
        "observability_owner",
    }

    for surface_name, spec in MEDIA_CONTROL_STATE_INVENTORY_BASELINE.items():
        if spec.surface_name != surface_name:
            errors.append(f"{surface_name}: surface_name field must match dictionary key")
        if spec.ownership_domain not in allowed_owners:
            errors.append(f"{surface_name}: invalid ownership_domain")
        if not spec.desired_state_fields:
            errors.append(f"{surface_name}: desired_state_fields must be non-empty")
        if not spec.effective_state_fields:
            errors.append(f"{surface_name}: effective_state_fields must be non-empty")
        if not spec.control_capability:
            errors.append(f"{surface_name}: control_capability must be non-empty")

    required_ops = set(MEDIA_CONTROL_OPERATION_MATRIX.keys())
    if set(MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX.keys()) != required_ops:
        errors.append("MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX must match 25.1 operation set")

    for operation_name, op_spec in MEDIA_CONTROL_OPERATION_OWNERSHIP_MATRIX.items():
        if op_spec.operation_name != operation_name:
            errors.append(f"{operation_name}: operation_name field must match dictionary key")
        if op_spec.authoritative_owner not in allowed_owners:
            errors.append(f"{operation_name}: invalid authoritative_owner")
        if op_spec.desired_state_surface not in MEDIA_CONTROL_STATE_INVENTORY_BASELINE:
            errors.append(f"{operation_name}: desired_state_surface must reference canonical surface")
        if op_spec.effective_state_surface not in MEDIA_CONTROL_STATE_INVENTORY_BASELINE:
            errors.append(f"{operation_name}: effective_state_surface must reference canonical surface")
        if op_spec.terminal_mutation_allowed is not False:
            errors.append(f"{operation_name}: terminal_mutation_allowed must be false")

        op_matrix_spec = MEDIA_CONTROL_OPERATION_MATRIX.get(operation_name, {})
        if op_spec.canonical_api != op_matrix_spec.get("canonical_api"):
            errors.append(f"{operation_name}: canonical_api must align with 25.1 matrix")
        if op_spec.renegotiation_required != op_matrix_spec.get("requires_renegotiation"):
            errors.append(f"{operation_name}: renegotiation flag must align with 25.1 matrix")

    required_distinction_keys = {
        "track_enabled_vs_track_muted",
        "transceiver_direction_vs_current_direction",
        "ui_intent_vs_remote_visibility",
    }
    if set(DESIRED_EFFECTIVE_STATE_DISTINCTION.keys()) != required_distinction_keys:
        errors.append("DESIRED_EFFECTIVE_STATE_DISTINCTION must define canonical distinction set")
    for key, payload in DESIRED_EFFECTIVE_STATE_DISTINCTION.items():
        if payload.get("must_not_be_conflated") is not True:
            errors.append(f"{key}: must_not_be_conflated must be true")
        if not payload.get("desired_state_field"):
            errors.append(f"{key}: desired_state_field is required")
        if not payload.get("effective_state_fields"):
            errors.append(f"{key}: effective_state_fields are required")

    required_relations = {
        "user_mute_controls_track_enabled": True,
        "source_mute_does_not_equal_user_mute": True,
        "replace_track_updates_sender_binding": True,
        "direction_change_requires_negotiation_to_affect_currentDirection": True,
        "set_parameters_affects_sender_only_not_track_enabled_state": True,
        "stats_surface_is_observability_only": True,
    }
    if ALLOWED_STATE_RELATIONS != required_relations:
        errors.append("ALLOWED_STATE_RELATIONS must match canonical relation set")

    required_invariants = {
        "single_authoritative_owner_per_operation": True,
        "desired_and_effective_states_explicitly_separated": True,
        "enabled_vs_muted_distinction_required": True,
        "direction_vs_currentDirection_distinction_required": True,
        "sender_parameters_distinct_from_track_state": True,
        "terminal_session_rejects_mutation_operations": True,
        "production_runtime_change_allowed_in_25_2": False,
    }
    if MEDIA_CONTROL_STATE_INVARIANTS != required_invariants:
        errors.append("MEDIA_CONTROL_STATE_INVARIANTS must match canonical invariant set")

    if MEDIA_CONTROL_OWNERSHIP_BOUNDARIES.get("ownership_overlap_forbidden") is not True:
        errors.append("Stage 25.1 ownership boundaries must keep ownership_overlap_forbidden=true")

    if STAGE25_SUBSTEP_DRAFT.get("25.2") != "media_control_state_inventory_and_ownership_matrix":
        errors.append("Stage 25.1 substep draft must define 25.2 inventory milestone")

    return errors

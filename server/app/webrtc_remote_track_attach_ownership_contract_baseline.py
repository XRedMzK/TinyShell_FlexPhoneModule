from __future__ import annotations


REMOTE_ATTACH_OWNER_KEY_SCHEMA_28_2 = {
    "primary_key_model": "receiver_transceiver_centric",
    "primary_key_fields": (
        "receiver",
        "transceiver",
    ),
    "track_id_primary_key": False,
    "stream_index_primary_key": False,
    "track_id_secondary_diagnostic_key": True,
}

REMOTE_ATTACH_TARGET_SCHEMA_28_2 = {
    "attach_trigger": "RTCPeerConnection.track",
    "attach_property": "HTMLMediaElement.srcObject",
    "attach_target": "dedicated_remote_media_element_slot",
    "single_writer_attach_owner_required": True,
    "implicit_attach_side_effect_allowed": False,
}

REMOTE_ATTACH_BINDING_STATE_SCHEMA_28_2 = {
    "required_fields": (
        "owner_key",
        "element_slot",
        "stream_binding_key",
        "attached_track_ids",
        "binding_revision",
    ),
    "binding_comparison_order_sensitive": False,
    "track_membership_representation": "identity_membership_set",
}

REMOTE_STREAMLESS_TRACK_FALLBACK_28_2 = {
    "streams_may_be_empty": True,
    "streamless_branch_required": True,
    "streamless_attach_payload": "deterministic_synthetic_stream_container",
    "synthetic_stream_key_bound_to_owner_key": True,
    "streamless_branch_reentrant": True,
}

REMOTE_DUPLICATE_ATTACH_GUARD_28_2 = {
    "duplicate_detection_inputs": (
        "owner_key",
        "element_slot",
        "effective_stream_binding_membership",
    ),
    "duplicate_branch_action": "noop",
    "duplicate_branch_reassigns_srcobject": False,
    "non_duplicate_actions": (
        "new_binding",
        "remount_reattach_same_binding",
        "membership_update",
    ),
}

REMOTE_REATTACH_SEMANTICS_28_2 = {
    "remount_with_same_owner_requires_explicit_reattach": True,
    "reattach_preserves_owner_identity": True,
    "reattach_reclassifies_as_new_track_arrival": False,
    "repeated_remount_behavior_deterministic": True,
}

REMOTE_ATTACH_TRANSITIONS_28_2 = {
    "new_event": "attach",
    "duplicate_event": "noop",
    "remount": "reattach_same_binding",
    "stream_membership_change": "membership_update",
}

REMOTE_ATTACH_INVARIANTS_28_2 = {
    "owner_key_receiver_transceiver_centric": True,
    "streamless_track_path_explicit": True,
    "duplicate_attach_is_noop": True,
    "srcobject_assignment_single_writer_controlled": True,
    "binding_state_order_insensitive_membership_based": True,
    "stable_remount_reattach_semantics": True,
    "production_runtime_change_allowed_in_28_2": False,
}

STAGE28_CLOSURE_CRITERIA_28_2 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "owner_key_streamless_duplicate_guard_binding_defined",
    "dependency_alignment_with_28_1_checker_enforced",
    "checker_and_compileall_pass",
)


def is_streamless_track_event(stream_count: int) -> bool:
    return stream_count == 0


def is_duplicate_attach(
    same_owner_key: bool,
    same_element_slot: bool,
    same_effective_membership: bool,
) -> bool:
    return same_owner_key and same_element_slot and same_effective_membership


def requires_new_binding(
    existing_binding: bool,
    duplicate_attach: bool,
) -> bool:
    return not existing_binding and not duplicate_attach


def requires_membership_update(
    existing_binding: bool,
    duplicate_attach: bool,
    membership_changed: bool,
) -> bool:
    return existing_binding and (not duplicate_attach) and membership_changed


def validate_webrtc_remote_track_attach_ownership_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_media_attach_autoplay_track_state_resilience_baseline import (
        REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL,
        STAGE28_SUBSTEP_DRAFT,
        STAGE28_VERIFICATION_TYPES,
    )

    required_owner_schema = {
        "primary_key_model": "receiver_transceiver_centric",
        "primary_key_fields": (
            "receiver",
            "transceiver",
        ),
        "track_id_primary_key": False,
        "stream_index_primary_key": False,
        "track_id_secondary_diagnostic_key": True,
    }
    if REMOTE_ATTACH_OWNER_KEY_SCHEMA_28_2 != required_owner_schema:
        errors.append("REMOTE_ATTACH_OWNER_KEY_SCHEMA_28_2 must match canonical owner-key schema")

    required_target_schema = {
        "attach_trigger": "RTCPeerConnection.track",
        "attach_property": "HTMLMediaElement.srcObject",
        "attach_target": "dedicated_remote_media_element_slot",
        "single_writer_attach_owner_required": True,
        "implicit_attach_side_effect_allowed": False,
    }
    if REMOTE_ATTACH_TARGET_SCHEMA_28_2 != required_target_schema:
        errors.append("REMOTE_ATTACH_TARGET_SCHEMA_28_2 must match canonical target schema")

    required_binding_state_schema = {
        "required_fields": (
            "owner_key",
            "element_slot",
            "stream_binding_key",
            "attached_track_ids",
            "binding_revision",
        ),
        "binding_comparison_order_sensitive": False,
        "track_membership_representation": "identity_membership_set",
    }
    if REMOTE_ATTACH_BINDING_STATE_SCHEMA_28_2 != required_binding_state_schema:
        errors.append("REMOTE_ATTACH_BINDING_STATE_SCHEMA_28_2 must match canonical binding-state schema")

    required_streamless_fallback = {
        "streams_may_be_empty": True,
        "streamless_branch_required": True,
        "streamless_attach_payload": "deterministic_synthetic_stream_container",
        "synthetic_stream_key_bound_to_owner_key": True,
        "streamless_branch_reentrant": True,
    }
    if REMOTE_STREAMLESS_TRACK_FALLBACK_28_2 != required_streamless_fallback:
        errors.append("REMOTE_STREAMLESS_TRACK_FALLBACK_28_2 must match streamless fallback contract")

    required_duplicate_guard = {
        "duplicate_detection_inputs": (
            "owner_key",
            "element_slot",
            "effective_stream_binding_membership",
        ),
        "duplicate_branch_action": "noop",
        "duplicate_branch_reassigns_srcobject": False,
        "non_duplicate_actions": (
            "new_binding",
            "remount_reattach_same_binding",
            "membership_update",
        ),
    }
    if REMOTE_DUPLICATE_ATTACH_GUARD_28_2 != required_duplicate_guard:
        errors.append("REMOTE_DUPLICATE_ATTACH_GUARD_28_2 must match duplicate-attach guard")

    required_reattach_semantics = {
        "remount_with_same_owner_requires_explicit_reattach": True,
        "reattach_preserves_owner_identity": True,
        "reattach_reclassifies_as_new_track_arrival": False,
        "repeated_remount_behavior_deterministic": True,
    }
    if REMOTE_REATTACH_SEMANTICS_28_2 != required_reattach_semantics:
        errors.append("REMOTE_REATTACH_SEMANTICS_28_2 must match canonical reattach semantics")

    required_transitions = {
        "new_event": "attach",
        "duplicate_event": "noop",
        "remount": "reattach_same_binding",
        "stream_membership_change": "membership_update",
    }
    if REMOTE_ATTACH_TRANSITIONS_28_2 != required_transitions:
        errors.append("REMOTE_ATTACH_TRANSITIONS_28_2 must match transition contract")

    required_invariants = {
        "owner_key_receiver_transceiver_centric": True,
        "streamless_track_path_explicit": True,
        "duplicate_attach_is_noop": True,
        "srcobject_assignment_single_writer_controlled": True,
        "binding_state_order_insensitive_membership_based": True,
        "stable_remount_reattach_semantics": True,
        "production_runtime_change_allowed_in_28_2": False,
    }
    if REMOTE_ATTACH_INVARIANTS_28_2 != required_invariants:
        errors.append("REMOTE_ATTACH_INVARIANTS_28_2 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "owner_key_streamless_duplicate_guard_binding_defined",
        "dependency_alignment_with_28_1_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE28_CLOSURE_CRITERIA_28_2 != required_closure:
        errors.append("STAGE28_CLOSURE_CRITERIA_28_2 must match closure criteria")

    if STAGE28_SUBSTEP_DRAFT.get("28.2") != "remote_track_attach_and_ownership_contract":
        errors.append("Stage 28 draft must define 28.2 remote-track attach milestone")

    if STAGE28_VERIFICATION_TYPES.get("28.2") != "build check":
        errors.append("Stage 28 verification map must keep 28.2 as build check")

    if REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL.get("attach_trigger") != "pc.ontrack":
        errors.append("28.1 attach model must keep ontrack as authoritative trigger")

    if REMOTE_TRACK_ATTACH_OWNERSHIP_MODEL.get("stable_binding_key") != "receiver_track_identity":
        errors.append("28.1 attach model must keep stable receiver-track identity semantics")

    if is_streamless_track_event(0) is not True:
        errors.append("is_streamless_track_event must classify zero-stream events as streamless")

    if is_duplicate_attach(True, True, True) is not True:
        errors.append("is_duplicate_attach must detect duplicate ownership-slot-membership triples")

    if requires_new_binding(existing_binding=False, duplicate_attach=False) is not True:
        errors.append("requires_new_binding must allow attach for non-existing non-duplicate bindings")

    if (
        requires_membership_update(
            existing_binding=True,
            duplicate_attach=False,
            membership_changed=True,
        )
        is not True
    ):
        errors.append("requires_membership_update must allow membership update on non-duplicate existing binding")

    return errors

from __future__ import annotations


DIMENSION_RECONCILIATION_SURFACES_29_5 = {
    "intrinsic_width_property": "HTMLVideoElement.videoWidth",
    "intrinsic_height_property": "HTMLVideoElement.videoHeight",
    "initial_dimension_event": "HTMLMediaElement.loadedmetadata",
    "dimension_update_event": "HTMLVideoElement.resize",
    "ready_state_surface": "HTMLMediaElement.readyState",
    "css_layout_box_authoritative_for_dimension_truth": False,
}

DIMENSION_TRUTH_MODEL_29_5 = {
    "intrinsic_dimensions_are_canonical_truth": True,
    "intrinsic_dimension_unit": "css_pixels",
    "have_nothing_dimensions_unproven_allowed": True,
    "zero_dimensions_before_metadata_allowed": True,
    "loadedmetadata_establishes_initial_dimension_proof": True,
    "resize_establishes_subsequent_dimension_updates": True,
}

DIMENSION_RECONCILIATION_POLICY_29_5 = {
    "metadata_or_resize_signal_required_for_reconcile": True,
    "explicit_runtime_snapshot_update_required": True,
    "dimension_known_requires_positive_intrinsic_values": True,
    "css_only_resize_used_as_dimension_truth": False,
    "stale_snapshot_without_dimension_signal_allowed": False,
}

DIMENSION_FAILURE_BOUNDARY_29_5 = {
    "dimension_change_equals_failure": False,
    "dimension_change_equals_terminal": False,
    "dimension_change_equals_reattach_trigger": False,
    "dimension_change_equals_progress_or_freeze_proof": False,
    "terminal_failure_out_of_scope_for_29_5": True,
}

DIMENSION_CLASSIFICATION_STATES_29_5 = (
    "dimension_unproven",
    "dimension_initial_proven",
    "dimension_update_observed",
    "dimension_reconciled",
    "dimension_invalid_snapshot",
    "terminal_out_of_scope",
)

DIMENSION_INVARIANTS_29_5 = {
    "intrinsic_dimensions_canonical_truth": True,
    "layout_css_size_non_authoritative": True,
    "dimension_unproven_allowed_before_metadata": True,
    "resize_is_non_terminal_intrinsic_update": True,
    "dimension_change_not_reattach_trigger": True,
    "dimension_change_not_failure_branch": True,
    "production_runtime_change_allowed_in_29_5": False,
}

STAGE29_CLOSURE_CRITERIA_29_5 = (
    "baseline_doc_present",
    "baseline_module_present",
    "baseline_checker_present",
    "intrinsic_truth_and_metadata_resize_boundaries_explicit",
    "intrinsic_vs_layout_boundary_and_non_equivalence_to_failure_explicit",
    "dependency_alignment_with_29_1_29_2_29_3_29_4_checker_enforced",
    "checker_and_compileall_pass",
)


def is_intrinsic_dimension_known(video_width: int, video_height: int, ready_state: int | None) -> bool:
    if ready_state == 0:
        return False
    return video_width > 0 and video_height > 0


def is_dimension_update_event(event_name: str | None) -> bool:
    return event_name == "resize"


def is_dimension_unproven(video_width: int, video_height: int, ready_state: int | None) -> bool:
    return not is_intrinsic_dimension_known(video_width, video_height, ready_state)


def requires_reattach_on_dimension_change(dimension_changed: bool, terminal: bool) -> bool:
    return dimension_changed and terminal


def classify_dimension_reconciliation_state(
    metadata_seen: bool,
    resize_seen: bool,
    video_width: int,
    video_height: int,
    ready_state: int | None,
    reconciled: bool,
    terminal: bool,
) -> str:
    if terminal:
        return "terminal_out_of_scope"
    if video_width < 0 or video_height < 0:
        return "dimension_invalid_snapshot"
    if is_dimension_unproven(video_width, video_height, ready_state):
        return "dimension_unproven"
    if resize_seen and reconciled:
        return "dimension_reconciled"
    if resize_seen:
        return "dimension_update_observed"
    if metadata_seen:
        return "dimension_initial_proven"
    if reconciled:
        return "dimension_reconciled"
    return "dimension_initial_proven"


def validate_webrtc_dimension_resize_reconciliation_contract_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_remote_video_first_frame_render_stall_dimension_change_resilience_baseline import (
        DIMENSION_CHANGE_RECONCILIATION_MODEL,
        REMOTE_VIDEO_SURFACES,
        STAGE29_SUBSTEP_DRAFT,
        STAGE29_VERIFICATION_TYPES,
    )
    from app.webrtc_remote_video_first_frame_readiness_contract_baseline import (
        FIRST_FRAME_INVARIANTS_29_2,
        FIRST_FRAME_READINESS_SURFACES_29_2,
    )
    from app.webrtc_frame_progress_freeze_detection_observability_contract_baseline import (
        FRAME_PROGRESS_INVARIANTS_29_3,
    )
    from app.webrtc_waiting_stalled_resume_recovery_contract_baseline import (
        WAITING_STALLED_INVARIANTS_29_4,
    )
    from app.webrtc_remote_track_attach_ownership_contract_baseline import (
        REMOTE_ATTACH_INVARIANTS_28_2,
    )

    required_surfaces = {
        "intrinsic_width_property": "HTMLVideoElement.videoWidth",
        "intrinsic_height_property": "HTMLVideoElement.videoHeight",
        "initial_dimension_event": "HTMLMediaElement.loadedmetadata",
        "dimension_update_event": "HTMLVideoElement.resize",
        "ready_state_surface": "HTMLMediaElement.readyState",
        "css_layout_box_authoritative_for_dimension_truth": False,
    }
    if DIMENSION_RECONCILIATION_SURFACES_29_5 != required_surfaces:
        errors.append("DIMENSION_RECONCILIATION_SURFACES_29_5 must match canonical surfaces")

    required_truth_model = {
        "intrinsic_dimensions_are_canonical_truth": True,
        "intrinsic_dimension_unit": "css_pixels",
        "have_nothing_dimensions_unproven_allowed": True,
        "zero_dimensions_before_metadata_allowed": True,
        "loadedmetadata_establishes_initial_dimension_proof": True,
        "resize_establishes_subsequent_dimension_updates": True,
    }
    if DIMENSION_TRUTH_MODEL_29_5 != required_truth_model:
        errors.append("DIMENSION_TRUTH_MODEL_29_5 must match canonical truth model")

    required_policy = {
        "metadata_or_resize_signal_required_for_reconcile": True,
        "explicit_runtime_snapshot_update_required": True,
        "dimension_known_requires_positive_intrinsic_values": True,
        "css_only_resize_used_as_dimension_truth": False,
        "stale_snapshot_without_dimension_signal_allowed": False,
    }
    if DIMENSION_RECONCILIATION_POLICY_29_5 != required_policy:
        errors.append("DIMENSION_RECONCILIATION_POLICY_29_5 must match canonical reconciliation policy")

    required_failure_boundary = {
        "dimension_change_equals_failure": False,
        "dimension_change_equals_terminal": False,
        "dimension_change_equals_reattach_trigger": False,
        "dimension_change_equals_progress_or_freeze_proof": False,
        "terminal_failure_out_of_scope_for_29_5": True,
    }
    if DIMENSION_FAILURE_BOUNDARY_29_5 != required_failure_boundary:
        errors.append("DIMENSION_FAILURE_BOUNDARY_29_5 must match canonical non-equivalence boundary")

    required_states = (
        "dimension_unproven",
        "dimension_initial_proven",
        "dimension_update_observed",
        "dimension_reconciled",
        "dimension_invalid_snapshot",
        "terminal_out_of_scope",
    )
    if DIMENSION_CLASSIFICATION_STATES_29_5 != required_states:
        errors.append("DIMENSION_CLASSIFICATION_STATES_29_5 must match canonical state set/order")

    required_invariants = {
        "intrinsic_dimensions_canonical_truth": True,
        "layout_css_size_non_authoritative": True,
        "dimension_unproven_allowed_before_metadata": True,
        "resize_is_non_terminal_intrinsic_update": True,
        "dimension_change_not_reattach_trigger": True,
        "dimension_change_not_failure_branch": True,
        "production_runtime_change_allowed_in_29_5": False,
    }
    if DIMENSION_INVARIANTS_29_5 != required_invariants:
        errors.append("DIMENSION_INVARIANTS_29_5 must match canonical invariant set")

    required_closure = (
        "baseline_doc_present",
        "baseline_module_present",
        "baseline_checker_present",
        "intrinsic_truth_and_metadata_resize_boundaries_explicit",
        "intrinsic_vs_layout_boundary_and_non_equivalence_to_failure_explicit",
        "dependency_alignment_with_29_1_29_2_29_3_29_4_checker_enforced",
        "checker_and_compileall_pass",
    )
    if STAGE29_CLOSURE_CRITERIA_29_5 != required_closure:
        errors.append("STAGE29_CLOSURE_CRITERIA_29_5 must match closure criteria")

    if STAGE29_SUBSTEP_DRAFT.get("29.5") != "dimension_resize_reconciliation_contract":
        errors.append("Stage 29 draft must keep 29.5 dimension/resize milestone")

    if STAGE29_VERIFICATION_TYPES.get("29.5") != "build check":
        errors.append("Stage 29 verification map must keep 29.5 as build check")

    if DIMENSION_CHANGE_RECONCILIATION_MODEL.get("loadedmetadata_initializes_dimension_truth") is not True:
        errors.append("29.1 model must keep loadedmetadata initial dimension truth")

    if DIMENSION_CHANGE_RECONCILIATION_MODEL.get("resize_updates_dimension_truth") is not True:
        errors.append("29.1 model must keep resize dimension update truth")

    if REMOTE_VIDEO_SURFACES.get("resize_surface") != "HTMLVideoElement.resize":
        errors.append("29.1 surfaces must keep HTMLVideoElement.resize as dimension update surface")

    if FIRST_FRAME_READINESS_SURFACES_29_2.get("metadata_surface") != "HTMLMediaElement.loadedmetadata":
        errors.append("29.2 surfaces must keep loadedmetadata metadata boundary")

    if FIRST_FRAME_INVARIANTS_29_2.get("loadedmetadata_not_first_frame_proof") is not True:
        errors.append("29.2 invariants must keep loadedmetadata not-first-frame-proof distinction")

    if FRAME_PROGRESS_INVARIANTS_29_3.get("playing_not_progress_truth") is not True:
        errors.append("29.3 invariants must keep playing separate from progress truth")

    if WAITING_STALLED_INVARIANTS_29_4.get("waiting_stalled_non_terminal_by_default") is not True:
        errors.append("29.4 invariants must keep waiting/stalled non-terminal branches")

    if REMOTE_ATTACH_INVARIANTS_28_2.get("stable_remount_reattach_semantics") is not True:
        errors.append("28.2 invariants must keep remount/reattach semantics separate from dimension updates")

    if is_intrinsic_dimension_known(1280, 720, 1) is not True:
        errors.append("is_intrinsic_dimension_known must classify positive intrinsic dimensions as known")

    if is_intrinsic_dimension_known(0, 0, 0) is not False:
        errors.append("is_intrinsic_dimension_known must keep HAVE_NOTHING zero-dimension branch unproven")

    if is_dimension_update_event("resize") is not True:
        errors.append("is_dimension_update_event must classify resize event")

    if is_dimension_unproven(0, 0, 0) is not True:
        errors.append("is_dimension_unproven must keep pre-metadata branch unproven")

    if requires_reattach_on_dimension_change(dimension_changed=True, terminal=False) is not False:
        errors.append("requires_reattach_on_dimension_change must not require reattach for non-terminal change")

    if classify_dimension_reconciliation_state(
        metadata_seen=False,
        resize_seen=False,
        video_width=0,
        video_height=0,
        ready_state=0,
        reconciled=False,
        terminal=False,
    ) != "dimension_unproven":
        errors.append("classify_dimension_reconciliation_state must map pre-metadata zero dimensions to dimension_unproven")

    if classify_dimension_reconciliation_state(
        metadata_seen=True,
        resize_seen=False,
        video_width=1280,
        video_height=720,
        ready_state=1,
        reconciled=False,
        terminal=False,
    ) != "dimension_initial_proven":
        errors.append("classify_dimension_reconciliation_state must map metadata-proven branch")

    if classify_dimension_reconciliation_state(
        metadata_seen=True,
        resize_seen=True,
        video_width=1920,
        video_height=1080,
        ready_state=4,
        reconciled=False,
        terminal=False,
    ) != "dimension_update_observed":
        errors.append("classify_dimension_reconciliation_state must map resize branch to dimension_update_observed")

    if classify_dimension_reconciliation_state(
        metadata_seen=True,
        resize_seen=True,
        video_width=1920,
        video_height=1080,
        ready_state=4,
        reconciled=True,
        terminal=False,
    ) != "dimension_reconciled":
        errors.append("classify_dimension_reconciliation_state must map reconciled resize branch")

    if classify_dimension_reconciliation_state(
        metadata_seen=True,
        resize_seen=False,
        video_width=1920,
        video_height=1080,
        ready_state=4,
        reconciled=False,
        terminal=True,
    ) != "terminal_out_of_scope":
        errors.append("classify_dimension_reconciliation_state must map terminal branch out of scope")

    return errors

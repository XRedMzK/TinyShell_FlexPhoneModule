from __future__ import annotations

import json
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.webrtc_audio_output_remote_playout_route_resilience_baseline import (
    OUTPUT_RECONCILIATION_MODEL,
    OUTPUT_SELECTION_SURFACES,
)
from app.webrtc_output_device_inventory_permission_policy_visibility_contract_baseline import (
    OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE,
    OUTPUT_VISIBILITY_PATHS,
)
from app.webrtc_output_device_loss_fallback_rebinding_contract_baseline import (
    APPLY_FAILURE_CLASSIFICATION_RULES_27_4,
    FALLBACK_TO_DEFAULT_RULES_27_4,
    OUTPUT_ROUTE_STATE_SCHEMA_27_4,
    REBIND_MODE_RULES_27_4,
)
from app.webrtc_output_devicechange_reconciliation_contract_baseline import (
    OUTPUT_DETERMINISTIC_RECONCILE_FLOW_27_5,
    OUTPUT_RECONCILE_TRIGGER_MODEL_27_5,
    OUTPUT_STALE_SINK_TRIGGER_BOUNDARIES_27_5,
)


class OutputRouteSmokeError(RuntimeError):
    pass


OUTPUT_ROUTE_SMOKE_SCENARIO_IDS = (
    "A_non_default_apply_happy_path",
    "B_stale_sink_loss_fallback_default",
    "C_passive_rebind_after_return",
    "D_interactive_rebind_rotated_id",
    "E_explicit_reconcile_without_devicechange",
    "F_error_class_sanity",
)

OUTPUT_ROUTE_SMOKE_SUCCESS_MARKER = "WebRTC output-route resilience sandbox smoke: OK"


@dataclass
class OutputRouteSandboxSession:
    visible_audiooutput_ids_ordered: list[str]
    preferred_sink_id: str = ""
    effective_sink_id: str = ""
    rebind_status: str = "bound"
    last_route_error_class: str | None = None
    last_reconcile_reason: str | None = None
    operations: list[str] = field(default_factory=list)

    def _sink_visible(self, sink_id: str) -> bool:
        return sink_id in self.visible_audiooutput_ids_ordered

    def apply_selected_sink(self, sink_id: str) -> None:
        if not self._sink_visible(sink_id):
            self.last_route_error_class = "not_found"
            self.operations.append(f"apply_not_found_{sink_id}")
            raise OutputRouteSmokeError("sink_id_missing_or_stale")

        self.preferred_sink_id = sink_id
        self.effective_sink_id = sink_id
        self.rebind_status = "bound"
        self.last_route_error_class = None
        self.operations.append(f"apply_success_{sink_id}")

    def classify_apply_failure(self, error_name: str) -> None:
        mapped = APPLY_FAILURE_CLASSIFICATION_RULES_27_4.get(error_name)
        if mapped is None:
            raise OutputRouteSmokeError(f"Unsupported apply error class: {error_name}")

        if error_name == "NotAllowedError":
            self.last_route_error_class = "not_allowed"
            self.rebind_status = "permission_blocked"
            self.operations.append("apply_permission_blocked")
            return

        self.last_route_error_class = "not_found" if error_name == "NotFoundError" else "abort"
        self.operations.append(f"apply_failure_{mapped}")
        self.fallback_to_default()

    def fallback_to_default(self) -> None:
        if FALLBACK_TO_DEFAULT_RULES_27_4["fallback_call"] != "HTMLMediaElement.setSinkId_empty_string":
            raise OutputRouteSmokeError("Fallback contract mismatch")

        self.effective_sink_id = ""
        self.rebind_status = "pending_rebind"
        self.operations.append("fallback_to_default")

    def reconcile(self, reason: str) -> None:
        self.last_reconcile_reason = reason
        self.operations.append(f"reconcile_{reason}")

        preferred_stale = bool(self.preferred_sink_id) and not self._sink_visible(self.preferred_sink_id)
        effective_stale = bool(self.effective_sink_id) and not self._sink_visible(self.effective_sink_id)

        if OUTPUT_STALE_SINK_TRIGGER_BOUNDARIES_27_5["effective_non_default_missing_in_snapshot_is_stale"]:
            if effective_stale:
                self.fallback_to_default()
                return

        if self.rebind_status == "pending_rebind" and not preferred_stale and self.preferred_sink_id:
            self.passive_rebind()

    def passive_rebind(self) -> None:
        if not self._sink_visible(self.preferred_sink_id):
            raise OutputRouteSmokeError("Passive rebind called while preferred sink is not visible")

        self.effective_sink_id = self.preferred_sink_id
        self.rebind_status = "bound"
        self.last_route_error_class = None
        self.operations.append("passive_rebind_success")

    def interactive_rebind(self, selected_sink_id: str, *, rotated_id: str | None = None) -> None:
        if REBIND_MODE_RULES_27_4["interactive_rebind"]["requires_user_activation"] is not True:
            raise OutputRouteSmokeError("Interactive rebind user-activation rule mismatch")

        apply_id = rotated_id or selected_sink_id
        self.preferred_sink_id = apply_id

        if not self._sink_visible(apply_id):
            self.last_route_error_class = "not_found"
            self.rebind_status = "rebind_required_user_activation"
            self.operations.append("interactive_rebind_not_found")
            return

        self.effective_sink_id = apply_id
        self.rebind_status = "bound"
        self.last_route_error_class = None
        self.operations.append("interactive_rebind_success")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OutputRouteSmokeError(message)


def _scenario_a_non_default_apply_happy_path() -> dict[str, Any]:
    session = OutputRouteSandboxSession(visible_audiooutput_ids_ordered=["", "sink-usb"])
    session.apply_selected_sink("sink-usb")

    _require(session.preferred_sink_id == "sink-usb", "Scenario A preferred sink mismatch")
    _require(session.effective_sink_id == "sink-usb", "Scenario A effective sink mismatch")
    _require(session.rebind_status == "bound", "Scenario A rebind status mismatch")

    return {
        "scenario_id": "A_non_default_apply_happy_path",
        "trigger": "explicit_select_then_apply",
        "authoritative_surfaces": [
            "selectAudioOutput",
            "setSinkId",
        ],
        "deterministic_actions": [
            "apply_success_non_default",
        ],
        "expected_state_assertions": [
            "preferred_equals_effective_non_default",
            "rebind_status_bound",
        ],
        "status": "PASS",
    }


def _scenario_b_stale_sink_loss_fallback_default() -> dict[str, Any]:
    session = OutputRouteSandboxSession(visible_audiooutput_ids_ordered=["", "sink-usb"])
    session.apply_selected_sink("sink-usb")

    session.visible_audiooutput_ids_ordered = [""]
    session.reconcile("devicechange_hint")

    _require(session.preferred_sink_id == "sink-usb", "Scenario B must preserve preferred sink after fallback")
    _require(session.effective_sink_id == "", "Scenario B must fallback effective sink to default")
    _require(session.rebind_status == "pending_rebind", "Scenario B rebind status mismatch")

    return {
        "scenario_id": "B_stale_sink_loss_fallback_default",
        "trigger": "active_non_default_sink_becomes_missing",
        "authoritative_surfaces": [
            "enumerateDevices_snapshot",
            "setSinkId_empty_string",
        ],
        "deterministic_actions": [
            "detect_effective_stale",
            "fallback_to_default",
        ],
        "expected_state_assertions": [
            "effective_default",
            "preferred_preserved",
            "pending_rebind",
        ],
        "status": "PASS",
    }


def _scenario_c_passive_rebind_after_return() -> dict[str, Any]:
    session = OutputRouteSandboxSession(visible_audiooutput_ids_ordered=["", "sink-usb"])
    session.apply_selected_sink("sink-usb")

    session.visible_audiooutput_ids_ordered = [""]
    session.reconcile("devicechange_hint")

    session.visible_audiooutput_ids_ordered = ["", "sink-usb"]
    session.reconcile("explicit_reconcile")

    _require(session.effective_sink_id == "sink-usb", "Scenario C passive rebind did not restore effective sink")
    _require(session.rebind_status == "bound", "Scenario C rebind status must be bound")

    return {
        "scenario_id": "C_passive_rebind_after_return",
        "trigger": "preferred_sink_visible_again",
        "authoritative_surfaces": [
            "enumerateDevices_snapshot",
            "setSinkId_preferred",
        ],
        "deterministic_actions": [
            "pending_rebind_detected",
            "passive_rebind_attempt",
        ],
        "expected_state_assertions": [
            "effective_restored_to_preferred",
            "rebind_status_bound",
        ],
        "status": "PASS",
    }


def _scenario_d_interactive_rebind_rotated_id() -> dict[str, Any]:
    session = OutputRouteSandboxSession(visible_audiooutput_ids_ordered=["", "sink-rotated"])
    session.preferred_sink_id = "sink-old"
    session.effective_sink_id = ""
    session.rebind_status = "pending_rebind"

    session.interactive_rebind("sink-old", rotated_id="sink-rotated")

    _require(session.preferred_sink_id == "sink-rotated", "Scenario D must update preferred sink to rotated id")
    _require(session.effective_sink_id == "sink-rotated", "Scenario D must apply rotated sink id")
    _require(session.rebind_status == "bound", "Scenario D rebind status must be bound")

    return {
        "scenario_id": "D_interactive_rebind_rotated_id",
        "trigger": "user_restore_action_with_persisted_id",
        "authoritative_surfaces": [
            "selectAudioOutput_with_hint",
            "setSinkId_rotated_id",
        ],
        "deterministic_actions": [
            "revalidate_persisted_id",
            "apply_rotated_id",
        ],
        "expected_state_assertions": [
            "preferred_updated_to_rotated_id",
            "effective_matches_rotated_id",
        ],
        "status": "PASS",
    }


def _scenario_e_explicit_reconcile_without_devicechange() -> dict[str, Any]:
    session = OutputRouteSandboxSession(visible_audiooutput_ids_ordered=["", "sink-usb"])
    session.apply_selected_sink("sink-usb")

    session.visible_audiooutput_ids_ordered = [""]
    session.reconcile("visibility_regain")

    _require(
        OUTPUT_RECONCILE_TRIGGER_MODEL_27_5["explicit_reconcile_without_devicechange_required"] is True,
        "Scenario E trigger model must support explicit reconcile without devicechange",
    )
    _require(session.effective_sink_id == "", "Scenario E explicit reconcile must fallback to default")

    return {
        "scenario_id": "E_explicit_reconcile_without_devicechange",
        "trigger": "explicit_reconcile_reason_without_devicechange_event",
        "authoritative_surfaces": [
            "enumerateDevices_snapshot",
        ],
        "deterministic_actions": [
            "explicit_reconcile_pass",
            "stale_detection_from_snapshot",
            "fallback_to_default",
        ],
        "expected_state_assertions": [
            "correctness_without_devicechange_dependency",
        ],
        "status": "PASS",
    }


def _scenario_f_error_class_sanity() -> dict[str, Any]:
    session = OutputRouteSandboxSession(visible_audiooutput_ids_ordered=["", "sink-usb"])

    session.classify_apply_failure("NotFoundError")
    _require(session.last_route_error_class == "not_found", "Scenario F NotFoundError class mismatch")
    _require(session.rebind_status == "pending_rebind", "Scenario F NotFoundError should route to pending_rebind")

    session.classify_apply_failure("AbortError")
    _require(session.last_route_error_class == "abort", "Scenario F AbortError class mismatch")
    _require(session.rebind_status == "pending_rebind", "Scenario F AbortError should route to pending_rebind")

    session.classify_apply_failure("NotAllowedError")
    _require(session.last_route_error_class == "not_allowed", "Scenario F NotAllowedError class mismatch")
    _require(session.rebind_status == "permission_blocked", "Scenario F NotAllowedError branch mismatch")

    return {
        "scenario_id": "F_error_class_sanity",
        "trigger": "apply_failures_by_error_class",
        "authoritative_surfaces": [
            "setSinkId_error_classes",
        ],
        "deterministic_actions": [
            "not_found_to_fallback_pending_rebind",
            "abort_to_fallback_pending_rebind",
            "not_allowed_to_permission_branch",
        ],
        "expected_state_assertions": [
            "error_branches_non_overlapping",
        ],
        "status": "PASS",
    }


def run_output_route_resilience_sandbox_smoke() -> dict[str, Any]:
    required_checks = {
        "selection_api": OUTPUT_SELECTION_SURFACES["selection_api"] == "MediaDevices.selectAudioOutput",
        "inventory_api": OUTPUT_DEVICE_INVENTORY_AUTHORITY_SURFACE["inventory_api"] == "MediaDevices.enumerateDevices",
        "explicit_grant_path": OUTPUT_VISIBILITY_PATHS["explicit_grant_path"] == "MediaDevices.selectAudioOutput",
        "fallback_preserves_preference": FALLBACK_TO_DEFAULT_RULES_27_4["fallback_preserves_preferred_sink"],
        "reconcile_authoritative_snapshot": OUTPUT_RECONCILE_TRIGGER_MODEL_27_5[
            "enumerate_devices_snapshot_is_authoritative"
        ],
        "stale_boundary_default_not_stale": OUTPUT_STALE_SINK_TRIGGER_BOUNDARIES_27_5[
            "effective_default_empty_string_is_not_stale"
        ],
        "reconcile_routes_to_fallback": OUTPUT_DETERMINISTIC_RECONCILE_FLOW_27_5[
            "effective_stale_routes_to_27_4_fallback"
        ],
        "state_schema_has_rebind_status": "rebind_status" in OUTPUT_ROUTE_STATE_SCHEMA_27_4,
    }

    if not all(required_checks.values()):
        failed = [key for key, ok in required_checks.items() if not ok]
        raise OutputRouteSmokeError(f"Contract dependency precheck failed: {', '.join(failed)}")

    scenarios = [
        _scenario_a_non_default_apply_happy_path(),
        _scenario_b_stale_sink_loss_fallback_default(),
        _scenario_c_passive_rebind_after_return(),
        _scenario_d_interactive_rebind_rotated_id(),
        _scenario_e_explicit_reconcile_without_devicechange(),
        _scenario_f_error_class_sanity(),
    ]

    statuses = [s["status"] for s in scenarios]
    if any(status != "PASS" for status in statuses):
        raise OutputRouteSmokeError("One or more output-route resilience smoke scenarios failed")

    return {
        "overall_status": "PASS",
        "scenarios_total": len(scenarios),
        "scenarios_passed": len([s for s in scenarios if s["status"] == "PASS"]),
        "explicit_reconcile_without_devicechange_supported": True,
        "fallback_preserves_preference": True,
        "apply_failure_classification": APPLY_FAILURE_CLASSIFICATION_RULES_27_4,
        "scenario_ids": OUTPUT_ROUTE_SMOKE_SCENARIO_IDS,
        "scenarios": scenarios,
    }


def main() -> int:
    try:
        proof = run_output_route_resilience_sandbox_smoke()
        print(json.dumps(proof, indent=2, sort_keys=True))
        print(OUTPUT_ROUTE_SMOKE_SUCCESS_MARKER)
        return 0
    except Exception as exc:  # pragma: no cover - smoke entrypoint
        print(f"WebRTC output-route resilience sandbox smoke: FAILED: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

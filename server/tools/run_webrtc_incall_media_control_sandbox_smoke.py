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

from app.webrtc_incall_quality_observability_baseline import (
    LIMITED_AVAILABILITY_NON_GATING_METRICS,
    NON_GATING_LIMITED_METRIC_HANDLING,
    QUALITY_SEVERITY_MAPPING_RULES,
    QUALITY_STATS_SURFACE_BASELINE,
    REQUIRED_QUALITY_METRICS_BY_DOMAIN,
)
from app.webrtc_mute_unmute_source_switch_transceiver_direction_contract import (
    DETERMINISTIC_OPERATION_CASE_ACTIONS,
)
from app.webrtc_sender_parameters_bitrate_codec_boundary_contract import (
    ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES,
    DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS,
)


class InCallMediaControlSmokeError(RuntimeError):
    pass


INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS = (
    "A_user_mute_unmute",
    "B_source_switch_replace_track",
    "C_transceiver_direction_desired_vs_effective",
    "D_sender_parameters_boundary",
    "E_quality_observability_getstats",
    "F_late_controls_after_close",
)

INCALL_MEDIA_CONTROL_SMOKE_SUCCESS_MARKER = "WebRTC in-call media-control sandbox smoke: OK"


@dataclass
class InCallMediaSession:
    session_id: str
    ui_intent: dict[str, bool] = field(
        default_factory=lambda: {
            "audio_user_muted": False,
            "video_user_muted": False,
        }
    )
    track_enabled: dict[str, bool] = field(
        default_factory=lambda: {
            "audio": True,
            "video": True,
        }
    )
    source_muted: dict[str, bool] = field(
        default_factory=lambda: {
            "audio": False,
            "video": False,
        }
    )
    sender_track_binding: str = "camera_front"
    direction_desired: str = "sendrecv"
    direction_effective: str = "sendrecv"
    direction_pending: bool = False
    sender_parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "encodings": [{"active": True, "maxBitrate": 500000}],
            "degradationPreference": "balanced",
        }
    )
    closed: bool = False
    operations: list[str] = field(default_factory=list)

    def set_user_mute(self, kind: str, muted: bool) -> str:
        if self.closed:
            action = "reject_terminal_session_mutation"
            self.operations.append(f"{kind}_user_mute_terminal_reject")
            return action

        if kind not in ("audio", "video"):
            raise InCallMediaControlSmokeError(f"Unsupported mute kind: {kind}")

        key = "audio_user_muted" if kind == "audio" else "video_user_muted"
        self.ui_intent[key] = muted
        self.track_enabled[kind] = not muted

        if kind == "audio":
            action_key = "mic_user_mute_request" if muted else "mic_user_unmute_request"
        else:
            action_key = "camera_user_mute_request" if muted else "camera_user_unmute_request"

        action = DETERMINISTIC_OPERATION_CASE_ACTIONS[action_key]
        self.operations.append(action_key)
        return action

    def set_source_muted(self, kind: str, muted: bool) -> str:
        if kind not in ("audio", "video"):
            raise InCallMediaControlSmokeError(f"Unsupported source mute kind: {kind}")
        self.source_muted[kind] = muted
        action_key = "source_muted_event_observed"
        self.operations.append(action_key)
        return DETERMINISTIC_OPERATION_CASE_ACTIONS[action_key]

    def replace_track(self, new_track_binding: str, *, same_kind: bool = True, late_abort: bool = False) -> str:
        if late_abort:
            action_key = "source_switch_late_abort"
            self.operations.append(action_key)
            return DETERMINISTIC_OPERATION_CASE_ACTIONS[action_key]

        if self.closed:
            action = "reject_terminal_session_mutation"
            self.operations.append("source_switch_terminal_reject")
            return action

        if not same_kind:
            action_key = "source_switch_invalid_kind"
            self.operations.append(action_key)
            return DETERMINISTIC_OPERATION_CASE_ACTIONS[action_key]

        self.sender_track_binding = new_track_binding
        action_key = "source_switch_success"
        self.operations.append(action_key)
        return DETERMINISTIC_OPERATION_CASE_ACTIONS[action_key]

    def request_direction_change(self, direction: str) -> str:
        if self.closed:
            action = "reject_terminal_session_mutation"
            self.operations.append("direction_change_terminal_reject")
            return action

        self.direction_desired = direction
        self.direction_pending = True
        action_key = "direction_change_request"
        self.operations.append(action_key)
        return DETERMINISTIC_OPERATION_CASE_ACTIONS[action_key]

    def complete_direction_change(self, success: bool) -> str:
        if not self.direction_pending:
            raise InCallMediaControlSmokeError("Direction negotiation completion called without pending change")

        if success:
            self.direction_effective = self.direction_desired
            action_key = "direction_change_negotiation_committed"
        else:
            self.direction_desired = self.direction_effective
            action_key = "direction_change_negotiation_failed"

        self.direction_pending = False
        self.operations.append(action_key)
        return DETERMINISTIC_OPERATION_CASE_ACTIONS[action_key]

    def update_sender_parameters(
        self,
        update_class: str,
        value: Any,
        *,
        envelope_ok: bool = True,
        supported: bool = True,
    ) -> dict[str, Any]:
        if self.closed:
            action = DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS["sender_parameter_update_terminal_session"]
            self.operations.append("sender_parameter_update_terminal_session")
            return {"applied": False, "action": action}

        if update_class not in ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES or not supported:
            action = DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS["sender_parameter_update_unsupported"]
            self.operations.append("sender_parameter_update_unsupported")
            return {"applied": False, "action": action}

        if not envelope_ok:
            action = DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS["sender_parameter_update_out_of_envelope"]
            self.operations.append("sender_parameter_update_out_of_envelope")
            return {"applied": False, "action": action}

        if update_class == "bitrate_tuning":
            self.sender_parameters["encodings"][0]["maxBitrate"] = int(value)
        elif update_class == "encoding_activation_toggle":
            self.sender_parameters["encodings"][0]["active"] = bool(value)
        elif update_class == "degradation_preference_update":
            self.sender_parameters["degradationPreference"] = str(value)

        action = DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS["sender_parameter_update_supported"]
        self.operations.append("sender_parameter_update_supported")
        return {"applied": True, "action": action}

    def collect_stats(self, *, include_optional: bool, include_limited: bool) -> dict[str, Any]:
        stat_types = set(QUALITY_STATS_SURFACE_BASELINE["required_stat_types"])
        if include_optional:
            stat_types.update(QUALITY_STATS_SURFACE_BASELINE["optional_stat_types"])

        metrics = {
            "candidate_pair.currentRoundTripTime": 0.18,
            "candidate_pair.availableOutgoingBitrate": 450000,
            "candidate_pair.availableIncomingBitrate": 500000,
            "inbound_rtp.packetsLost": 12,
            "inbound_rtp.packetsReceived": 3800,
            "inbound_rtp.jitter": 0.02,
            "inbound_rtp.bytesReceived": 1250000,
            "outbound_rtp.packetsSent": 5200,
            "outbound_rtp.bytesSent": 2100000,
            "outbound_rtp.framesEncoded": 3600,
            "outbound_rtp.qualityLimitationReason": "none",
            "outbound_rtp.qualityLimitationDurations": {"none": 42.0},
            "inbound_video.framesPerSecond": 25,
            "inbound_video.framesDecoded": 3550,
        }

        if include_limited:
            metrics.update(
                {
                    "inbound_video.freezeCount": 0,
                    "inbound_audio.concealmentEvents": 0,
                    "inbound_audio.audioLevel": 0.12,
                    "remote_inbound_rtp.fractionLost": 0.01,
                }
            )

        return {
            "stat_types": tuple(sorted(stat_types)),
            "metrics": metrics,
        }

    def evaluate_quality(self, stats_payload: dict[str, Any]) -> dict[str, Any]:
        metrics = stats_payload["metrics"]
        indicator_results: dict[str, dict[str, Any]] = {}
        missing_non_gating: list[str] = []
        overall_gating_severity = "healthy"

        for indicator_name, rule in QUALITY_SEVERITY_MAPPING_RULES.items():
            metric_name = str(rule["source_metric"])
            metric_value: Any | None = metrics.get(metric_name)

            if metric_name == "inbound_rtp.packetLossRatio":
                packets_lost = metrics.get("inbound_rtp.packetsLost")
                packets_received = metrics.get("inbound_rtp.packetsReceived")
                if packets_lost is None or packets_received in (None, 0):
                    metric_value = None
                else:
                    metric_value = float(packets_lost) / float(packets_received)

            if metric_value is None:
                if metric_name in LIMITED_AVAILABILITY_NON_GATING_METRICS:
                    missing_non_gating.append(metric_name)
                    indicator_results[indicator_name] = {
                        "status": "unknown_non_gating",
                        "metric": metric_name,
                        "gating": False,
                    }
                    continue
                raise InCallMediaControlSmokeError(f"Missing required metric for indicator {indicator_name}: {metric_name}")

            status = "healthy"
            if "critical_gte" in rule and float(metric_value) >= float(rule["critical_gte"]):
                status = "critical"
            elif "warn_gte" in rule and float(metric_value) >= float(rule["warn_gte"]):
                status = "degraded"
            elif "critical_lte" in rule and float(metric_value) <= float(rule["critical_lte"]):
                status = "critical"
            elif "warn_lte" in rule and float(metric_value) <= float(rule["warn_lte"]):
                status = "degraded"
            elif "critical_delta_gte" in rule and float(metric_value) >= float(rule["critical_delta_gte"]):
                status = "critical"
            elif "warn_delta_gte" in rule and float(metric_value) >= float(rule["warn_delta_gte"]):
                status = "degraded"

            indicator_results[indicator_name] = {
                "status": status,
                "metric": metric_name,
                "value": metric_value,
                "gating": bool(rule["gating"]),
            }

            if rule["gating"]:
                if status == "critical":
                    overall_gating_severity = "critical"
                elif status == "degraded" and overall_gating_severity != "critical":
                    overall_gating_severity = "degraded"

        return {
            "overall_gating_severity": overall_gating_severity,
            "indicator_results": indicator_results,
            "missing_non_gating_metrics": sorted(set(missing_non_gating)),
        }

    def close(self) -> None:
        self.closed = True
        self.direction_pending = False
        self.operations.append("session_closed")


def _scenario_a_user_mute_unmute() -> dict[str, Any]:
    session = InCallMediaSession(session_id="scenario-a")

    action_mute = session.set_user_mute("audio", True)
    if action_mute != DETERMINISTIC_OPERATION_CASE_ACTIONS["mic_user_mute_request"]:
        raise InCallMediaControlSmokeError("Scenario A mute action mismatch")
    if session.track_enabled["audio"] is not False:
        raise InCallMediaControlSmokeError("Scenario A: audio track must be disabled after user mute")

    source_action = session.set_source_muted("audio", True)
    if source_action != DETERMINISTIC_OPERATION_CASE_ACTIONS["source_muted_event_observed"]:
        raise InCallMediaControlSmokeError("Scenario A source mute action mismatch")
    if session.ui_intent["audio_user_muted"] is not True:
        raise InCallMediaControlSmokeError("Scenario A: source mute must not override user mute intent")

    action_unmute = session.set_user_mute("audio", False)
    if action_unmute != DETERMINISTIC_OPERATION_CASE_ACTIONS["mic_user_unmute_request"]:
        raise InCallMediaControlSmokeError("Scenario A unmute action mismatch")
    if session.track_enabled["audio"] is not True:
        raise InCallMediaControlSmokeError("Scenario A: audio track must be enabled after user unmute")

    return {
        "scenario_id": "A_user_mute_unmute",
        "operations": list(session.operations),
        "deterministic_actions": [action_mute, source_action, action_unmute],
        "expected_contract_assertions": {
            "user_mute_uses_track_enabled": True,
            "user_mute_not_equal_source_mute": True,
        },
        "status": "PASS",
    }


def _scenario_b_source_switch() -> dict[str, Any]:
    session = InCallMediaSession(session_id="scenario-b")
    initial_binding = session.sender_track_binding

    action_success = session.replace_track("camera_rear", same_kind=True)
    if action_success != DETERMINISTIC_OPERATION_CASE_ACTIONS["source_switch_success"]:
        raise InCallMediaControlSmokeError("Scenario B success action mismatch")
    if session.sender_track_binding != "camera_rear":
        raise InCallMediaControlSmokeError("Scenario B: sender binding must switch to camera_rear")

    action_invalid = session.replace_track("screen_capture", same_kind=False)
    if action_invalid != DETERMINISTIC_OPERATION_CASE_ACTIONS["source_switch_invalid_kind"]:
        raise InCallMediaControlSmokeError("Scenario B invalid-kind action mismatch")
    if session.sender_track_binding != "camera_rear":
        raise InCallMediaControlSmokeError("Scenario B: invalid-kind switch must not mutate sender binding")

    action_late_abort = session.replace_track("camera_virtual", late_abort=True)
    if action_late_abort != DETERMINISTIC_OPERATION_CASE_ACTIONS["source_switch_late_abort"]:
        raise InCallMediaControlSmokeError("Scenario B late-abort action mismatch")
    if session.sender_track_binding != "camera_rear":
        raise InCallMediaControlSmokeError("Scenario B: late-abort must not mutate sender binding")

    return {
        "scenario_id": "B_source_switch_replace_track",
        "operations": list(session.operations),
        "deterministic_actions": [action_success, action_invalid, action_late_abort],
        "expected_contract_assertions": {
            "replace_track_authoritative": True,
            "invalid_kind_rejected": True,
            "late_abort_non_mutating": True,
            "initial_binding": initial_binding,
        },
        "status": "PASS",
    }


def _scenario_c_direction_change() -> dict[str, Any]:
    session = InCallMediaSession(session_id="scenario-c")

    action_request = session.request_direction_change("sendonly")
    if action_request != DETERMINISTIC_OPERATION_CASE_ACTIONS["direction_change_request"]:
        raise InCallMediaControlSmokeError("Scenario C request action mismatch")
    if session.direction_desired != "sendonly" or session.direction_effective != "sendrecv":
        raise InCallMediaControlSmokeError("Scenario C: desired/effective direction distinction broken")

    action_commit = session.complete_direction_change(success=True)
    if action_commit != DETERMINISTIC_OPERATION_CASE_ACTIONS["direction_change_negotiation_committed"]:
        raise InCallMediaControlSmokeError("Scenario C commit action mismatch")
    if session.direction_effective != "sendonly":
        raise InCallMediaControlSmokeError("Scenario C: effective direction must update after commit")

    session.request_direction_change("recvonly")
    action_rollback = session.complete_direction_change(success=False)
    if action_rollback != DETERMINISTIC_OPERATION_CASE_ACTIONS["direction_change_negotiation_failed"]:
        raise InCallMediaControlSmokeError("Scenario C rollback action mismatch")
    if session.direction_desired != session.direction_effective:
        raise InCallMediaControlSmokeError("Scenario C: failed direction change must rollback desired state")

    return {
        "scenario_id": "C_transceiver_direction_desired_vs_effective",
        "operations": list(session.operations),
        "deterministic_actions": [action_request, action_commit, action_rollback],
        "expected_contract_assertions": {
            "direction_currentDirection_distinct": True,
            "negotiation_commit_required_for_effective_change": True,
        },
        "status": "PASS",
    }


def _scenario_d_sender_parameter_boundary() -> dict[str, Any]:
    session = InCallMediaSession(session_id="scenario-d")

    result_supported = session.update_sender_parameters("bitrate_tuning", 320000)
    if result_supported["applied"] is not True:
        raise InCallMediaControlSmokeError("Scenario D: supported sender update must apply")
    if session.sender_parameters["encodings"][0]["maxBitrate"] != 320000:
        raise InCallMediaControlSmokeError("Scenario D: bitrate_tuning must update maxBitrate")

    result_unsupported = session.update_sender_parameters("codec_change_runtime", {"codec": "vp9"}, supported=False)
    if result_unsupported["action"] != DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS["sender_parameter_update_unsupported"]:
        raise InCallMediaControlSmokeError("Scenario D: unsupported sender update action mismatch")

    result_out_of_envelope = session.update_sender_parameters(
        "degradation_preference_update",
        "maintain-framerate",
        envelope_ok=False,
    )
    if result_out_of_envelope["action"] != DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS[
        "sender_parameter_update_out_of_envelope"
    ]:
        raise InCallMediaControlSmokeError("Scenario D: out-of-envelope action mismatch")

    session.close()
    result_terminal = session.update_sender_parameters("encoding_activation_toggle", False)
    if result_terminal["action"] != DETERMINISTIC_SENDER_PARAMETER_CASE_ACTIONS[
        "sender_parameter_update_terminal_session"
    ]:
        raise InCallMediaControlSmokeError("Scenario D: terminal update action mismatch")

    return {
        "scenario_id": "D_sender_parameters_boundary",
        "operations": list(session.operations),
        "deterministic_actions": [
            result_supported["action"],
            result_unsupported["action"],
            result_out_of_envelope["action"],
            result_terminal["action"],
        ],
        "expected_contract_assertions": {
            "sender_update_surface": "RTCRtpSender.getParameters/setParameters",
            "supported_update_applied": True,
            "unsupported_and_out_of_envelope_rejected": True,
            "terminal_session_rejects_mutation": True,
        },
        "status": "PASS",
    }


def _scenario_e_quality_observability() -> dict[str, Any]:
    session = InCallMediaSession(session_id="scenario-e")
    stats_payload = session.collect_stats(include_optional=True, include_limited=False)

    required_types = set(QUALITY_STATS_SURFACE_BASELINE["required_stat_types"])
    observed_types = set(stats_payload["stat_types"])
    if not required_types.issubset(observed_types):
        raise InCallMediaControlSmokeError("Scenario E: required stat types missing in getStats payload")

    required_metrics = {
        metric
        for metric_group in REQUIRED_QUALITY_METRICS_BY_DOMAIN.values()
        for metric in metric_group
    }
    missing_required = sorted(metric for metric in required_metrics if metric not in stats_payload["metrics"])
    if missing_required:
        raise InCallMediaControlSmokeError(f"Scenario E: missing required metrics: {missing_required}")

    quality_result = session.evaluate_quality(stats_payload)

    if NON_GATING_LIMITED_METRIC_HANDLING["optional_metrics_must_not_block_baseline_pass"] is not True:
        raise InCallMediaControlSmokeError("Scenario E: optional metric handling contract violation")

    expected_missing = sorted(
        metric
        for metric in (
            QUALITY_SEVERITY_MAPPING_RULES["video_freeze_count_delta"]["source_metric"],
            QUALITY_SEVERITY_MAPPING_RULES["audio_concealment_events_delta"]["source_metric"],
        )
        if metric not in stats_payload["metrics"]
    )
    if sorted(quality_result["missing_non_gating_metrics"]) != expected_missing:
        raise InCallMediaControlSmokeError("Scenario E: non-gating missing metric classification mismatch")

    indicator_results = quality_result["indicator_results"]
    if indicator_results["video_freeze_count_delta"]["status"] != "unknown_non_gating":
        raise InCallMediaControlSmokeError("Scenario E: video freeze missing metric must be unknown_non_gating")
    if indicator_results["audio_concealment_events_delta"]["status"] != "unknown_non_gating":
        raise InCallMediaControlSmokeError("Scenario E: audio concealment missing metric must be unknown_non_gating")

    return {
        "scenario_id": "E_quality_observability_getstats",
        "operations": list(session.operations),
        "deterministic_actions": ["collect_getstats", "evaluate_quality_severity"],
        "expected_contract_assertions": {
            "required_stat_types_present": True,
            "required_metrics_present": True,
            "limited_metrics_non_gating": True,
            "overall_gating_severity": quality_result["overall_gating_severity"],
        },
        "non_gating_missing_metrics": quality_result["missing_non_gating_metrics"],
        "status": "PASS",
    }


def _scenario_f_closed_session_late_controls() -> dict[str, Any]:
    session = InCallMediaSession(session_id="scenario-f")
    session.close()

    action_switch_after_close = session.replace_track("camera_rear")
    action_mute_after_close = session.set_user_mute("video", True)
    terminal_param_result = session.update_sender_parameters("encoding_activation_toggle", False)

    if action_switch_after_close != "reject_terminal_session_mutation":
        raise InCallMediaControlSmokeError("Scenario F: source-switch after close must be terminal reject")
    if action_mute_after_close != "reject_terminal_session_mutation":
        raise InCallMediaControlSmokeError("Scenario F: mute after close must be terminal reject")
    if terminal_param_result["applied"] is not False:
        raise InCallMediaControlSmokeError("Scenario F: sender update after close must not apply")

    return {
        "scenario_id": "F_late_controls_after_close",
        "operations": list(session.operations),
        "deterministic_actions": [
            action_switch_after_close,
            action_mute_after_close,
            terminal_param_result["action"],
        ],
        "expected_contract_assertions": {
            "closed_session_rejects_media_mutation": True,
            "state_integrity_preserved": True,
        },
        "status": "PASS",
    }


def run_webrtc_incall_media_control_sandbox_smoke(*, return_proof: bool = False) -> int | dict[str, Any]:
    scenarios = [
        _scenario_a_user_mute_unmute(),
        _scenario_b_source_switch(),
        _scenario_c_direction_change(),
        _scenario_d_sender_parameter_boundary(),
        _scenario_e_quality_observability(),
        _scenario_f_closed_session_late_controls(),
    ]

    proof = {
        "overall_status": "PASS",
        "scenarios_passed": len(scenarios),
        "scenarios_total": len(scenarios),
        "scenario_ids": INCALL_MEDIA_CONTROL_SMOKE_SCENARIO_IDS,
        "required_stat_types": QUALITY_STATS_SURFACE_BASELINE["required_stat_types"],
        "non_gating_missing_metrics": sorted(LIMITED_AVAILABILITY_NON_GATING_METRICS),
        "scenarios": scenarios,
    }

    print("WebRTC in-call media-control sandbox smoke proof:")
    print(json.dumps(proof, ensure_ascii=True, sort_keys=True, indent=2))
    print(INCALL_MEDIA_CONTROL_SMOKE_SUCCESS_MARKER)

    if return_proof:
        return proof
    return 0


def main() -> int:
    try:
        return run_webrtc_incall_media_control_sandbox_smoke()
    except InCallMediaControlSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"WebRTC in-call media-control sandbox smoke: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - runtime harness
        print(f"WebRTC in-call media-control sandbox smoke: FAILED (unexpected) - {exc!r}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations


QUALITY_STATS_SURFACE_BASELINE = {
    "stats_source": "RTCPeerConnection.getStats",
    "required_stat_types": (
        "candidate-pair",
        "outbound-rtp",
        "inbound-rtp",
    ),
    "optional_stat_types": (
        "remote-inbound-rtp",
    ),
}

REQUIRED_QUALITY_METRICS_BY_DOMAIN = {
    "network_transport": (
        "candidate_pair.currentRoundTripTime",
        "candidate_pair.availableOutgoingBitrate",
        "candidate_pair.availableIncomingBitrate",
    ),
    "inbound_media_core": (
        "inbound_rtp.packetsLost",
        "inbound_rtp.jitter",
        "inbound_rtp.bytesReceived",
    ),
    "outbound_media_core": (
        "outbound_rtp.packetsSent",
        "outbound_rtp.bytesSent",
        "outbound_rtp.framesEncoded",
    ),
}

OPTIONAL_ENRICHMENT_METRICS = (
    "inbound_video.framesPerSecond",
    "inbound_video.framesDecoded",
    "inbound_video.freezeCount",
    "inbound_audio.concealmentEvents",
    "inbound_audio.audioLevel",
    "outbound_rtp.qualityLimitationReason",
    "outbound_rtp.qualityLimitationDurations",
    "remote_inbound_rtp.fractionLost",
)

LIMITED_AVAILABILITY_NON_GATING_METRICS = (
    "inbound_video.freezeCount",
    "inbound_audio.concealmentEvents",
    "inbound_audio.audioLevel",
    "remote_inbound_rtp.fractionLost",
)

QUALITY_SAMPLING_CADENCE_POLICY = {
    "canonical_sampling_interval_ms": 5000,
    "runtime_polling_interval_bounds_ms": (2000, 10000),
    "rolling_window_samples": 6,
    "trend_metrics_use_window_or_delta": True,
    "single_sample_not_authoritative_for_trend_metrics": True,
    "stats_cache_throttling_awareness_required": True,
}

QUALITY_SEVERITY_MAPPING_RULES = {
    "latency_rtt_seconds": {
        "source_metric": "candidate_pair.currentRoundTripTime",
        "warn_gte": 0.2,
        "critical_gte": 0.4,
        "gating": True,
        "evaluation_mode": "rolling_window",
    },
    "packet_loss_ratio": {
        "source_metric": "inbound_rtp.packetLossRatio",
        "derived_from": (
            "inbound_rtp.packetsLost",
            "inbound_rtp.packetsReceived",
        ),
        "warn_gte": 0.03,
        "critical_gte": 0.08,
        "gating": True,
        "evaluation_mode": "rolling_window",
    },
    "jitter_seconds": {
        "source_metric": "inbound_rtp.jitter",
        "warn_gte": 0.03,
        "critical_gte": 0.07,
        "gating": True,
        "evaluation_mode": "rolling_window",
    },
    "available_outgoing_bitrate_bps": {
        "source_metric": "candidate_pair.availableOutgoingBitrate",
        "warn_lte": 300000,
        "critical_lte": 120000,
        "gating": True,
        "evaluation_mode": "rolling_window",
    },
    "available_incoming_bitrate_bps": {
        "source_metric": "candidate_pair.availableIncomingBitrate",
        "warn_lte": 300000,
        "critical_lte": 120000,
        "gating": True,
        "evaluation_mode": "rolling_window",
    },
    "video_freeze_count_delta": {
        "source_metric": "inbound_video.freezeCount",
        "warn_delta_gte": 1,
        "critical_delta_gte": 3,
        "gating": False,
        "evaluation_mode": "delta_window",
    },
    "audio_concealment_events_delta": {
        "source_metric": "inbound_audio.concealmentEvents",
        "warn_delta_gte": 5,
        "critical_delta_gte": 20,
        "gating": False,
        "evaluation_mode": "delta_window",
    },
}

NON_GATING_LIMITED_METRIC_HANDLING = {
    "missing_limited_metric_action": "mark_unknown_non_gating_and_continue",
    "missing_required_metric_action": "contract_breach",
    "optional_metrics_must_not_block_baseline_pass": True,
    "non_gating_classification_must_be_explicit": True,
}

INCALL_QUALITY_OBSERVABILITY_INVARIANTS = {
    "canonical_stats_source_is_getstats": True,
    "required_metrics_map_to_required_stat_types": True,
    "limited_availability_metrics_non_gating": True,
    "severity_mapping_covers_latency_loss_jitter_bitrate_video_freeze_audio_concealment": True,
    "sampling_and_window_semantics_explicit": True,
    "production_runtime_change_allowed_in_25_5": False,
}


def validate_webrtc_incall_quality_observability_baseline() -> list[str]:
    errors: list[str] = []

    from app.webrtc_incall_media_control_quality_observability_baseline import (
        QUALITY_OBSERVABILITY_SURFACE,
        STAGE25_SUBSTEP_DRAFT,
    )
    from app.webrtc_media_control_state_inventory import (
        ALLOWED_STATE_RELATIONS,
        MEDIA_CONTROL_STATE_INVENTORY_BASELINE,
    )
    from app.webrtc_sender_parameters_bitrate_codec_boundary_contract import (
        ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES,
    )

    if STAGE25_SUBSTEP_DRAFT.get("25.5") != "incall_quality_observability_baseline":
        errors.append("Stage 25.1 substep draft must define 25.5 observability milestone")

    required_surface = {
        "stats_source": "RTCPeerConnection.getStats",
        "required_stat_types": (
            "candidate-pair",
            "outbound-rtp",
            "inbound-rtp",
        ),
        "optional_stat_types": (
            "remote-inbound-rtp",
        ),
    }
    if QUALITY_STATS_SURFACE_BASELINE != required_surface:
        errors.append("QUALITY_STATS_SURFACE_BASELINE must match canonical stats surface baseline")

    required_metric_domains = {
        "network_transport",
        "inbound_media_core",
        "outbound_media_core",
    }
    if set(REQUIRED_QUALITY_METRICS_BY_DOMAIN.keys()) != required_metric_domains:
        errors.append("REQUIRED_QUALITY_METRICS_BY_DOMAIN must define canonical metric domains")

    for domain_name, metrics in REQUIRED_QUALITY_METRICS_BY_DOMAIN.items():
        if not metrics:
            errors.append(f"{domain_name}: required metric domain must be non-empty")

    required_flat_metrics = {
        metric
        for metric_group in REQUIRED_QUALITY_METRICS_BY_DOMAIN.values()
        for metric in metric_group
    }

    expected_required_from_25_1 = set(QUALITY_OBSERVABILITY_SURFACE.get("required_metrics", ()))
    if required_flat_metrics != expected_required_from_25_1:
        errors.append("25.5 required metric set must align exactly with 25.1 required_metrics")

    if QUALITY_STATS_SURFACE_BASELINE["stats_source"] != QUALITY_OBSERVABILITY_SURFACE.get("stats_source"):
        errors.append("25.5 stats_source must align with 25.1 QUALITY_OBSERVABILITY_SURFACE")

    if QUALITY_STATS_SURFACE_BASELINE["required_stat_types"] != QUALITY_OBSERVABILITY_SURFACE.get("required_stat_types"):
        errors.append("25.5 required_stat_types must align with 25.1 QUALITY_OBSERVABILITY_SURFACE")

    if not OPTIONAL_ENRICHMENT_METRICS:
        errors.append("OPTIONAL_ENRICHMENT_METRICS must be non-empty")

    limited_metrics_set = set(LIMITED_AVAILABILITY_NON_GATING_METRICS)
    optional_metrics_set = set(OPTIONAL_ENRICHMENT_METRICS)
    if not limited_metrics_set.issubset(optional_metrics_set):
        errors.append("LIMITED_AVAILABILITY_NON_GATING_METRICS must be a subset of OPTIONAL_ENRICHMENT_METRICS")

    required_sampling_policy = {
        "canonical_sampling_interval_ms": 5000,
        "runtime_polling_interval_bounds_ms": (2000, 10000),
        "rolling_window_samples": 6,
        "trend_metrics_use_window_or_delta": True,
        "single_sample_not_authoritative_for_trend_metrics": True,
        "stats_cache_throttling_awareness_required": True,
    }
    if QUALITY_SAMPLING_CADENCE_POLICY != required_sampling_policy:
        errors.append("QUALITY_SAMPLING_CADENCE_POLICY must match canonical sampling policy")

    if QUALITY_SAMPLING_CADENCE_POLICY["runtime_polling_interval_bounds_ms"][0] > QUALITY_SAMPLING_CADENCE_POLICY[
        "runtime_polling_interval_bounds_ms"
    ][1]:
        errors.append("runtime_polling_interval_bounds_ms must be ordered as (min, max)")

    required_indicator_set = {
        "latency_rtt_seconds",
        "packet_loss_ratio",
        "jitter_seconds",
        "available_outgoing_bitrate_bps",
        "available_incoming_bitrate_bps",
        "video_freeze_count_delta",
        "audio_concealment_events_delta",
    }
    if set(QUALITY_SEVERITY_MAPPING_RULES.keys()) != required_indicator_set:
        errors.append("QUALITY_SEVERITY_MAPPING_RULES must define canonical indicator set")

    for indicator_name, rule in QUALITY_SEVERITY_MAPPING_RULES.items():
        if not rule.get("source_metric"):
            errors.append(f"{indicator_name}: source_metric is required")
        if not rule.get("evaluation_mode"):
            errors.append(f"{indicator_name}: evaluation_mode is required")
        if "gating" not in rule:
            errors.append(f"{indicator_name}: gating flag is required")

        threshold_gte_present = "warn_gte" in rule and "critical_gte" in rule
        threshold_lte_present = "warn_lte" in rule and "critical_lte" in rule
        threshold_delta_present = "warn_delta_gte" in rule and "critical_delta_gte" in rule

        if not (threshold_gte_present or threshold_lte_present or threshold_delta_present):
            errors.append(f"{indicator_name}: threshold pair is required")

    non_gating_sources = {
        QUALITY_SEVERITY_MAPPING_RULES["video_freeze_count_delta"]["source_metric"],
        QUALITY_SEVERITY_MAPPING_RULES["audio_concealment_events_delta"]["source_metric"],
    }
    if not non_gating_sources.issubset(limited_metrics_set):
        errors.append("video_freeze/audio_concealment indicators must map to limited non-gating metrics")

    if QUALITY_SEVERITY_MAPPING_RULES["video_freeze_count_delta"]["gating"] is not False:
        errors.append("video_freeze_count_delta must be non-gating")
    if QUALITY_SEVERITY_MAPPING_RULES["audio_concealment_events_delta"]["gating"] is not False:
        errors.append("audio_concealment_events_delta must be non-gating")

    required_non_gating_handling = {
        "missing_limited_metric_action": "mark_unknown_non_gating_and_continue",
        "missing_required_metric_action": "contract_breach",
        "optional_metrics_must_not_block_baseline_pass": True,
        "non_gating_classification_must_be_explicit": True,
    }
    if NON_GATING_LIMITED_METRIC_HANDLING != required_non_gating_handling:
        errors.append("NON_GATING_LIMITED_METRIC_HANDLING must match canonical handling contract")

    required_invariants = {
        "canonical_stats_source_is_getstats": True,
        "required_metrics_map_to_required_stat_types": True,
        "limited_availability_metrics_non_gating": True,
        "severity_mapping_covers_latency_loss_jitter_bitrate_video_freeze_audio_concealment": True,
        "sampling_and_window_semantics_explicit": True,
        "production_runtime_change_allowed_in_25_5": False,
    }
    if INCALL_QUALITY_OBSERVABILITY_INVARIANTS != required_invariants:
        errors.append("INCALL_QUALITY_OBSERVABILITY_INVARIANTS must match canonical invariant set")

    # Cross-check against Step 25.2 observability ownership and boundaries.
    quality_surface = MEDIA_CONTROL_STATE_INVENTORY_BASELINE.get("quality_stats_surface")
    if quality_surface is None:
        errors.append("Step 25.2 must define quality_stats_surface")
    else:
        if quality_surface.ownership_domain != "observability_owner":
            errors.append("quality_stats_surface ownership_domain must remain observability_owner")
        if quality_surface.observable_only is not True:
            errors.append("quality_stats_surface must remain observable_only")

    if ALLOWED_STATE_RELATIONS.get("stats_surface_is_observability_only") is not True:
        errors.append("Step 25.2 must preserve stats_surface_is_observability_only relation")

    # Cross-check against Step 25.4 sender boundary contract.
    bitrate_update_class = ALLOWED_RUNTIME_PARAMETER_UPDATE_CLASSES.get("bitrate_tuning")
    if bitrate_update_class is None:
        errors.append("Step 25.4 must define bitrate_tuning update class")
    else:
        if bitrate_update_class.get("parameter_path") != "encodings[].maxBitrate":
            errors.append("Step 25.4 bitrate_tuning parameter path must remain encodings[].maxBitrate")

    return errors

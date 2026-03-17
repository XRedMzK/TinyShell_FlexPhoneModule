from __future__ import annotations

import json
import logging
import uuid

from fastapi.testclient import TestClient
import pytest

from app import main
from app.auth_challenge_store import InMemoryAuthChallengeStore
from app.calls import InMemoryCallRegistry
from app.main import app, registered_devices, settings
from app.observability import observability
from app.operational_logging import clear_request_context, log_event, set_request_context
from app.signaling import InMemorySignalingHub
from app.tracing import shutdown_tracing


@pytest.fixture(autouse=True)
def reset_runtime_state(monkeypatch: pytest.MonkeyPatch) -> None:
    registered_devices.clear()
    observability.reset()
    monkeypatch.setattr(main, "auth_challenge_store", InMemoryAuthChallengeStore())
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    monkeypatch.setattr(settings, "otel_exporter", "none")
    yield
    registered_devices.clear()
    observability.reset()
    shutdown_tracing()


def _log_records(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    return [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "flexphone.ops"
    ]


def test_runtime_ready_degraded_emits_structured_log_with_request_id(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="flexphone.ops")
    monkeypatch.setattr(
        main,
        "_collect_runtime_readiness_checks",
        lambda: {
            "auth_challenge_redis": "unavailable",
            "signaling_redis": "ok",
            "otel_exporter": "none",
        },
    )

    with TestClient(app) as client:
        response = client.get("/ready", headers={"x-request-id": "req-ready-1"})

    assert response.status_code == 503
    entries = _log_records(caplog)
    ready_log = next(item for item in entries if item.get("event") == "runtime.ready.degraded")
    assert ready_log["request_id"] == "req-ready-1"
    assert ready_log["reason_code"] == "dependency_degraded"
    assert ready_log["reason_class"] == "dependency"
    assert ready_log["auth_challenge_redis"] == "unavailable"
    assert ready_log["trace_id"] is None or len(str(ready_log["trace_id"])) == 32


def test_auth_verify_failed_log_contains_trace_and_span_when_tracing_enabled(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="flexphone.ops")
    monkeypatch.setattr(settings, "otel_exporter", "console")

    with TestClient(app) as client:
        response = client.post(
            "/auth/verify",
            json={
                "challenge_id": str(uuid.uuid4()),
                "nickname": "@ghost",
                "device_id": "a" * 64,
                "signature": "ZmFrZV9zaWc",
            },
        )

    assert response.status_code == 404
    entries = _log_records(caplog)
    verify_log = next(item for item in entries if item.get("event") == "auth.verify.failed")
    assert verify_log["reason_code"] == "challenge_not_found"
    assert verify_log["reason_class"] == "security"
    assert isinstance(verify_log["trace_id"], str) and len(verify_log["trace_id"]) == 32
    assert isinstance(verify_log["span_id"], str) and len(verify_log["span_id"]) == 16


def test_sensitive_fields_are_redacted_in_operational_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="flexphone.ops")
    set_request_context(request_id="req-redact-1", route="/unit", method="TEST")
    try:
        log_event(
            level="INFO",
            event="unit.redaction",
            message="unit redaction check",
            service="flexphone-test",
            env="test",
            component="unit",
            reason_code="ok",
            access_token="plain-token",
            password="p@ssw0rd",
            token="another-token",
        )
    finally:
        clear_request_context()

    entries = _log_records(caplog)
    redaction_log = next(item for item in entries if item.get("event") == "unit.redaction")
    assert redaction_log["reason_class"] == "operational"
    assert redaction_log["access_token"] == "***redacted***"
    assert redaction_log["password"] == "***redacted***"
    assert redaction_log["token"] == "***redacted***"

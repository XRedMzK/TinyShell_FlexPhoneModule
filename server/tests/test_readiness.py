from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app import main
from app.auth_challenge_store import InMemoryAuthChallengeStore
from app.calls import InMemoryCallRegistry
from app.main import app, registered_devices
from app.observability import observability
from app.signaling import InMemorySignalingHub


@pytest.fixture(autouse=True)
def reset_runtime_state(monkeypatch: pytest.MonkeyPatch) -> None:
    registered_devices.clear()
    observability.reset()
    monkeypatch.setattr(main, "auth_challenge_store", InMemoryAuthChallengeStore())
    monkeypatch.setattr(main, "registry", InMemoryCallRegistry())
    monkeypatch.setattr(main, "hub", InMemorySignalingHub())
    yield
    registered_devices.clear()
    observability.reset()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_ready_returns_ok_when_runtime_dependencies_are_available(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main,
        "_collect_runtime_readiness_checks",
        lambda: {
            "auth_challenge_redis": "ok",
            "signaling_redis": "ok",
            "otel_exporter": "none",
        },
    )

    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checks"]["auth_challenge_redis"] == "ok"
    assert payload["checks"]["signaling_redis"] == "ok"
    assert observability.snapshot()["counters"]["ready.ok"] >= 1


def test_ready_returns_503_when_runtime_dependencies_are_degraded(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main,
        "_collect_runtime_readiness_checks",
        lambda: {
            "auth_challenge_redis": "unavailable",
            "signaling_redis": "ok",
            "otel_exporter": "otlp",
        },
    )

    response = client.get("/ready")
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["auth_challenge_redis"] == "unavailable"
    assert observability.snapshot()["counters"]["ready.degraded"] >= 1

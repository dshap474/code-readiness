from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from code_readiness_template.app import create_app
from code_readiness_template.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()


def test_create_app_exposes_runtime_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_RELEASE", "unit-test")
    monkeypatch.setattr("code_readiness_template.app.ping_database", lambda settings: None)

    with TestClient(create_app()) as client:
        health = client.get("/healthz", headers={"x-request-id": "health-request"})
        ready = client.get("/readyz")
        metrics = client.get("/metrics")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "alive", "release": "unit-test"}
    assert health.headers["x-request-id"] == "health-request"
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok", "database": "ready", "release": "unit-test"}
    assert metrics.status_code == 200
    assert "code_readiness_http_requests_total" in metrics.text


def test_readyz_returns_503_when_database_ping_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_RELEASE", "unit-test")

    def fail(_settings: Any) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr("code_readiness_template.app.ping_database", fail)

    with TestClient(create_app()) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database not ready."}

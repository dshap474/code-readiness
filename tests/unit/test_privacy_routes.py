from __future__ import annotations

from fastapi.testclient import TestClient

from code_readiness_template.app import create_app
from code_readiness_template.config import get_settings


def test_privacy_retention_route_reports_policy(monkeypatch) -> None:
    monkeypatch.setenv("PRIVACY_CONTACT_EMAIL", "privacy@example.com")
    monkeypatch.setenv("PRIVACY_DATA_RETENTION_DAYS", "45")
    monkeypatch.setenv("PRIVACY_EXPORT_ENABLED", "true")
    monkeypatch.setenv("PRIVACY_DELETE_ENABLED", "true")
    get_settings.cache_clear()

    client = TestClient(create_app())
    response = client.get("/privacy/retention")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "action": "retention",
        "retention_days": 45,
        "contact_email": "privacy@example.com",
    }


def test_privacy_export_route_honors_disable_flag(monkeypatch) -> None:
    monkeypatch.setenv("PRIVACY_CONTACT_EMAIL", "privacy@example.com")
    monkeypatch.setenv("PRIVACY_DATA_RETENTION_DAYS", "45")
    monkeypatch.setenv("PRIVACY_EXPORT_ENABLED", "false")
    monkeypatch.setenv("PRIVACY_DELETE_ENABLED", "true")
    get_settings.cache_clear()

    client = TestClient(create_app())
    response = client.post("/privacy/export")

    assert response.status_code == 503
    assert response.json()["detail"] == "Privacy export workflow is temporarily disabled."


def test_privacy_delete_route_returns_contact_details(monkeypatch) -> None:
    monkeypatch.setenv("PRIVACY_CONTACT_EMAIL", "privacy@example.com")
    monkeypatch.setenv("PRIVACY_DATA_RETENTION_DAYS", "14")
    monkeypatch.setenv("PRIVACY_EXPORT_ENABLED", "true")
    monkeypatch.setenv("PRIVACY_DELETE_ENABLED", "true")
    get_settings.cache_clear()

    client = TestClient(create_app())
    response = client.post("/privacy/delete")

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "action": "delete",
        "retention_days": 14,
        "contact_email": "privacy@example.com",
    }

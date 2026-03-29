from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from code_readiness_template.config import get_settings
from code_readiness_template.db import get_engine
from code_readiness_template.features.widgets import Widget


@pytest.mark.integration
def test_create_and_fetch_widget(client: TestClient) -> None:
    create_response = client.post("/api/v1/widgets", json={"name": "Launch Widget"})
    assert create_response.status_code == 201
    widget_id = create_response.json()["id"]

    fetch_response = client.get(f"/api/v1/widgets/{widget_id}")
    assert fetch_response.status_code == 200
    assert fetch_response.json()["slug"] == "launch-widget"


@pytest.mark.integration
def test_list_widgets_uses_single_query(client: TestClient, session_factory) -> None:
    with session_factory() as session:
        session.add_all(
            [
                Widget(name="Alpha Widget", slug="alpha-widget"),
                Widget(name="Beta Widget", slug="beta-widget"),
            ]
        )
        session.commit()

    settings = get_settings()
    engine = get_engine(settings.database_url)
    query_count = 0

    def before_cursor_execute(*args) -> None:
        nonlocal query_count
        query_count += 1

    listener: Callable[..., None] = before_cursor_execute
    event.listen(engine, "before_cursor_execute", listener)
    try:
        response = client.get("/api/v1/widgets")
    finally:
        event.remove(engine, "before_cursor_execute", listener)

    assert response.status_code == 200
    assert len(response.json()) >= 2
    assert query_count == 1


@pytest.mark.integration
def test_healthcheck_confirms_database(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "alive", "release": "test-suite"}


@pytest.mark.integration
def test_readycheck_confirms_database(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ready", "release": "test-suite"}


@pytest.mark.integration
def test_metrics_endpoint_exposes_runtime_metrics(client: TestClient) -> None:
    client.get("/healthz")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "code_readiness_http_requests_total" in response.text
    assert "code_readiness_widget_actions_total" in response.text


@pytest.mark.integration
def test_request_id_header_is_echoed(client: TestClient) -> None:
    response = client.get("/healthz", headers={"x-request-id": "integration-request-id"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "integration-request-id"


@pytest.mark.integration
def test_widget_routes_emit_product_events(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[tuple[str, dict[str, Any]]] = []

    def record_event(event_name: str, **kwargs: Any) -> None:
        captured.append((event_name, kwargs))

    monkeypatch.setattr("code_readiness_template.features.widgets.emit_product_event", record_event)

    create_response = client.post("/api/v1/widgets", json={"name": "Telemetry Widget"})
    widget_id = create_response.json()["id"]
    client.get("/api/v1/widgets")
    client.get(f"/api/v1/widgets/{widget_id}")

    assert [event_name for event_name, _ in captured] == [
        "widget_created",
        "widget_list_viewed",
        "widget_detail_viewed",
    ]


@pytest.mark.integration
def test_widget_detail_route_uses_single_query(client: TestClient) -> None:
    create_response = client.post("/api/v1/widgets", json={"name": "Detail Widget"})
    widget_id = create_response.json()["id"]

    settings = get_settings()
    engine = get_engine(settings.database_url)
    query_count = 0

    def before_cursor_execute(*args) -> None:
        nonlocal query_count
        query_count += 1

    listener: Callable[..., None] = before_cursor_execute
    event.listen(engine, "before_cursor_execute", listener)
    try:
        response = client.get(f"/api/v1/widgets/{widget_id}")
    finally:
        event.remove(engine, "before_cursor_execute", listener)

    assert response.status_code == 200
    assert response.json()["id"] == widget_id
    assert query_count == 1

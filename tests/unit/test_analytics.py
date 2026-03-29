from __future__ import annotations

from typing import Any

import httpx
import pytest

from code_readiness_template.analytics import (
    CIRCUIT_BREAKER_STATE,
    emit_product_event,
    reset_analytics_circuit_breaker,
)
from code_readiness_template.config import Settings


@pytest.fixture(autouse=True)
def reset_breaker_state() -> None:
    reset_analytics_circuit_breaker()


def test_emit_product_event_skips_posthog_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, Any]] = []

    def record_info(_message: str, *, extra: dict[str, Any]) -> None:
        captured.append(extra)

    def fail_post(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("httpx.post should not be called without a PostHog key.")

    monkeypatch.setattr("code_readiness_template.analytics.LOGGER.info", record_info)
    monkeypatch.setattr("code_readiness_template.analytics.httpx.post", fail_post)

    settings = Settings(app_env="test", app_release="unit-test", posthog_api_key=None)
    emit_product_event("widget_created", properties={"widget_id": 7}, settings=settings)

    assert captured[0]["event_name"] == "widget_created"
    assert captured[0]["properties"]["widget_id"] == 7


def test_emit_product_event_posts_to_posthog(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

    def record_post(url: str, *, json: dict[str, Any], timeout: float) -> Response:
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("code_readiness_template.analytics.httpx.post", record_post)

    settings = Settings(
        app_env="test",
        app_release="unit-test",
        posthog_api_key="test-key",
        posthog_host="https://example.invalid",
    )
    emit_product_event("widget_detail_viewed", properties={"slug": "demo"}, settings=settings)

    assert captured["url"] == "https://example.invalid/capture/"
    assert captured["payload"]["event"] == "widget_detail_viewed"
    assert captured["payload"]["properties"]["slug"] == "demo"
    assert captured["timeout"] == 2.0


def test_emit_product_event_logs_delivery_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    warnings: list[dict[str, Any]] = []
    attempts = {"count": 0}

    def fail_post(*args: Any, **kwargs: Any) -> None:
        attempts["count"] += 1
        raise httpx.HTTPError("network down")

    def record_warning(_message: str, *, extra: dict[str, Any]) -> None:
        warnings.append(extra)

    monkeypatch.setattr("code_readiness_template.analytics.httpx.post", fail_post)
    monkeypatch.setattr("code_readiness_template.analytics.LOGGER.warning", record_warning)

    settings = Settings(
        app_env="test",
        app_release="unit-test",
        posthog_api_key="test-key",
        posthog_host="https://example.invalid",
        analytics_circuit_breaker_threshold=1,
    )
    emit_product_event("widget_list_viewed", settings=settings)

    assert attempts["count"] == 3
    assert warnings[-1]["event"] == "product.event.delivery_failed"
    assert warnings[-1]["circuit_open"] is True


def test_emit_product_event_skips_when_circuit_is_open(monkeypatch: pytest.MonkeyPatch) -> None:
    warnings: list[dict[str, Any]] = []

    def fail_post(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("httpx.post should not be called while breaker is open.")

    def record_warning(_message: str, *, extra: dict[str, Any]) -> None:
        warnings.append(extra)

    monkeypatch.setattr("code_readiness_template.analytics.httpx.post", fail_post)
    monkeypatch.setattr("code_readiness_template.analytics.LOGGER.warning", record_warning)

    CIRCUIT_BREAKER_STATE.failure_count = 3
    CIRCUIT_BREAKER_STATE.opened_at = 999999.0
    monkeypatch.setattr("code_readiness_template.analytics.time.monotonic", lambda: 1000000.0)

    settings = Settings(
        app_env="test",
        app_release="unit-test",
        posthog_api_key="test-key",
        posthog_host="https://example.invalid",
        analytics_circuit_breaker_threshold=3,
        analytics_circuit_breaker_reset_seconds=30,
    )
    emit_product_event("widget_list_viewed", settings=settings)

    assert warnings[0]["event"] == "product.event.skipped"
    assert warnings[0]["reason"] == "circuit_open"


def test_emit_product_event_closes_circuit_after_reset_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

    def record_post(url: str, *, json: dict[str, Any], timeout: float) -> Response:
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("code_readiness_template.analytics.httpx.post", record_post)
    monkeypatch.setattr("code_readiness_template.analytics.time.monotonic", lambda: 1031.0)

    CIRCUIT_BREAKER_STATE.failure_count = 3
    CIRCUIT_BREAKER_STATE.opened_at = 1000.0

    settings = Settings(
        app_env="test",
        app_release="unit-test",
        posthog_api_key="test-key",
        posthog_host="https://example.invalid",
        analytics_circuit_breaker_threshold=3,
        analytics_circuit_breaker_reset_seconds=30,
    )
    emit_product_event("widget_detail_viewed", properties={"slug": "demo"}, settings=settings)

    assert captured["url"] == "https://example.invalid/capture/"
    assert CIRCUIT_BREAKER_STATE.opened_at is None

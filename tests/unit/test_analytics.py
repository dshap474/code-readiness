from __future__ import annotations

from typing import Any

import httpx
import pytest

from code_readiness_template.analytics import emit_product_event
from code_readiness_template.config import Settings


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

    def record_post(url: str, *, json: dict[str, Any], timeout: float) -> None:
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout

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

    def fail_post(*args: Any, **kwargs: Any) -> None:
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
    )
    emit_product_event("widget_list_viewed", settings=settings)

    assert warnings[0]["event"] == "product.event.delivery_failed"

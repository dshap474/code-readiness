from __future__ import annotations

import logging
from typing import Any

import httpx
from prometheus_client import Counter

from code_readiness_template.config import Settings, get_settings
from code_readiness_template.observability import redact_sensitive_data

LOGGER = logging.getLogger("code_readiness_template.product")
PRODUCT_EVENTS_TOTAL = Counter(
    "code_readiness_product_events_total",
    "Total product events emitted by the template service.",
    ("event_name",),
)


def emit_product_event(
    event_name: str,
    *,
    properties: dict[str, Any] | None = None,
    distinct_id: str | None = None,
    settings: Settings | None = None,
) -> None:
    runtime_settings = settings or get_settings()
    safe_properties = {
        "app_env": runtime_settings.app_env,
        "release": runtime_settings.app_release or "local",
        **(properties or {}),
    }
    PRODUCT_EVENTS_TOTAL.labels(event_name).inc()
    LOGGER.info(
        "product.event",
        extra={
            "event": "product.event",
            "event_name": event_name,
            "distinct_id": distinct_id or "anonymous",
            "properties": redact_sensitive_data(safe_properties),
        },
    )
    if not runtime_settings.posthog_api_key:
        return

    payload = {
        "api_key": runtime_settings.posthog_api_key,
        "event": event_name,
        "distinct_id": distinct_id or "anonymous",
        "properties": safe_properties,
    }
    endpoint = f"{runtime_settings.posthog_host.rstrip('/')}/capture/"
    try:
        httpx.post(endpoint, json=payload, timeout=2.0)
    except httpx.HTTPError:
        LOGGER.warning(
            "product.event.delivery_failed",
            extra={
                "event": "product.event.delivery_failed",
                "event_name": event_name,
                "host": runtime_settings.posthog_host,
            },
        )

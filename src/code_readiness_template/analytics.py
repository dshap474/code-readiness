from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx
from prometheus_client import Counter
from tenacity import RetryCallState, retry, stop_after_attempt, wait_exponential

from code_readiness_template.config import Settings, get_settings
from code_readiness_template.observability import redact_sensitive_data

LOGGER = logging.getLogger("code_readiness_template.product")
PRODUCT_EVENTS_TOTAL = Counter(
    "code_readiness_product_events_total",
    "Total product events emitted by the template service.",
    ("event_name",),
)
PRODUCT_EVENTS_DROPPED_TOTAL = Counter(
    "code_readiness_product_events_dropped_total",
    "Total product events dropped because the analytics circuit breaker was open.",
    ("reason",),
)


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    opened_at: float | None = None


CIRCUIT_BREAKER_STATE = CircuitBreakerState()


def _before_sleep_log(retry_state: RetryCallState) -> None:
    error = retry_state.outcome.exception() if retry_state.outcome else None
    LOGGER.warning(
        "product.event.retrying",
        extra={
            "event": "product.event.retrying",
            "attempt": retry_state.attempt_number,
            "error": str(error) if error else "unknown",
        },
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, min=0.1, max=1),
    before_sleep=_before_sleep_log,
    reraise=True,
)
def _post_event(endpoint: str, payload: dict[str, Any], timeout_seconds: float) -> None:
    response = httpx.post(endpoint, json=payload, timeout=timeout_seconds)
    response.raise_for_status()


def _circuit_breaker_open(now: float, settings: Settings) -> bool:
    opened_at = CIRCUIT_BREAKER_STATE.opened_at
    if opened_at is None:
        return False
    reset_window = settings.analytics_circuit_breaker_reset_seconds
    if now - opened_at >= reset_window:
        CIRCUIT_BREAKER_STATE.failure_count = 0
        CIRCUIT_BREAKER_STATE.opened_at = None
        return False
    return True


def _record_delivery_failure(event_name: str, settings: Settings, error: Exception) -> None:
    CIRCUIT_BREAKER_STATE.failure_count += 1
    if CIRCUIT_BREAKER_STATE.failure_count >= settings.analytics_circuit_breaker_threshold:
        CIRCUIT_BREAKER_STATE.opened_at = time.monotonic()
    LOGGER.warning(
        "product.event.delivery_failed",
        extra={
            "event": "product.event.delivery_failed",
            "event_name": event_name,
            "host": runtime_host(settings.posthog_host),
            "failure_count": CIRCUIT_BREAKER_STATE.failure_count,
            "circuit_open": CIRCUIT_BREAKER_STATE.opened_at is not None,
            "error": str(error),
        },
    )


def runtime_host(host: str) -> str:
    return host.rstrip("/")


def reset_analytics_circuit_breaker() -> None:
    CIRCUIT_BREAKER_STATE.failure_count = 0
    CIRCUIT_BREAKER_STATE.opened_at = None


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
    if _circuit_breaker_open(time.monotonic(), runtime_settings):
        PRODUCT_EVENTS_DROPPED_TOTAL.labels("circuit_open").inc()
        LOGGER.warning(
            "product.event.skipped",
            extra={
                "event": "product.event.skipped",
                "event_name": event_name,
                "host": runtime_host(runtime_settings.posthog_host),
                "reason": "circuit_open",
            },
        )
        return

    endpoint = f"{runtime_host(runtime_settings.posthog_host)}/capture/"
    try:
        _post_event(endpoint, payload, runtime_settings.posthog_timeout_seconds)
        reset_analytics_circuit_breaker()
    except httpx.HTTPError as error:
        _record_delivery_failure(event_name, runtime_settings, error)

from __future__ import annotations

import logging
from typing import Any

import pytest
from fastapi import FastAPI

from code_readiness_template.config import Settings
from code_readiness_template.observability import (
    JsonFormatter,
    configure_sentry,
    configure_tracing,
    redact_sensitive_data,
)


def test_redact_sensitive_data_masks_secret_keys() -> None:
    payload = {"password": "secret-value", "nested": {"authorization": "Bearer token"}}
    assert redact_sensitive_data(payload) == {
        "password": "[REDACTED]",
        "nested": {"authorization": "[REDACTED]"},
    }


def test_redact_sensitive_data_preserves_safe_values() -> None:
    payload = {"status": "ok", "widget_id": 3}
    assert redact_sensitive_data(payload) == payload


def test_json_formatter_redacts_sensitive_extras() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="code_readiness_template",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.password = "secret-value"
    rendered = formatter.format(record)
    assert '"password": "[REDACTED]"' in rendered


def test_configure_sentry_calls_init(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[dict[str, Any]] = []
    monkeypatch.setattr("code_readiness_template.observability.SENTRY_CONFIGURED", False)
    monkeypatch.setattr(
        "code_readiness_template.observability.init_sentry",
        lambda **kwargs: called.append(kwargs),
    )
    settings = Settings(sentry_dsn="https://example.invalid/1", app_env="test", app_release="unit")
    configure_sentry(settings)
    assert called[0]["dsn"] == "https://example.invalid/1"


def test_configure_tracing_marks_app_instrumented(monkeypatch: pytest.MonkeyPatch) -> None:
    instrumented: list[FastAPI] = []
    providers: list[Any] = []

    class FakeTracerProvider:
        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        def add_span_processor(self, _processor: object) -> None:
            return None

    monkeypatch.setattr("code_readiness_template.observability.TRACING_CONFIGURED", False)
    monkeypatch.setattr(
        "code_readiness_template.observability.TracerProvider",
        FakeTracerProvider,
    )
    monkeypatch.setattr(
        "code_readiness_template.observability.OTLPSpanExporter",
        lambda endpoint: {"endpoint": endpoint},
    )
    monkeypatch.setattr(
        "code_readiness_template.observability.BatchSpanProcessor",
        lambda exporter: exporter,
    )
    monkeypatch.setattr(
        "code_readiness_template.observability.trace.set_tracer_provider",
        lambda provider: providers.append(provider),
    )

    def fake_instrument_app(app: FastAPI, *, excluded_urls: str) -> None:
        assert excluded_urls == "/metrics"
        instrumented.append(app)

    monkeypatch.setattr(
        "code_readiness_template.observability.FastAPIInstrumentor.instrument_app",
        fake_instrument_app,
    )
    settings = Settings(otel_exporter_otlp_endpoint="http://collector:4318/v1/traces")
    app = FastAPI()
    configure_tracing(app, settings)
    assert instrumented == [app]
    assert len(providers) == 1
    assert app.state.otel_instrumented is True

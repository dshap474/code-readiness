from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sentry_sdk import init as init_sentry
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from code_readiness_template.config import Settings

REQUEST_ID_CONTEXT: ContextVar[str | None] = ContextVar("request_id", default=None)
SENSITIVE_KEYWORDS = {
    "api_key",
    "authorization",
    "cookie",
    "database_url",
    "dsn",
    "password",
    "secret",
    "token",
}
PII_KEYWORDS = {
    "address",
    "dob",
    "email",
    "first_name",
    "last_name",
    "full_name",
    "name",
    "phone",
    "ssn",
}
LOGGING_CONFIGURED = False
SENTRY_CONFIGURED = False
TRACING_CONFIGURED = False

HTTP_REQUESTS_TOTAL = Counter(
    "code_readiness_http_requests_total",
    "Total HTTP requests handled by the template service.",
    ("method", "path", "status"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "code_readiness_http_request_duration_seconds",
    "HTTP request latency for the template service.",
    ("method", "path"),
)

LOGGER = logging.getLogger("code_readiness_template")


def _current_trace_id() -> str | None:
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None
    return f"{span_context.trace_id:032x}"


def redact_sensitive_data(value: Any, *, key: str | None = None) -> Any:
    lowered_key = (key or "").lower()
    if lowered_key and any(keyword in lowered_key for keyword in SENSITIVE_KEYWORDS):
        return "[REDACTED]"
    if lowered_key and any(keyword in lowered_key for keyword in PII_KEYWORDS):
        return "[REDACTED-PII]"
    if isinstance(value, dict):
        return {
            item_key: redact_sensitive_data(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, str):
        lowered_value = value.lower()
        if any(keyword in lowered_value for keyword in SENSITIVE_KEYWORDS):
            return "[REDACTED]"
        if "@" in value and "." in value.split("@")[-1]:
            return "[REDACTED-PII]"
    return value


class JsonFormatter(logging.Formatter):
    RESERVED_FIELDS = {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": REQUEST_ID_CONTEXT.get(),
            "trace_id": _current_trace_id(),
        }
        for key, value in record.__dict__.items():
            if key in self.RESERVED_FIELDS or key.startswith("_"):
                continue
            payload[key] = redact_sensitive_data(value, key=key)
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(
            {key: value for key, value in payload.items() if value is not None}, sort_keys=True
        )


def configure_logging() -> None:
    global LOGGING_CONFIGURED
    if LOGGING_CONFIGURED:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    LOGGING_CONFIGURED = True


def configure_sentry(settings: Settings) -> None:
    global SENTRY_CONFIGURED
    if SENTRY_CONFIGURED or not settings.sentry_dsn:
        return

    init_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        release=settings.app_release,
        send_default_pii=False,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
    )
    SENTRY_CONFIGURED = True


def configure_tracing(app: FastAPI, settings: Settings) -> None:
    global TRACING_CONFIGURED
    if settings.otel_exporter_otlp_endpoint and not TRACING_CONFIGURED:
        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": "code-readiness-template",
                    "deployment.environment": settings.app_env,
                }
            )
        )
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        TRACING_CONFIGURED = True

    if not getattr(app.state, "otel_instrumented", False):
        FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics")
        app.state.otel_instrumented = True


def configure_observability(app: FastAPI, settings: Settings) -> None:
    configure_logging()
    configure_sentry(settings)
    configure_tracing(app, settings)

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        token = REQUEST_ID_CONTEXT.set(request_id)
        started_at = time.perf_counter()
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception:
            duration_seconds = time.perf_counter() - started_at
            HTTP_REQUESTS_TOTAL.labels(request.method, path, "500").inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(request.method, path).observe(duration_seconds)
            LOGGER.exception(
                "request.failed",
                extra={
                    "event": "http.request.failed",
                    "method": request.method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": round(duration_seconds * 1000, 3),
                },
            )
            REQUEST_ID_CONTEXT.reset(token)
            raise

        duration_seconds = time.perf_counter() - started_at
        status_code = str(response.status_code)
        response.headers["x-request-id"] = request_id
        HTTP_REQUESTS_TOTAL.labels(request.method, path, status_code).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(request.method, path).observe(duration_seconds)
        LOGGER.info(
            "request.completed",
            extra={
                "event": "http.request.completed",
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_seconds * 1000, 3),
            },
        )
        REQUEST_ID_CONTEXT.reset(token)
        return response


def metrics_response() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


def log_runtime_event(event: str, **fields: Any) -> None:
    LOGGER.info(event, extra={"event": event, **fields})

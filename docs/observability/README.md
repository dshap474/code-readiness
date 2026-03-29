# Observability

## Runtime Surface

This template service uses one small, coherent observability surface:

- structured JSON logs from the FastAPI runtime
- request correlation through `x-request-id`
- optional OTEL tracing through `OTEL_EXPORTER_OTLP_ENDPOINT`
- optional Sentry error reporting through `SENTRY_DSN`
- Prometheus metrics on `GET /metrics`

## Canonical Signals

- logs: request lifecycle events plus widget route events
- metrics:
  - `code_readiness_http_requests_total`
  - `code_readiness_http_request_duration_seconds`
  - `code_readiness_widget_actions_total`
  - `code_readiness_product_events_total`
- traces: optional OTEL spans for FastAPI request handling
- error tracking: optional Sentry with environment and release context

## Dashboard Surface

The repo-level dashboard contract is documented in `monitoring/dashboards/README.md`.
The repo-owned quality report contract is documented in `monitoring/quality/README.md`.
Hosted dashboards can be added later, but the local-proofable readiness surface uses the
quality report, alert contract, profiling command, and post-deploy check script as the
authoritative evidence path.

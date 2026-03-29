# Observability Schema

## Log Fields

- `timestamp`: UTC ISO-8601 timestamp
- `level`: log severity
- `logger`: emitting logger name
- `message`: log message
- `event`: stable event identifier when present
- `request_id`: request correlation identifier
- `trace_id`: OTEL trace identifier when tracing is configured
- `status_code`: HTTP status when relevant
- `duration_ms`: request duration when relevant

## Metric Names

- `code_readiness_http_requests_total`
- `code_readiness_http_request_duration_seconds`
- `code_readiness_widget_actions_total`
- `code_readiness_product_events_total`

## Release Tags

- `APP_ENV` identifies the runtime environment
- `APP_RELEASE` identifies the release marker shown in `/healthz`, `/readyz`, and
  optional Sentry or OTEL exports

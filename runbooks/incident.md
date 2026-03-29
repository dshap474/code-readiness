# Incident Runbook

## Trigger

Use this runbook when the API is returning unexpected `5xx` responses, `/readyz`
fails, or error-tracking noise indicates a user-facing regression.

## First Checks

1. Check `GET /healthz` for liveness and `GET /readyz` for dependency readiness.
2. Inspect recent structured logs for `request.failed`, `readiness.failed`, or
   `widget.*` runtime events.
3. Review `GET /metrics` for request spikes, latency growth, or widget action drift.

## Evidence Sources

- structured logs from the app runtime
- `GET /metrics`
- optional Sentry issues tagged with environment and release
- optional OTEL trace exports when configured

## Escalation

1. If the failure is database-related, follow `runbooks/local-db-reset.md`.
2. If the failure follows a rollout, follow `runbooks/post-deploy.md`.
3. If a user-facing regression is confirmed, open or update a tracked issue through the
   error-to-insight flow in `docs/product/error-pipeline.md`.

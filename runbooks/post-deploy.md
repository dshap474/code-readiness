# Post-Deploy Runbook

## Purpose

Confirm a new release is healthy after rollout and connect deploy activity to the
template's runtime signals.

## Verification Steps

1. Run `just post-deploy-check` against the deployed base URL.
2. Check structured logs for `request.failed` or `readiness.failed`.
3. Check `GET /metrics` for abnormal request failure rates or latency.
4. Review optional Sentry or OTEL outputs if the repo is configured to send them.

## Rollback Signals

- `/readyz` returns `503`
- repeated `5xx` responses in request metrics
- contextualized application errors that reproduce on real widget flows

## Follow-Up

If rollback is required, use the deploy system outside this repo. Record the incident or
follow-up issue using the product error-routing path when the failure is user-facing.

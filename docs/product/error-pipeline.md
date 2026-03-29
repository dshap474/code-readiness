# Error To Insight Pipeline

## Error Source

- optional Sentry or equivalent project for contextualized runtime errors
- structured runtime logs and request metrics for repos that have not connected Sentry yet

## Routing Path

- GitHub issue destination using `.github/workflows/error-to-insight.yml`
- owner: engineering

## Triage Rule

- create tracked work for user-facing widget failures, repeated readiness failures, and
  post-deploy regressions
- keep low-signal operational noise in observability tooling only

## Required Context

Every routed issue should preserve:

- release or environment
- request or trace correlation when available
- failure summary
- links to the originating observability evidence

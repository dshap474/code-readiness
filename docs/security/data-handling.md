# Data Handling

## Current Data Classes

This template handles:

- widget names and slugs
- local development credentials provided through environment variables
- operational metadata such as request identifiers and release tags

It does not intentionally handle regulated personal data by default.

## Secret Handling

- secrets belong in local environment files or a hosted secret manager
- `.env.example` contains names and placeholders only
- `.gitignore` keeps local `.env` files and repo-local virtualenvs out of source control
- local changes are scanned with `scripts/check-secrets.py` and the `gitleaks-protect` pre-commit hook
- logs and analytics payloads redact secret-like values by default

## PII And Privacy Applicability

- `PII Handling`: `N/A` for the default template unless a downstream adopter adds
  personal-data fields
- `Privacy Compliance`: downstream-ready controls are present so adopters can wire regulated
  or privacy-sensitive data flows onto a concrete contract instead of starting from zero
- if downstream adopters add fields such as `email`, `phone`, `full_name`, or `address`,
  they must treat them as personal data and ensure logs and analytics are redacted as `[REDACTED-PII]`
- `scripts/check-pii-handling.py` blocks obvious personal-data field additions unless the repo is
  intentionally updated to handle them

## Downstream-Ready Privacy Controls

- `GET /privacy/retention` exposes the current retention policy contract
- `POST /privacy/export` represents the privacy export workflow surface
- `POST /privacy/delete` represents the privacy delete workflow surface
- all privacy workflow responses include the configured retention window and privacy contact email
- privacy workflow availability is controlled by `PRIVACY_EXPORT_ENABLED` and
  `PRIVACY_DELETE_ENABLED`
- retention policy is configured through `PRIVACY_DATA_RETENTION_DAYS`
- downstream adopters must replace the placeholder `PRIVACY_CONTACT_EMAIL` value before handling
  real user data

## Hosted Controls

The following controls are required after the repo is hosted and cannot be enforced from
source control alone:

- branch protection on the primary branch
- required status checks for CI and security review
- provider-native secret scanning and push protection

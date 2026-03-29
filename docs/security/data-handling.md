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
- logs and analytics payloads redact secret-like values by default

## PII And Privacy Applicability

- `PII Handling`: `N/A` for the default template unless a downstream adopter adds
  personal-data fields
- `Privacy Compliance`: `N/A` for the default template unless a downstream adopter adds
  regulated or privacy-sensitive data flows

## Hosted Controls

The following controls are required after the repo is hosted and cannot be enforced from
source control alone:

- branch protection on the primary branch
- required status checks for CI and security review
- provider-native secret scanning and push protection

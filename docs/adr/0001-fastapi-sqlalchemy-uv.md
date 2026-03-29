# ADR 0001: FastAPI + SQLAlchemy + uv

## Status

Accepted

## Context

The template repo needs a stable modern best Python service stack that is easy for Codex to bootstrap, validate, and extend without hidden framework machinery.

## Decision

Use:

- `uv` for environments, dependency resolution, locking, and builds
- FastAPI for the HTTP layer
- SQLAlchemy for the data layer
- Alembic for schema migrations
- Postgres as the local service dependency

## Consequences

- The repo gets a strong typed Python service baseline with explicit configuration and migrations.
- The template exercises local services, devcontainer, env templates, and integration tests honestly.
- The repo stays small enough that feature behavior remains easy to read.

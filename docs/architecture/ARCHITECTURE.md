# Architecture

## System Shape

This repo is a small FastAPI service with one Postgres-backed resource: `widgets`.

- HTTP entrypoint lives in `src/code_readiness_template/app.py`
- typed settings live in `src/code_readiness_template/config.py`
- engine and session ownership live in `src/code_readiness_template/db.py`
- runtime logging, metrics, and optional OTEL or Sentry setup live in `src/code_readiness_template/observability.py`
- product event emission lives in `src/code_readiness_template/analytics.py`
- widget routes, request models, response models, and table model are co-located in `src/code_readiness_template/features/widgets.py`
- schema changes live in `alembic/versions/`

## Dependency Direction

- `app.py` depends on feature routers and database health checks.
- feature modules depend on `db.py` and standard library helpers.
- `db.py` depends on typed settings from `config.py`.
- tests depend on public app and database surfaces, not the reverse.

## Runtime Boundaries

- FastAPI provides the HTTP boundary.
- `/healthz`, `/readyz`, and `/metrics` are the repo's runtime evidence endpoints.
- SQLAlchemy provides the persistence boundary.
- Postgres is the local and production-shaped data store.
- Alembic is the schema source of truth.
- structured logs, request correlation, and repo-owned metrics provide the observability boundary.

## Proof Surface

- static proof: `just lint` and `just type`
- fast tests: `just test-unit`
- broader proof: `just test`
- full local truth path: `just ci`

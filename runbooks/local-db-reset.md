# Local DB Reset

## Purpose

Reset the local Postgres state when the schema or seed data is no longer trustworthy.

## Steps

1. Stop dependent processes such as `just run`.
2. Run `just db-down`.
3. Start a clean database with `just db-up`.
4. Re-apply the schema with `uv run alembic upgrade head`.
5. Re-run the proof path with `just test-integration`.

## Verification

- `GET /readyz` returns `200`
- `just test-integration` passes

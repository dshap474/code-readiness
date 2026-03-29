# Devcontainer Rebuild

## Purpose

Rebuild the devcontainer when the Dockerfile, dependency surface, or bootstrap contract changes.

## Steps

1. Rebuild the devcontainer from the editor command palette or devcontainer UI.
2. Let `postCreateCommand` run `scripts/bootstrap-worktree.sh`.
3. Start Postgres with `just db-up` if it is not already running.
4. Apply migrations with `uv run alembic upgrade head`.
5. Run `just ci`.

## Verification

- `just run` starts successfully
- `GET /metrics` responds inside the container
- `just ci` passes inside the container

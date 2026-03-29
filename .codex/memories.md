# Project Memory

## Decisions

- Use `/.codex/` as the primary mirrored namespace because this repo is explicitly Codex-native.
- Keep `/scripts/bootstrap-worktree.sh` as the source of truth for setup so hooks stay thin.
- Use FastAPI + SQLAlchemy + Alembic + Postgres to exercise the prepared readiness sections honestly.

## Invariants

- `docs/api/openapi.yaml` is generated from the app and should not be edited by hand.
- `justfile` is the only public command surface.
- Alembic migrations are the database schema source of truth.

## Known Debt

- The remaining readiness sections are intentionally deferred to later phases listed in `PLANS.md`.

## Operations Notes

- Local integration tests use disposable Postgres containers.
- Local manual development uses `compose.yml` for Postgres.

# Code Readiness Template

This repository is a Codex-native FastAPI + SQLAlchemy + Postgres template used to exercise all nine hardened `code-readiness` sections:

- Style & Validation
- Build System
- Testing
- Documentation
- Development Environment
- Debugging & Observability
- Security
- Task Discovery
- Product & Experimentation

## Quickstart

1. Install `uv`, Docker, Node.js, and `just`.
2. Run `just bootstrap`.
3. Start Postgres with `just db-up`.
4. Apply migrations with `uv run alembic upgrade head`.
5. Start the API with `just run`.

If `just` is unavailable, the underlying commands are documented in the root `justfile`.

## API Surface

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/widgets`
- `POST /api/v1/widgets`
- `GET /api/v1/widgets/{widget_id}`

## Proof Commands

- `just fmt`
- `just lint`
- `just type`
- `just test`
- `just ci`
- `just docs-generate`
- `just docs-check`
- `just profile`
- `just post-deploy-check`

## GitHub Operator Flows

- inspect pull requests with `gh pr view`
- inspect recent workflow runs with `gh run list`
- inspect triage issues created by automation with `gh issue list --label needs-triage`

## Control Plane

The primary mirrored namespace for this repo is `/.codex/`.

- Root agent guidance lives in `AGENTS.md`.
- Shared Codex config lives in `/.codex/config.toml`.
- Lifecycle hook wiring lives in `/.codex/hooks.json`.
- Repo-owned hook scripts live in `/.codex/hooks/`.

## New Readiness Surfaces

- observability docs: `docs/observability/` and `monitoring/`
- security contracts: `.github/CODEOWNERS`, `.github/dependabot.yml`, `.gitleaks.toml`, and `docs/security/`
- task discovery: `.github/labels.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, and `.github/task-discovery.md`
- product contracts: `docs/product/` and `.github/workflows/error-to-insight.yml`

## Next Docs

- Architecture: `docs/architecture/ARCHITECTURE.md`
- ADR: `docs/adr/0001-fastapi-sqlalchemy-uv.md`
- Generated API contract: `docs/api/openapi.yaml`
- Runbooks: `runbooks/`
- Quality report contract: `monitoring/quality/README.md`
- Current readiness notes: `PLANS.md`

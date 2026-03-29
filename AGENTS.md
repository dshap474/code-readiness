# AGENTS

Use this file as the universal operating contract for the repo.

## Start Here

- Bootstrap from a clean checkout with `just bootstrap`.
- Start local Postgres with `just db-up`.
- Apply schema changes with `uv run alembic upgrade head`.
- Run the app with `just run`.
- Use `FEATURE_FLAGS=widget_write_enabled=false` when you need to disable widget writes without
  taking the read surface down.
- Apply formatting with `just fmt` and expect `ruff format` to stay clean.
- Prove changes with `just ci` before concluding work.
- Inspect pull requests with `gh pr view`.
- Inspect workflow runs with `gh run list`.
- Download PR review artifacts with `gh run download --name codex-pr-review`.
- Download CI timing artifacts with `gh run download --name fast-feedback`.
- Download CI performance summaries with `gh run download --name ci-performance-summary`.
- Inspect deploy runs with `gh run list --workflow deploy.yml`.
- Download deploy evidence with `gh run download --name deploy-evidence`.
- Trigger rollback automation with deploy workflow inputs `mode: rollback` and `rollback_release`.
- Inspect generated release notes with `gh run list --workflow release-notes.yml`.
- Inspect published releases with `gh release list`.
- Inspect security review runs with `gh run list --workflow security-review.yml`.

## Primary Namespace

This repo is Codex-native. The primary mirrored namespace is `/.codex/`.

- Shared Codex config: `/.codex/config.toml`
- Lifecycle wiring: `/.codex/hooks.json`
- Hook scripts: `/.codex/hooks/`
- Repo memory: `/.codex/memories.md`
- Repo rules: `/.codex/rules/`
- Reusable workflows: `/.codex/skills/`
- Bounded subagents: `/.codex/agents/`

## Constraints

- `/scripts/bootstrap-worktree.sh` is the source of truth for automated setup.
- `/.codex/hooks.json` must remain a thin wiring layer over repo-owned scripts.
- `docs/api/openapi.yaml` is generated from the FastAPI app. Refresh it with `just docs-generate`.
- Do not add a second public command surface. Root commands belong in `justfile`.
- Keep security guardrails in `/.codex/hooks/pre-tool-use-security.sh` thin and deterministic.
- Keep product event contracts in `docs/product/` aligned with the actual app instrumentation in `src/`.
- Keep observability contracts in `docs/observability/`, `monitoring/`, and `runbooks/` aligned with the real runtime behavior.
- Keep local-proofable automation evidence in `.github/proof/` aligned with the workflows and check scripts that validate it.

## Durable Docs

- Architecture: `docs/architecture/ARCHITECTURE.md`
- ADRs: `docs/adr/`
- Observability: `docs/observability/` and `monitoring/`
- Security: `docs/security/`
- Product contracts: `docs/product/`
- Runbooks: `runbooks/`
- Readiness notes and hosted-only gaps: `PLANS.md`

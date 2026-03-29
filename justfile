set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
    @just --list

bootstrap:
    ./scripts/bootstrap-worktree.sh

run:
    uv run uvicorn code_readiness_template.app:app --reload --host "${APP_HOST:-127.0.0.1}" --port "${APP_PORT:-8000}"

fmt:
    uv run ruff format .

lint:
    uv run ruff check .
    uv run python scripts/check-secrets.py
    uv run python scripts/check-build-surface.py
    uv run python scripts/check-devcontainer.py
    uv run python scripts/check-large-files.py
    uv run python scripts/check-debt.py
    uv run python scripts/check-architecture.py
    uv run python scripts/check-observability.py
    uv run python scripts/check-security-surface.py
    uv run python scripts/check-task-discovery.py
    uv run python scripts/check-product-surface.py
    uv run radon cc src -n B -s
    npx --yes jscpd@4.0.5 --config .jscpd.json
    uv run vulture src tests scripts scripts/vulture_whitelist.py --min-confidence 100
    uv run deptry .

type:
    uv run ty check src tests scripts

build:
    uv build

test-unit:
    uv run pytest tests/unit --cov-fail-under=0

test-integration:
    uv run pytest tests/integration -m integration --cov-fail-under=0

test:
    uv run pytest

ci:
    uv run ruff format --check .
    uv run ruff check .
    uv run python scripts/check-secrets.py
    uv run ty check src tests scripts
    uv run python scripts/check-build-surface.py
    uv run python scripts/check-devcontainer.py
    uv run python scripts/check-large-files.py
    uv run python scripts/check-debt.py
    uv run python scripts/check-architecture.py
    uv run python scripts/check-observability.py
    uv run python scripts/check-security-surface.py
    uv run python scripts/check-task-discovery.py
    uv run python scripts/check-product-surface.py
    uv run radon cc src -n B -s
    npx --yes jscpd@4.0.5 --config .jscpd.json
    uv run vulture src tests scripts scripts/vulture_whitelist.py --min-confidence 100
    uv run deptry .
    bash .codex/hooks/check-docs.sh
    uv build
    uv run pytest
    uv run python scripts/check-flaky-tests.py

db-up:
    docker compose up -d postgres

db-down:
    docker compose down --remove-orphans

docs-generate:
    uv run python scripts/export_openapi.py --write

docs-check:
    bash .codex/hooks/check-docs.sh

profile:
    bash scripts/profile-widget-routes.sh

post-deploy-check base_url="http://127.0.0.1:8000":
    bash scripts/post-deploy-check.sh {{base_url}}

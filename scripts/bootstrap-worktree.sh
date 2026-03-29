#!/bin/bash
set -euo pipefail

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

uv sync --dev
uv run pre-commit install

echo
echo "Bootstrap complete."
echo "Next steps:"
echo "  1. docker compose up -d postgres"
echo "  2. uv run alembic upgrade head"
echo "  3. just run"

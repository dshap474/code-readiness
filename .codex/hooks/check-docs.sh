#!/bin/bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"

if [[ ! -f "$repo_root/.venv/bin/python" ]]; then
  echo "Skipping docs check because the local environment is not bootstrapped yet."
  exit 0
fi

cd "$repo_root"
grep -q '^## Start Here' AGENTS.md
grep -q '^## Primary Namespace' AGENTS.md
grep -q '^## Constraints' AGENTS.md
grep -q '^## Durable Docs' AGENTS.md
grep -q '/.codex/' AGENTS.md
uv run python scripts/export_openapi.py --check

#!/usr/bin/env bash
set -euo pipefail

artifact="monitoring/profiling/widget-routes.prof"
mkdir -p "$(dirname "${artifact}")"

uv run python -m cProfile -o "${artifact}" -m pytest tests/unit/test_widget_routes.py -q

echo "Wrote profiling artifact to ${artifact}"

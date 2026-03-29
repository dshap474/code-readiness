#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-http://127.0.0.1:8000}"

curl --fail --silent "${base_url}/healthz" >/dev/null
curl --fail --silent "${base_url}/readyz" >/dev/null
curl --fail --silent "${base_url}/metrics" >/dev/null

echo "Post-deploy checks passed for ${base_url}"

#!/bin/bash
set -euo pipefail

payload="$(cat)"
command="$(
  python3 -c 'import json, sys; payload = json.load(sys.stdin); print(payload.get("tool_input", {}).get("command", ""))' <<<"$payload"
)"

blocked_reason=""
if printf '%s' "$command" | grep -Eq '(^|[[:space:]])git[[:space:]]+push([[:space:]]|$)'; then
  blocked_reason="Direct git push is blocked in this repo. Use the human publication workflow."
elif printf '%s' "$command" | grep -Eq 'git[[:space:]]+reset[[:space:]]+--hard'; then
  blocked_reason="git reset --hard is blocked by the repo security hook."
elif printf '%s' "$command" | grep -Eq 'rm[[:space:]]+-rf[[:space:]]+/'; then
  blocked_reason="Destructive root deletion is blocked by the repo security hook."
elif printf '%s' "$command" | grep -Eq 'curl.+\|[[:space:]]*(sh|bash)'; then
  blocked_reason="Piped remote shell execution is blocked by the repo security hook."
fi

if [[ -n "$blocked_reason" ]]; then
  echo "$blocked_reason" >&2
  exit 2
fi

exit 0

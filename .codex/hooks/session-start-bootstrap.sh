#!/bin/bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
"/bin/bash" "$repo_root/scripts/bootstrap-worktree.sh"

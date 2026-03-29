from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config_path = ROOT / ".devcontainer" / "devcontainer.json"
    dockerfile_path = ROOT / ".devcontainer" / "Dockerfile"
    if not config_path.exists() or not dockerfile_path.exists():
        print("Devcontainer check failed. Missing .devcontainer files.")
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))
    post_create = config.get("postCreateCommand", "")
    if "scripts/bootstrap-worktree.sh" not in post_create:
        print(
            "Devcontainer check failed. "
            "devcontainer.json must delegate setup to scripts/bootstrap-worktree.sh."
        )
        return 1
    if "build" not in config:
        print("Devcontainer check failed. devcontainer.json must define a build surface.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

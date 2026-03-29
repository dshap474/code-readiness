from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".codex" / "hooks" / "pre-tool-use-security.sh"


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run(
        ["/bin/bash", str(HOOK)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )


def test_security_hook_blocks_direct_git_push() -> None:
    result = run_hook("git push origin main")
    assert result.returncode == 2
    assert "Direct git push is blocked" in result.stderr


def test_security_hook_allows_safe_commands() -> None:
    result = run_hook("uv run pytest tests/unit")
    assert result.returncode == 0


def test_architecture_check_enforces_module_boundaries() -> None:
    result = subprocess.run(
        [str(ROOT / ".venv" / "bin" / "python"), str(ROOT / "scripts" / "check-architecture.py")],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0

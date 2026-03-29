from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if shutil.which("gitleaks") is None:
        print("Secret scan check failed. Install `gitleaks` to run local secret scanning.")
        print("Suggested install: `brew install gitleaks`.")
        return 1

    command = [
        "gitleaks",
        "dir",
        str(ROOT),
        "--config",
        str(ROOT / ".gitleaks.toml"),
        "--redact",
    ]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print("Secret scan check failed. gitleaks reported potential secrets.")
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

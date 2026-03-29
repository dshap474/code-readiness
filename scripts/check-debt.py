from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "build"}
EXCLUDED_FILES = {"check-debt.py", "uv.lock"}
DEBT_PATTERN = re.compile(r"\b(TODO|FIXME)\b(?!.*(#\d+|https?://))")


def should_scan(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name in EXCLUDED_FILES:
        return False
    tracked_suffixes = {".py", ".md", ".toml", ".yaml", ".yml", ".json"}
    return path.suffix in tracked_suffixes or path.name == "justfile"


def main() -> int:
    violations: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not should_scan(path):
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if DEBT_PATTERN.search(line):
                violations.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")
    if violations:
        print("Debt tracking check failed. TODO/FIXME entries require an issue reference or URL.")
        for violation in violations:
            print(f"- {violation}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

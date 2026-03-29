from __future__ import annotations

from pathlib import Path

MAX_LINES = 400
ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
}
EXCLUDED_PATHS = {
    ROOT / "docs" / "api" / "openapi.yaml",
}
TRACKED_SUFFIXES = {".md", ".py", ".json", ".toml", ".yaml", ".yml"}


def should_check(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path in EXCLUDED_PATHS:
        return False
    if "alembic" in path.parts and "versions" in path.parts:
        return False
    if path.name == "justfile":
        return True
    return path.suffix in TRACKED_SUFFIXES


def main() -> int:
    violations: list[str] = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not should_check(path):
            continue
        line_count = path.read_text(encoding="utf-8").count("\n") + 1
        if line_count > MAX_LINES:
            violations.append(f"{path.relative_to(ROOT)}: {line_count} lines")

    if violations:
        print(f"Large-file check failed. Maximum allowed lines: {MAX_LINES}")
        for violation in violations:
            print(f"- {violation}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

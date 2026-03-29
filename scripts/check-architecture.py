from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "code_readiness_template"
FORBIDDEN_PREFIXES = ("tests", "scripts", "docs")
FORBIDDEN_FEATURE_IMPORTS = ("code_readiness_template.app",)


def iter_python_files() -> list[Path]:
    return sorted(path for path in SRC_ROOT.rglob("*.py") if path.is_file())


def resolve_import(from_module: str | None, level: int, current_module: str) -> str | None:
    if level == 0:
        return from_module
    parts = current_module.split(".")
    if level > len(parts):
        return None
    prefix = parts[:-level]
    if from_module:
        prefix.append(from_module)
    return ".".join(prefix)


def module_name_for(path: Path) -> str:
    relative = path.relative_to(ROOT / "src").with_suffix("")
    return ".".join(relative.parts)


def violations_for_node(node: ast.AST, module_name: str, path: Path) -> list[str]:
    violations: list[str] = []
    relative_path = path.relative_to(ROOT)

    if isinstance(node, ast.Import):
        for alias in node.names:
            imported = alias.name
            if imported.startswith(FORBIDDEN_PREFIXES):
                violations.append(
                    f"{relative_path} imports forbidden external surface `{imported}`."
                )
        return violations

    if isinstance(node, ast.ImportFrom):
        imported = resolve_import(node.module, node.level, module_name)
        if imported and imported.startswith(FORBIDDEN_PREFIXES):
            violations.append(f"{relative_path} imports forbidden external surface `{imported}`.")
        if (
            module_name.startswith("code_readiness_template.features")
            and imported in FORBIDDEN_FEATURE_IMPORTS
        ):
            violations.append(
                f"{relative_path} imports `{imported}`. "
                "Feature modules must not import app entrypoints."
            )

    return violations


def main() -> int:
    violations: list[str] = []

    for path in iter_python_files():
        module_name = module_name_for(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            violations.extend(violations_for_node(node, module_name, path))

    if violations:
        print("Architecture check failed.")
        for violation in violations:
            print(f"- {violation}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

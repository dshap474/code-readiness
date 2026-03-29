from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBSERVABILITY = ROOT / "src" / "code_readiness_template" / "observability.py"
DATA_HANDLING = ROOT / "docs" / "security" / "data-handling.md"
PII_FIELD_MARKERS = {"email", "phone", "ssn", "full_name", "first_name", "last_name", "address"}


def check_observability_redaction() -> int:
    source = OBSERVABILITY.read_text(encoding="utf-8")
    for term in ("PII_KEYWORDS", "[REDACTED-PII]", "send_default_pii=False"):
        if term not in source:
            print(f"PII handling check failed. observability.py must include `{term}`.")
            return 1
    return 0


def check_docs() -> int:
    text = DATA_HANDLING.read_text(encoding="utf-8")
    for term in (
        "PII Handling",
        "Privacy Compliance",
        "redacted as `[REDACTED-PII]`",
        "privacy export",
        "privacy delete",
        "retention",
        "email",
        "phone",
    ):
        if term not in text:
            print(f"PII handling check failed. data-handling.md must mention `{term}`.")
            return 1
    return 0


def _iter_source_files() -> list[Path]:
    return [path for path in (ROOT / "src").rglob("*.py") if ".venv" not in path.parts]


def _pii_violations_for_node(node: ast.AST, path: Path) -> list[str]:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.target.id.lower() in PII_FIELD_MARKERS:
            return [f"{path.relative_to(ROOT)}::{node.target.id}"]
    if isinstance(node, ast.Assign):
        return [
            f"{path.relative_to(ROOT)}::{target.id}"
            for target in node.targets
            if isinstance(target, ast.Name) and target.id.lower() in PII_FIELD_MARKERS
        ]
    return []


def check_runtime_models() -> int:
    violations = [
        violation
        for path in _iter_source_files()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        for violation in _pii_violations_for_node(node, path)
    ]
    if violations:
        print("PII handling check failed. Explicit personal-data fields require review:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    return 0


def main() -> int:
    for check in (check_observability_redaction, check_docs, check_runtime_models):
        result = check()
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

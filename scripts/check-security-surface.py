from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    ROOT / ".github" / "CODEOWNERS",
    ROOT / ".github" / "dependabot.yml",
    ROOT / ".github" / "branch-protection.json",
    ROOT / ".github" / "workflows" / "security-review.yml",
    ROOT / ".gitleaks.toml",
    ROOT / "docs" / "security" / "data-handling.md",
    ROOT / ".codex" / "hooks.json",
    ROOT / ".codex" / "hooks" / "pre-tool-use-security.sh",
]


def check_required_files() -> int:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    if not missing:
        return 0

    print("Security surface check failed.")
    for path in missing:
        print(f"- Missing required file: {path}")
    return 1


def check_codeowners() -> int:
    codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    for owned_path in (".github/", ".codex/", "docs/security/"):
        if owned_path not in codeowners:
            print(f"Security surface check failed. CODEOWNERS must cover `{owned_path}`.")
            return 1
    return 0


def check_codex_hook() -> int:
    hooks_text = (ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8")
    if "PreToolUse" not in hooks_text or "pre-tool-use-security.sh" not in hooks_text:
        print(
            "Security surface check failed. "
            ".codex/hooks.json must wire the pre-tool-use security hook."
        )
        return 1
    return 0


def check_gitignore() -> int:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", ".venv/"):
        if pattern not in gitignore:
            print(f"Security surface check failed. .gitignore must ignore `{pattern}`.")
            return 1
    return 0


def check_dependabot() -> int:
    dependabot = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    if not isinstance(dependabot, dict) or "updates" not in dependabot:
        print("Security surface check failed. dependabot.yml must define update entries.")
        return 1

    ecosystems = {item["package-ecosystem"] for item in dependabot["updates"]}
    for ecosystem in ("pip", "github-actions"):
        if ecosystem not in ecosystems:
            print(f"Security surface check failed. dependabot.yml must cover `{ecosystem}`.")
            return 1
    return 0


def check_branch_protection() -> int:
    branch_protection = yaml.safe_load(
        (ROOT / ".github" / "branch-protection.json").read_text(encoding="utf-8")
    )
    if branch_protection.get("branch") != "main":
        print("Security surface check failed. branch-protection.json must target main.")
        return 1

    checks = branch_protection.get("required_status_checks", [])
    for required_check in ("proof", "secret-scan", "dast"):
        if required_check not in checks:
            print(
                "Security surface check failed. "
                f"branch-protection.json must require `{required_check}`."
            )
            return 1
    return 0


def check_security_workflow() -> int:
    workflow = (ROOT / ".github" / "workflows" / "security-review.yml").read_text(encoding="utf-8")
    for term in ("gitleaks", "zap-baseline.py"):
        if term not in workflow:
            print(f"Security surface check failed. security-review.yml must include `{term}`.")
            return 1
    return 0


def main() -> int:
    for check in (
        check_required_files,
        check_codeowners,
        check_codex_hook,
        check_gitignore,
        check_dependabot,
        check_branch_protection,
        check_security_workflow,
    ):
        result = check()
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

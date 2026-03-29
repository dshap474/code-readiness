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
    ROOT / "scripts" / "check-pii-handling.py",
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
    for pattern in (".env", ".venv/", ".vscode/", ".idea/", ".DS_Store", "dist/", "build/"):
        if pattern not in gitignore:
            print(f"Security surface check failed. .gitignore must ignore `{pattern}`.")
            return 1
    return 0


def check_dependabot() -> int:
    dependabot = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    if not isinstance(dependabot, dict) or "updates" not in dependabot:
        print("Security surface check failed. dependabot.yml must define update entries.")
        return 1

    updates = dependabot["updates"]
    ecosystems = {item["package-ecosystem"] for item in updates}
    for ecosystem in ("pip", "github-actions"):
        if ecosystem not in ecosystems:
            print(f"Security surface check failed. dependabot.yml must cover `{ecosystem}`.")
            return 1

    for item in updates:
        schedule = item.get("schedule", {})
        if schedule.get("interval") != "weekly":
            print("Security surface check failed. dependabot entries must run weekly.")
            return 1
        if schedule.get("day") != "monday" or schedule.get("timezone") != "UTC":
            print(
                "Security surface check failed. "
                "dependabot entries must define Monday UTC schedules."
            )
            return 1
        if "labels" not in item or "dependencies" not in item["labels"]:
            print("Security surface check failed. dependabot entries must label dependency PRs.")
            return 1
        if item.get("commit-message", {}).get("prefix") != "deps":
            print(
                "Security surface check failed. "
                "dependabot entries must use the `deps` commit prefix."
            )
            return 1
        if "groups" not in item or not item["groups"]:
            print("Security surface check failed. dependabot entries must define groups.")
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
    for term in (
        "gitleaks",
        "gitleaks/gitleaks-action@v2",
        "zap-baseline.py",
        "dast-target.json",
        "dast-summary.md",
        "Readiness gate",
        "security-review-summary.md",
        "upload-artifact",
        "gitleaks-summary.md",
    ):
        if term not in workflow:
            print(f"Security surface check failed. security-review.yml must include `{term}`.")
            return 1
    return 0


def check_local_secret_scanning() -> int:
    pre_commit = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    justfile = (ROOT / "justfile").read_text(encoding="utf-8")
    checker = (ROOT / "scripts" / "check-secrets.py").read_text(encoding="utf-8")

    for term in ("gitleaks-protect", "scripts/check-secrets.py"):
        if term not in pre_commit:
            print(
                "Security surface check failed. "
                f".pre-commit-config.yaml must include `{term}` for local secret scanning."
            )
            return 1

    for term in ("uv run python scripts/check-secrets.py",):
        if term not in justfile:
            print(f"Security surface check failed. justfile must include `{term}`.")
            return 1

    for term in ('"gitleaks"', "--config", "--redact"):
        if term not in checker:
            print(f"Security surface check failed. check-secrets.py must include `{term}`.")
            return 1
    return 0


def check_pii_handling_surface() -> int:
    script = (ROOT / "scripts" / "check-pii-handling.py").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "security" / "data-handling.md").read_text(encoding="utf-8")
    app = (ROOT / "src" / "code_readiness_template" / "app.py").read_text(encoding="utf-8")

    for term in ("PII_FIELD_MARKERS", "[REDACTED-PII]", "send_default_pii=False"):
        if term not in script:
            print(f"Security surface check failed. check-pii-handling.py must include `{term}`.")
            return 1

    for term in ("[REDACTED-PII]", "Privacy Compliance", "privacy export", "privacy delete"):
        if term not in docs:
            print(f"Security surface check failed. data-handling.md must include `{term}`.")
            return 1

    for term in ("/privacy/retention", "/privacy/export", "/privacy/delete"):
        if term not in app:
            print(f"Security surface check failed. app.py must expose `{term}`.")
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
        check_local_secret_scanning,
        check_pii_handling_surface,
    ):
        result = check()
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

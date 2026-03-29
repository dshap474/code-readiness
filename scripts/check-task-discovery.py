from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    ROOT / ".github" / "labels.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "bug.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "feature.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "task.yml",
    ROOT / ".github" / "pull_request_template.md",
    ROOT / ".github" / "task-discovery.md",
    ROOT / ".github" / "workflows" / "backlog-health.yml",
    ROOT / ".github" / "proof" / "issues.json",
]
REQUIRED_PREFIXES = ("type/", "priority/", "area/")


def check_required_files() -> int:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    if not missing:
        return 0

    print("Task discovery check failed.")
    for path in missing:
        print(f"- Missing required file: {path}")
    return 1


def check_labels() -> int:
    labels = yaml.safe_load((ROOT / ".github" / "labels.yml").read_text(encoding="utf-8"))
    label_names = {item["name"] for item in labels.get("labels", [])}
    for prefix in REQUIRED_PREFIXES:
        if not any(label.startswith(prefix) for label in label_names):
            print(
                "Task discovery check failed. "
                f"labels.yml must include at least one `{prefix}` label."
            )
            return 1
    return 0


def check_issue_config() -> int:
    config = yaml.safe_load(
        (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
    )
    if config.get("blank_issues_enabled") is not False:
        print("Task discovery check failed. blank issues must be disabled by default.")
        return 1
    return 0


def check_pr_template() -> int:
    pr_template = (
        (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8").lower()
    )
    for section in ("summary", "validation", "risk"):
        if section not in pr_template:
            print(
                f"Task discovery check failed. pull_request_template.md must include `{section}`."
            )
            return 1
    return 0


def check_backlog_fixture() -> int:
    issues = json.loads((ROOT / ".github" / "proof" / "issues.json").read_text(encoding="utf-8"))
    for issue in issues:
        labels = set(issue.get("labels", []))
        for prefix in REQUIRED_PREFIXES:
            if not any(label.startswith(prefix) for label in labels):
                print(
                    "Task discovery check failed. "
                    "Every proof issue must include type, priority, and area labels."
                )
                return 1
        if "needs-triage" in labels:
            print("Task discovery check failed. Proof issues must not remain needs-triage.")
            return 1
    return 0


def main() -> int:
    for check in (
        check_required_files,
        check_labels,
        check_issue_config,
        check_pr_template,
        check_backlog_fixture,
    ):
        result = check()
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

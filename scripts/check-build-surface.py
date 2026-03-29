from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    ROOT / ".github" / "workflows" / "ci.yml",
    ROOT / ".github" / "workflows" / "pr-review.yml",
    ROOT / ".github" / "codex" / "prompts" / "review.md",
    ROOT / ".github" / "proof" / "ci-budget.json",
    ROOT / ".github" / "proof" / "pr-review-comment.md",
    ROOT / "AGENTS.md",
    ROOT / "README.md",
]


def check_required_files() -> int:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    if not missing:
        return 0

    print("Build surface check failed.")
    for path in missing:
        print(f"- Missing required file: {path}")
    return 1


def require_terms(text: str, terms: tuple[str, ...], message: str) -> int:
    for term in terms:
        if term not in text:
            print(f"{message} `{term}`.")
            return 1
    return 0


def check_ci_workflow() -> int:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    return require_terms(
        workflow,
        ("just ci", "build-metrics.json", "actions/upload-artifact"),
        "Build surface check failed. ci.yml must include",
    )


def check_ci_budget() -> int:
    budget = json.loads((ROOT / ".github" / "proof" / "ci-budget.json").read_text(encoding="utf-8"))
    if budget.get("workflow") != "ci" or budget.get("job") != "proof":
        print("Build surface check failed. ci-budget.json must target the ci proof job.")
        return 1
    if budget.get("artifact") != "build-metrics.json":
        print("Build surface check failed. ci-budget.json must point to build-metrics.json.")
        return 1
    if not isinstance(budget.get("max_seconds"), int) or budget["max_seconds"] <= 0:
        print("Build surface check failed. ci-budget.json must define a positive max_seconds.")
        return 1
    return 0


def check_pr_review_surface() -> int:
    workflow = (ROOT / ".github" / "workflows" / "pr-review.yml").read_text(encoding="utf-8")
    workflow_result = require_terms(
        workflow,
        ("openai/codex-action@v1", "prompt-file:", "pull_request"),
        "Build surface check failed. pr-review.yml must include",
    )
    if workflow_result != 0:
        return workflow_result

    review_fixture = (ROOT / ".github" / "proof" / "pr-review-comment.md").read_text(
        encoding="utf-8"
    )
    return require_terms(
        review_fixture,
        ("## Findings", "## Validation"),
        "Build surface check failed. pr-review-comment.md must include",
    )


def check_cli_docs() -> int:
    docs = (
        (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        + "\n"
        + (ROOT / "README.md").read_text(encoding="utf-8").lower()
    )
    return require_terms(
        docs,
        ("gh pr view", "gh run list"),
        "Build surface check failed. AGENTS.md or README.md must document",
    )


def main() -> int:
    for check in (
        check_required_files,
        check_ci_workflow,
        check_ci_budget,
        check_pr_review_surface,
        check_cli_docs,
    ):
        result = check()
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

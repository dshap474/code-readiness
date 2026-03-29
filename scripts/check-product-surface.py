from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    ROOT / "docs" / "product" / "analytics-events.yml",
    ROOT / "docs" / "product" / "experiments.yml",
    ROOT / "docs" / "product" / "error-pipeline.md",
    ROOT / ".github" / "workflows" / "error-to-insight.yml",
    ROOT / ".github" / "proof" / "error-event.json",
]
REQUIRED_EVENTS = {"widget_list_viewed", "widget_created", "widget_detail_viewed"}


def check_required_files() -> int:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    if not missing:
        return 0

    print("Product surface check failed.")
    for path in missing:
        print(f"- Missing required file: {path}")
    return 1


def check_event_contract() -> int:
    analytics = yaml.safe_load(
        (ROOT / "docs" / "product" / "analytics-events.yml").read_text(encoding="utf-8")
    )
    event_names = {item["name"] for item in analytics.get("events", [])}
    if REQUIRED_EVENTS - event_names:
        missing_events = ", ".join(sorted(REQUIRED_EVENTS - event_names))
        print(f"Product surface check failed. analytics-events.yml is missing: {missing_events}.")
        return 1

    experiments = yaml.safe_load(
        (ROOT / "docs" / "product" / "experiments.yml").read_text(encoding="utf-8")
    )
    if not experiments.get("experiments"):
        print(
            "Product surface check failed. "
            "experiments.yml must define at least one experiment contract."
        )
        return 1
    return 0


def check_runtime_instrumentation() -> int:
    source = (ROOT / "src" / "code_readiness_template" / "features" / "widgets.py").read_text(
        encoding="utf-8"
    )
    for event_name in REQUIRED_EVENTS:
        if event_name not in source:
            print(f"Product surface check failed. widgets.py must emit `{event_name}`.")
            return 1
    return 0


def check_error_pipeline() -> int:
    error_pipeline = (ROOT / "docs" / "product" / "error-pipeline.md").read_text(encoding="utf-8")
    for term in ("owner:", ".github/workflows/error-to-insight.yml"):
        if term not in error_pipeline:
            print(f"Product surface check failed. error-pipeline.md must mention `{term}`.")
            return 1
    return 0


def check_error_workflow() -> int:
    workflow = (ROOT / ".github" / "workflows" / "error-to-insight.yml").read_text(encoding="utf-8")
    for term in ("repository_dispatch", "labels:", "title:", "source:", "context:"):
        if term not in workflow:
            print(f"Product surface check failed. error-to-insight.yml must include `{term}`.")
            return 1
    return 0


def main() -> int:
    for check in (
        check_required_files,
        check_event_contract,
        check_runtime_instrumentation,
        check_error_pipeline,
        check_error_workflow,
    ):
        result = check()
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

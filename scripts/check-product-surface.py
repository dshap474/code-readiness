from __future__ import annotations

import ast
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


def _feature_flag_catalog() -> dict[str, dict[str, str]]:
    payload = yaml.safe_load(
        (ROOT / "docs" / "product" / "experiments.yml").read_text(encoding="utf-8")
    )
    catalog: dict[str, dict[str, str]] = {}
    for item in payload.get("experiments", []):
        flag_key = item.get("feature_flag")
        if not flag_key:
            continue
        catalog[flag_key] = {
            "status": str(item.get("status", "")).strip(),
            "name": str(item.get("name", flag_key)).strip(),
        }
    return catalog


def _defined_feature_flags() -> dict[str, str]:
    source = (ROOT / "src" / "code_readiness_template" / "feature_flags.py").read_text(
        encoding="utf-8"
    )
    module = ast.parse(source)
    defined: dict[str, str] = {}
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "FeatureFlag":
            continue
        key: str | None = None
        lifecycle = "active"
        for keyword in node.keywords:
            if keyword.arg == "key" and isinstance(keyword.value, ast.Constant):
                key = str(keyword.value.value)
            if keyword.arg == "lifecycle" and isinstance(keyword.value, ast.Constant):
                lifecycle = str(keyword.value.value)
        if key:
            defined[key] = lifecycle
    return defined


def _flag_usage_count(flag_key: str) -> int:
    total = 0
    for path in ROOT.rglob("*.py"):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        if ".venv" in path.parts:
            continue
        total += path.read_text(encoding="utf-8").count(flag_key)
    return total


def check_feature_flag_stale_detection() -> int:
    source = (ROOT / "src" / "code_readiness_template" / "feature_flags.py").read_text(
        encoding="utf-8"
    )
    for term in ("stale_feature_flags", "cleanup_by", "introduced_on", "owner"):
        if term not in source:
            print(
                "Product surface check failed. "
                f"feature_flags.py must include `{term}` for stale-flag detection."
            )
            return 1
    return 0


def check_feature_flag_lifecycle() -> int:
    catalog = _feature_flag_catalog()
    defined = _defined_feature_flags()

    undocumented = sorted(set(defined) - set(catalog))
    if undocumented:
        print(
            "Product surface check failed. experiments.yml must document feature flags: "
            + ", ".join(undocumented)
            + "."
        )
        return 1

    missing = sorted(set(catalog) - set(defined))
    if missing:
        print(
            "Product surface check failed. feature_flags.py must define documented flags: "
            + ", ".join(missing)
            + "."
        )
        return 1

    for flag_key, metadata in catalog.items():
        usage_count = _flag_usage_count(flag_key)
        if usage_count < 2:
            print(
                "Product surface check failed. "
                f"feature flag `{flag_key}` must be referenced "
                "in code or tests beyond its definition."
            )
            return 1
        if metadata["status"] == "dormant":
            print(
                "Product surface check failed. "
                f"feature flag `{flag_key}` is still documented as dormant; "
                "remove it or mark it active/cleanup."
            )
            return 1
        if metadata["status"] == "cleanup" and defined[flag_key] != "cleanup":
            print(
                "Product surface check failed. "
                f"feature flag `{flag_key}` must use lifecycle='cleanup' in feature_flags.py."
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
        check_feature_flag_stale_detection,
        check_feature_flag_lifecycle,
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

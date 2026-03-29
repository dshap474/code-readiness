from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    ROOT / "docs" / "observability" / "README.md",
    ROOT / "docs" / "observability" / "schema.md",
    ROOT / "runbooks" / "incident.md",
    ROOT / "runbooks" / "post-deploy.md",
    ROOT / "monitoring" / "alerts" / "alerts.yaml",
    ROOT / "monitoring" / "dashboards" / "README.md",
    ROOT / "monitoring" / "quality" / "README.md",
    ROOT / "monitoring" / "profiling" / "README.md",
    ROOT / ".github" / "workflows" / "observability-check.yml",
    ROOT / "scripts" / "post-deploy-check.sh",
    ROOT / "scripts" / "profile-widget-routes.sh",
]


def check_required_files() -> int:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    if not missing:
        return 0

    print("Observability contract check failed.")
    for path in missing:
        print(f"- Missing required file: {path}")
    return 1


def require_terms(text: str, terms: tuple[str, ...], message: str) -> int:
    for term in terms:
        if term not in text:
            print(f"{message} `{term}`.")
            return 1
    return 0


def check_signal_map() -> int:
    readme = (ROOT / "docs" / "observability" / "README.md").read_text(encoding="utf-8").lower()
    return require_terms(
        readme,
        ("logs", "metrics", "traces", "sentry", "quality report"),
        "Observability contract check failed. docs/observability/README.md must mention",
    )


def check_alert_contract() -> int:
    alerts = yaml.safe_load(
        (ROOT / "monitoring" / "alerts" / "alerts.yaml").read_text(encoding="utf-8")
    )
    if not isinstance(alerts, dict) or not alerts.get("alerts"):
        print(
            "Observability contract check failed. "
            "monitoring/alerts/alerts.yaml needs at least one alert."
        )
        return 1

    for alert in alerts["alerts"]:
        if not alert.get("owner") or not alert.get("route"):
            print("Observability contract check failed. Every alert needs owner and route fields.")
            return 1
    return 0


def check_quality_contract() -> int:
    dashboards = (ROOT / "monitoring" / "dashboards" / "README.md").read_text(encoding="utf-8")
    if "monitoring/quality/README.md" not in dashboards:
        print(
            "Observability contract check failed. "
            "monitoring/dashboards/README.md must point to monitoring/quality/README.md."
        )
        return 1

    quality = (ROOT / "monitoring" / "quality" / "README.md").read_text(encoding="utf-8").lower()
    return require_terms(
        quality,
        ("build-metrics.json", "coverage", "just ci"),
        "Observability contract check failed. monitoring/quality/README.md must mention",
    )


def check_profiling_and_post_deploy() -> int:
    profiling = (ROOT / "monitoring" / "profiling" / "README.md").read_text(encoding="utf-8")
    profiling_result = require_terms(
        profiling,
        ("just profile", "widget-routes.prof"),
        "Observability contract check failed. monitoring/profiling/README.md must mention",
    )
    if profiling_result != 0:
        return profiling_result

    post_deploy = (ROOT / "runbooks" / "post-deploy.md").read_text(encoding="utf-8")
    if "just post-deploy-check" not in post_deploy:
        print(
            "Observability contract check failed. "
            "runbooks/post-deploy.md must reference just post-deploy-check."
        )
        return 1
    return 0


def check_workflow() -> int:
    workflow = (ROOT / ".github" / "workflows" / "observability-check.yml").read_text(
        encoding="utf-8"
    )
    if "scripts/check-observability.py" not in workflow:
        print(
            "Observability contract check failed. "
            "observability-check workflow must run scripts/check-observability.py."
        )
        return 1
    return 0


def main() -> int:
    for check in (
        check_required_files,
        check_signal_map,
        check_alert_contract,
        check_quality_contract,
        check_profiling_and_post_deploy,
        check_workflow,
    ):
        result = check()
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

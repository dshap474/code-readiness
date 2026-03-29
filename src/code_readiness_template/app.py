from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from code_readiness_template.config import get_settings
from code_readiness_template.db import ping_database
from code_readiness_template.features import widgets_router
from code_readiness_template.observability import (
    configure_observability,
    log_runtime_event,
    metrics_response,
)


class PrivacyActionResponse(BaseModel):
    status: str
    action: str
    retention_days: int
    contact_email: str


def healthcheck() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "alive",
        "release": settings.app_release or "local",
    }


def readiness() -> dict[str, str]:
    settings = get_settings()
    try:
        ping_database(settings)
    except Exception as exc:
        log_runtime_event("readiness.failed", error_type=type(exc).__name__)
        raise HTTPException(status_code=503, detail="Database not ready.") from exc
    return {
        "status": "ok",
        "database": "ready",
        "release": settings.app_release or "local",
    }


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Code Readiness Template API",
        version="0.1.0",
        description=(
            "A Codex-native FastAPI template repo used to exercise code-readiness sections."
        ),
    )
    configure_observability(app, settings)

    app.get("/healthz")(healthcheck)
    app.get("/readyz")(readiness)
    app.get("/metrics", include_in_schema=False)(metrics_response)
    app.get("/privacy/retention", response_model=PrivacyActionResponse)(
        lambda: PrivacyActionResponse(
            status="ok",
            action="retention",
            retention_days=settings.privacy_data_retention_days,
            contact_email=settings.privacy_contact_email,
        )
    )
    app.post("/privacy/export", response_model=PrivacyActionResponse)(
        lambda: _privacy_action_response("export", settings)
    )
    app.post("/privacy/delete", response_model=PrivacyActionResponse)(
        lambda: _privacy_action_response("delete", settings)
    )
    app.include_router(widgets_router)
    return app


def _privacy_action_response(action: str, settings) -> PrivacyActionResponse:
    enabled = {
        "export": settings.privacy_export_enabled,
        "delete": settings.privacy_delete_enabled,
    }[action]
    if not enabled:
        log_runtime_event(f"privacy.{action}_disabled")
        raise HTTPException(
            status_code=503,
            detail=f"Privacy {action} workflow is temporarily disabled.",
        )
    log_runtime_event(
        f"privacy.{action}_requested",
        retention_days=settings.privacy_data_retention_days,
        privacy_contact_email=settings.privacy_contact_email,
    )
    return PrivacyActionResponse(
        status="accepted",
        action=action,
        retention_days=settings.privacy_data_retention_days,
        contact_email=settings.privacy_contact_email,
    )


app = create_app()

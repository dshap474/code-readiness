from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from prometheus_client import Counter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, String, desc, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from code_readiness_template.analytics import emit_product_event
from code_readiness_template.db import Base, get_session
from code_readiness_template.observability import log_runtime_event

router = APIRouter(prefix="/api/v1/widgets", tags=["widgets"])
SessionDep = Annotated[Session, Depends(get_session)]
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
WIDGET_ACTIONS_TOTAL = Counter(
    "code_readiness_widget_actions_total",
    "Widget-specific action counts for the template service.",
    ("action",),
)


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )


class WidgetCreate(BaseModel):
    name: str


class WidgetRead(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def slugify_widget_name(name: str) -> str:
    normalized = SLUG_PATTERN.sub("-", name.strip().lower()).strip("-")
    return normalized or "widget"


def build_widget_slug(name: str) -> str:
    return slugify_widget_name(name)


@router.get("", response_model=list[WidgetRead])
def list_widgets(session: SessionDep) -> Sequence[Widget]:
    statement = select(Widget).order_by(desc(Widget.created_at))
    widgets = session.scalars(statement).all()
    WIDGET_ACTIONS_TOTAL.labels("list").inc()
    log_runtime_event("widget.listed", widget_count=len(widgets))
    emit_product_event("widget_list_viewed", properties={"widget_count": len(widgets)})
    return widgets


@router.post("", response_model=WidgetRead, status_code=status.HTTP_201_CREATED)
def create_widget(payload: WidgetCreate, session: SessionDep) -> Widget:
    slug = build_widget_slug(payload.name)
    existing = session.scalar(select(Widget).where(Widget.slug == slug))
    if existing is not None:
        log_runtime_event("widget.create_conflict", slug=slug)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Widget slug already exists.",
        )

    widget = Widget(name=payload.name, slug=slug)
    session.add(widget)
    session.commit()
    session.refresh(widget)
    WIDGET_ACTIONS_TOTAL.labels("create").inc()
    log_runtime_event("widget.created", widget_id=widget.id, slug=widget.slug)
    emit_product_event(
        "widget_created",
        properties={"widget_id": widget.id, "slug": widget.slug},
        distinct_id=widget.slug,
    )
    return widget


@router.get("/{widget_id}", response_model=WidgetRead)
def get_widget(widget_id: int, session: SessionDep) -> Widget:
    widget = session.get(Widget, widget_id)
    if widget is None:
        log_runtime_event("widget.lookup_missing", widget_id=widget_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found.")
    WIDGET_ACTIONS_TOTAL.labels("get").inc()
    log_runtime_event("widget.retrieved", widget_id=widget.id, slug=widget.slug)
    emit_product_event(
        "widget_detail_viewed",
        properties={"widget_id": widget.id, "slug": widget.slug},
        distinct_id=widget.slug,
    )
    return widget

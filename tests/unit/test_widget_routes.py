from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from code_readiness_template.features.widgets import (
    Widget,
    WidgetCreate,
    create_widget,
    get_widget,
    list_widgets,
)


class FakeScalarResult:
    def __init__(self, values: list[Widget]) -> None:
        self._values = values

    def all(self) -> list[Widget]:
        return self._values


class FakeSession:
    def __init__(self) -> None:
        self.widgets: dict[int, Widget] = {}
        self.scalar_result: Widget | None = None
        self.next_id = 1

    def scalars(self, _statement: object) -> FakeScalarResult:
        return FakeScalarResult(list(self.widgets.values()))

    def scalar(self, _statement: object) -> Widget | None:
        return self.scalar_result

    def add(self, widget: Widget) -> None:
        self.widgets[self.next_id] = widget

    def commit(self) -> None:
        return None

    def refresh(self, widget: Widget) -> None:
        widget.id = self.next_id
        widget.created_at = datetime.now(UTC)
        self.next_id += 1

    def get(self, _model: object, widget_id: int) -> Widget | None:
        return self.widgets.get(widget_id)


def test_list_widgets_returns_session_results(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    widget = Widget(name="Alpha", slug="alpha")
    widget.id = 1
    widget.created_at = datetime.now(UTC)
    session.widgets[widget.id] = widget
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.emit_product_event",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.log_runtime_event",
        lambda *_args, **_kwargs: None,
    )

    results = list_widgets(cast(Session, session))
    assert [item.slug for item in results] == ["alpha"]


def test_create_widget_persists_new_widget(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    emitted: list[str] = []
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.is_feature_enabled",
        lambda _flag_key: True,
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.emit_product_event",
        lambda event_name, **_kwargs: emitted.append(event_name),
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.log_runtime_event",
        lambda *_args, **_kwargs: None,
    )

    widget = create_widget(WidgetCreate(name="Alpha Widget"), cast(Session, session))
    assert widget.slug == "alpha-widget"
    assert emitted == ["widget_created"]


def test_create_widget_raises_conflict_for_existing_slug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    session.scalar_result = Widget(name="Existing", slug="existing")
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.is_feature_enabled",
        lambda _flag_key: True,
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.emit_product_event",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.log_runtime_event",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(HTTPException) as exc_info:
        create_widget(WidgetCreate(name="Existing"), cast(Session, session))

    assert exc_info.value.status_code == 409


def test_create_widget_respects_feature_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.is_feature_enabled",
        lambda _flag_key: False,
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.emit_product_event",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.log_runtime_event",
        lambda *_args, **kwargs: kwargs,
    )

    with pytest.raises(HTTPException) as exc_info:
        create_widget(WidgetCreate(name="Disabled"), cast(Session, session))

    assert exc_info.value.status_code == 503


def test_get_widget_returns_existing_widget(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    widget = Widget(name="Alpha", slug="alpha")
    widget.id = 1
    widget.created_at = datetime.now(UTC)
    session.widgets[1] = widget
    emitted: list[str] = []
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.emit_product_event",
        lambda event_name, **_kwargs: emitted.append(event_name),
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.log_runtime_event",
        lambda *_args, **_kwargs: None,
    )

    result = get_widget(1, cast(Session, session))
    assert result.slug == "alpha"
    assert emitted == ["widget_detail_viewed"]


def test_get_widget_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.emit_product_event",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "code_readiness_template.features.widgets.log_runtime_event",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_widget(999, cast(Session, session))

    assert exc_info.value.status_code == 404

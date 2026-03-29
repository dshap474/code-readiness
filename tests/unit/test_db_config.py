from __future__ import annotations

import pytest

from code_readiness_template.config import Settings
from code_readiness_template.db import get_session, ping_database


def test_settings_populate_database_url_when_missing() -> None:
    settings = Settings(
        postgres_db="widgets",
        postgres_user="reader",
        postgres_password="secret",
        database_url=None,
    )
    assert settings.database_url == "postgresql+psycopg://reader:secret@127.0.0.1:5432/widgets"


def test_settings_preserve_explicit_database_url() -> None:
    settings = Settings(database_url="postgresql+psycopg://custom")
    assert settings.database_url == "postgresql+psycopg://custom"


def test_get_session_uses_session_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    session_object = object()

    class FakeContext:
        def __enter__(self) -> object:
            return session_object

        def __exit__(self, *_args: object) -> None:
            return None

    def fake_settings() -> Settings:
        return Settings(database_url="postgresql+psycopg://fake")

    def fake_factory(_database_url: str):
        def factory() -> FakeContext:
            return FakeContext()

        return factory

    monkeypatch.setattr("code_readiness_template.db.get_settings", fake_settings)
    monkeypatch.setattr("code_readiness_template.db.get_session_factory", fake_factory)

    yielded = next(get_session())
    assert yielded is session_object


def test_ping_database_uses_engine_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []

    class FakeConnection:
        def __enter__(self) -> FakeConnection:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def execute(self, statement: object) -> None:
            executed.append(str(statement))

    class FakeEngine:
        def connect(self) -> FakeConnection:
            return FakeConnection()

    monkeypatch.setattr("code_readiness_template.db.get_engine", lambda _database_url: FakeEngine())

    ping_database(Settings(database_url="postgresql+psycopg://fake"))
    assert executed == ["SELECT 1"]

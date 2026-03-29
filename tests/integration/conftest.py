from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from docker import from_env
from docker.errors import DockerException
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer

from code_readiness_template.config import get_settings
from code_readiness_template.db import get_engine, get_session_factory

ROOT = Path(__file__).resolve().parents[2]


def _to_psycopg_url(url: str) -> str:
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


def docker_available() -> bool:
    try:
        client = from_env()
        return bool(client.ping())
    except DockerException:
        return False


@pytest.fixture(scope="session")
def database_url() -> Generator[str]:
    if not docker_available():
        raise pytest.skip.Exception("Docker daemon unavailable for integration tests.")
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield _to_psycopg_url(postgres.get_connection_url())


@pytest.fixture(scope="session")
def migrated_database(database_url: str) -> Generator[str]:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    yield database_url


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, migrated_database: str) -> Generator[TestClient]:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_RELEASE", "test-suite")
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    from code_readiness_template.app import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def session_factory(monkeypatch: pytest.MonkeyPatch, migrated_database: str):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_RELEASE", "test-suite")
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    settings = get_settings()
    return get_session_factory(settings.database_url)

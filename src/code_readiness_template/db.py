from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from code_readiness_template.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


@lru_cache(maxsize=4)
def get_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(database_url),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def get_session() -> Iterator[Session]:
    settings = get_settings()
    session_factory = get_session_factory(settings.database_url)
    with session_factory() as session:
        yield session


def ping_database(settings: Settings) -> None:
    with get_engine(settings.database_url).connect() as connection:
        connection.execute(text("SELECT 1"))

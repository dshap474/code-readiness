from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_release: str | None = None
    postgres_db: str = "code_readiness"
    postgres_user: str = "code_readiness"
    postgres_password: str = "code_readiness"
    database_url: str | None = None
    sentry_dsn: str | None = None
    otel_exporter_otlp_endpoint: str | None = None
    posthog_api_key: str | None = None
    posthog_host: str = "https://us.i.posthog.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def populate_database_url(self) -> Settings:
        if self.database_url is None:
            self.database_url = (
                "postgresql+psycopg://"
                f"{self.postgres_user}:{self.postgres_password}"
                f"@127.0.0.1:5432/{self.postgres_db}"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

"""Application configuration management."""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    admin_ids: list[int]
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    pay_provider: str
    pay_return_url: str
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: Any) -> list[int]:
        """Convert a comma-separated string of admin IDs into a list of integers."""

        if value is None:
            return []
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",")]
            return [int(item) for item in items if item]
        if isinstance(value, list):
            return [int(item) for item in value]
        raise TypeError("admin_ids must be provided as a comma-separated string or list of integers")


@lru_cache
def get_config() -> Settings:
    """Return the cached application settings instance."""

    return Settings()

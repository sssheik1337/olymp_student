"""Configuration module for pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    bot_token: str
    admin_ids: list[int] = []
    database_url: str

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = BotSettings()

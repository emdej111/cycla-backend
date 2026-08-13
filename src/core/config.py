from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Cycla API"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+psycopg2://cycla:cycla@localhost:5432/cycla"

    # JWT / auth
    secret_key: str = "CHANGE_ME_dev_only_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Field-level encryption at rest (Fernet key, 32 url-safe base64 bytes)
    encryption_key: str = "z3nJZ7q1s0m3sM6f6f6QeXGz3nJZ7q1s0m3sM6f6f4="

    # Anthropic / Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # Personalization
    min_cycles_for_personalization: int = 3

    # CORS
    cors_origins: list[str] = ["*"]

    # Uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Quran Progress Tracking API"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://quran:quran@localhost:5432/quran",
        description="Async SQLAlchemy DSN. Use sqlite+aiosqlite:///:memory: for tests.",
    )

    # Security
    jwt_secret_key: str = Field(default="CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, description="Default requests/minute per IP")
    rate_limit_auth_per_minute: int = Field(default=10, description="Auth endpoint requests/minute per IP")


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""
Application settings — loaded from environment variables / .env file.

Uses pydantic-settings for type-safe, validated configuration.
All secrets are read from environment; never hard-coded.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the moments4u backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──
    app_name: str = "moments4u"
    app_env: str = "development"  # development | staging | production
    app_secret_key: str = "CHANGE_ME"
    app_url: str = "http://localhost:3000"
    debug: bool = True

    # ── Database ──
    database_url: str = "postgresql+asyncpg://moments4u:moments4u_dev@localhost:5432/moments4u"
    database_url_sync: str = "postgresql://moments4u:moments4u_dev@localhost:5432/moments4u"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── S3 / MinIO ──
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "moments4u-photos"
    s3_region: str = "us-east-1"

    # ── JWT ──
    jwt_secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ── Face Recognition ──
    face_match_threshold: float = 0.55
    face_min_confidence: float = 0.6
    face_min_size: int = 50

    # ── Cleanup ──
    photo_retention_days: int = 7
    cleanup_cron_hour: int = 2

    # ── CORS ──
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — created once per process."""
    return Settings()

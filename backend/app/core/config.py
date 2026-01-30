"""
Application configuration using pydantic-settings.
Loads from environment variables and .env file.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        ...,
        description="PostgreSQL connection string with PostGIS",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery",
    )

    # DigitalOcean Spaces
    do_spaces_region: str = Field(default="sgp1")
    do_spaces_bucket: str = Field(...)
    do_spaces_key: str = Field(...)
    do_spaces_secret: str = Field(...)
    do_spaces_endpoint: Optional[str] = Field(default=None)

    @field_validator("do_spaces_endpoint", mode="before")
    @classmethod
    def build_spaces_endpoint(cls, v, info):
        if v:
            return v
        region = info.data.get("do_spaces_region", "sgp1")
        return f"https://{region}.digitaloceanspaces.com"

    # Sentinel Hub
    sentinelhub_client_id: str = Field(...)
    sentinelhub_client_secret: str = Field(...)
    sentinelhub_base_url: str = Field(
        default="https://services.sentinel-hub.com"
    )

    # Tile Server (optional)
    tile_server_base_url: Optional[str] = Field(default=None)

    # Application
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Model Cache
    model_cache_dir: str = Field(default="./data/cache/models")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def spaces_public_url(self) -> str:
        """Public URL for accessing Spaces objects."""
        return f"https://{self.do_spaces_bucket}.{self.do_spaces_region}.digitaloceanspaces.com"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

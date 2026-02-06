"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "VALLORYS"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://vallorys:vallorys@localhost:5432/vallorys"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")
    redis_cache_ttl: int = 86400  # 24 hours

    # Auth
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # External APIs
    dvf_api_url: str = "https://api.dvf.etalab.gouv.fr"
    dvf_api_timeout: int = 30

    # AI
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Rate limiting
    rate_limit_valuation: int = 50
    rate_limit_fieldpack: int = 30
    rate_limit_objection: int = 100

    # Observability
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"

    # Multi-tenant
    default_tenant_schema: str = "public"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

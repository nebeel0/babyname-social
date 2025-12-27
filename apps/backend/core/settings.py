from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, field_validator
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
    APP_NAME: str = "Baby Names Social Network"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Database - Main (names, popularity, references)
    NAMES_DB_USER: str = "postgres"
    NAMES_DB_PASSWORD: str = "postgres"
    NAMES_DB_HOST: str = "localhost"
    POSTGRES_NAMES_PORT: int = 15434  # Changed to match .env variable name
    NAMES_DB_NAME: str = "babynames_db"

    # Database - Users (authentication, profiles)
    USERS_DB_USER: str = "postgres"
    USERS_DB_PASSWORD: str = "postgres"
    USERS_DB_HOST: str = "localhost"
    POSTGRES_USERS_PORT: int = 15433  # Changed to match .env variable name
    USERS_DB_NAME: str = "users_db"

    # Redis - Cache
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 16381
    REDIS_CACHE_DB: int = 0

    # Redis - Sessions
    REDIS_SESSIONS_HOST: str = "localhost"
    REDIS_SESSIONS_PORT: int = 16382
    REDIS_SESSIONS_DB: int = 0

    # Keep backward compatibility
    @property
    def NAMES_DB_PORT(self) -> int:
        return self.POSTGRES_NAMES_PORT

    @property
    def USERS_DB_PORT(self) -> int:
        return self.POSTGRES_USERS_PORT

    # Authentication
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Email (for user verification)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    # External APIs (for data enrichment)
    OPENAI_API_KEY: str | None = None  # For name meaning generation

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def names_database_url(self) -> str:
        """Construct async PostgreSQL URL for names database."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.NAMES_DB_USER,
                password=self.NAMES_DB_PASSWORD,
                host=self.NAMES_DB_HOST,
                port=self.NAMES_DB_PORT,
                path=self.NAMES_DB_NAME,
            )
        )

    @property
    def users_database_url(self) -> str:
        """Construct async PostgreSQL URL for users database."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.USERS_DB_USER,
                password=self.USERS_DB_PASSWORD,
                host=self.USERS_DB_HOST,
                port=self.USERS_DB_PORT,
                path=self.USERS_DB_NAME,
            )
        )

    @property
    def redis_cache_url(self) -> str:
        """Construct Redis URL for caching."""
        return str(
            RedisDsn.build(
                scheme="redis",
                host=self.REDIS_CACHE_HOST,
                port=self.REDIS_CACHE_PORT,
                path=str(self.REDIS_CACHE_DB),
            )
        )

    @property
    def redis_sessions_url(self) -> str:
        """Construct Redis URL for sessions."""
        return str(
            RedisDsn.build(
                scheme="redis",
                host=self.REDIS_SESSIONS_HOST,
                port=self.REDIS_SESSIONS_PORT,
                path=str(self.REDIS_SESSIONS_DB),
            )
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

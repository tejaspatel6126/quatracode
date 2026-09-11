"""
Centralized application configuration.
All settings loaded from environment variables — no hardcoded secrets.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "AI-Powered Web Security Auditor"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-to-a-long-random-secret-key"

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "mysql+pymysql://user:password@localhost:3306/web_security_auditor"
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # ── Scanner Network Security (Phase 03) ──────────────────────────────────
    # Allowed URL schemes for scan targets
    ALLOWED_SCHEMES: str = "http,https"
    # Allowed ports (empty string = only default 80/443 per scheme)
    ALLOWED_PORTS: str = "80,443"
    # DNS resolution timeout in seconds
    DNS_TIMEOUT: float = 5.0
    # TCP connect timeout in seconds (SECURITY.md §15)
    CONNECT_TIMEOUT: float = 5.0
    # Response read timeout in seconds
    READ_TIMEOUT: float = 10.0
    # Overall per-request wall-clock timeout in seconds
    REQUEST_TIMEOUT: float = 30.0
    # Maximum redirects to follow (SECURITY.md §15)
    MAX_REDIRECTS: int = 10
    # Maximum response body bytes to read into memory (5 MB default)
    MAX_RESPONSE_SIZE: int = 5 * 1024 * 1024

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── AI (Phase 08 — disabled in Phase 01) ─────────────────────────────────
    AI_ENABLED: bool = False
    AI_PROVIDER: str = ""
    AI_MODEL: str = ""
    AI_API_KEY: str = ""
    AI_TIMEOUT: int = 30
    AI_MAX_TOKENS: int = 1000

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list, stripping whitespace."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()

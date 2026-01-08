"""Web application configuration.

Provides environment-aware configuration for the JARVIS web API.
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class CORSConfig:
    """CORS configuration."""

    allow_origins: List[str] = field(default_factory=list)
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: ["*"])
    allow_headers: List[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_env(cls) -> "CORSConfig":
        """Create CORS config from environment variables."""
        env = os.getenv("JARVIS_ENV", "development")

        if env == "production":
            # Production: restrict origins
            origins_str = os.getenv("CORS_ORIGINS", "")
            origins = [o.strip() for o in origins_str.split(",") if o.strip()]
            if not origins:
                origins = ["https://jarvis.kaneko-ai.dev"]
            return cls(allow_origins=origins)
        else:
            # Development: allow all
            return cls(allow_origins=["*"])


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    requests_per_minute: int = 100
    authenticated_rpm: int = 1000
    burst_limit: int = 20

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """Create rate limit config from environment."""
        return cls(
            requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "100")),
            authenticated_rpm=int(os.getenv("RATE_LIMIT_AUTH_RPM", "1000")),
            burst_limit=int(os.getenv("RATE_LIMIT_BURST", "20")),
        )


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = ""
    pool_size: int = 5
    max_overflow: int = 10

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database config from environment."""
        return cls(
            url=os.getenv("DATABASE_URL", "sqlite:///jarvis.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        )


@dataclass
class SecurityConfig:
    """Security configuration."""

    secret_key: str = ""
    token_expiry_hours: int = 24
    require_auth: bool = False

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Create security config from environment."""
        env = os.getenv("JARVIS_ENV", "development")
        return cls(
            secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
            token_expiry_hours=int(os.getenv("TOKEN_EXPIRY_HOURS", "24")),
            require_auth=env == "production",
        )


@dataclass
class AppConfig:
    """Application configuration."""

    env: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create app config from environment."""
        env = os.getenv("JARVIS_ENV", "development")
        return cls(
            env=env,
            debug=env == "development",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO" if env == "production" else "DEBUG"),
            cors=CORSConfig.from_env(),
            rate_limit=RateLimitConfig.from_env(),
            database=DatabaseConfig.from_env(),
            security=SecurityConfig.from_env(),
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "development"


# Global config instance (singleton)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get application configuration (singleton).

    Returns:
        AppConfig instance with current configuration
    """
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset configuration (for testing)."""
    global _config
    _config = None

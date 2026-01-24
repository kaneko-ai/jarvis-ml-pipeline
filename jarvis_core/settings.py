import os
from dataclasses import dataclass, field


class MissingSettingError(Exception):
    """Exception raised when a mandatory setting is missing."""

    pass


@dataclass
class CoreSettings:
    """Core settings for JARVIS."""

    # API Keys
    ncbi_api_key: str = field(default_factory=lambda: os.getenv("NCBI_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    # Environment
    env: str = field(default_factory=lambda: os.getenv("JARVIS_ENV", "development"))

    # Paths
    cache_dir: str = field(default_factory=lambda: os.getenv("JARVIS_CACHE_DIR", ".cache"))

    def validate(self):
        """Validate that mandatory settings are present."""
        # NCBI_API_KEY is usually mandatory for production-like runs
        if not self.ncbi_api_key and self.env == "production":
            raise MissingSettingError("NCBI_API_KEY is required in production environment.")

        # Add other validations as needed
        pass


# Global settings instance
_settings = None


def get_settings() -> CoreSettings:
    global _settings
    if _settings is None:
        _settings = CoreSettings()
        _settings.validate()
    return _settings

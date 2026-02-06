"""Operations configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpsConfig:
    """Configuration for ops layer."""

    environment: str = "dev"
    enable_audit: bool = True


def load_config() -> OpsConfig:
    """Load operations configuration.

    Returns:
        OpsConfig with defaults.
    """
    return OpsConfig()


__all__ = ["OpsConfig", "load_config"]

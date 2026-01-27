"""Source Adapter Registry (Phase 29).

Manages available data sources.
"""

from __future__ import annotations

import logging
from typing import Dict, Type
from jarvis_core.sources.base import SourceAdapter

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Registry for Source Adapters."""

    _adapters: Dict[str, Type[SourceAdapter]] = {}
    _instances: Dict[str, SourceAdapter] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a source adapter."""

        def wrapper(adapter_cls: Type[SourceAdapter]):
            cls._adapters[name] = adapter_cls
            return adapter_cls

        return wrapper

    @classmethod
    def get_adapter(cls, name: str) -> SourceAdapter:
        """Get or instantiate an adapter by name."""
        if name in cls._instances:
            return cls._instances[name]

        if name not in cls._adapters:
            raise ValueError(f"Unknown source adapter: {name}")

        # Instantiate
        adapter_cls = cls._adapters[name]
        instance = adapter_cls()
        cls._instances[name] = instance
        logger.info(f"Initialized source adapter: {name}")
        return instance

    @classmethod
    def list_sources(cls) -> list[str]:
        """List available source names."""
        return list(cls._adapters.keys())

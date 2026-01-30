"""Plugin System for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 3.1: プラグインシステム
Provides extensible plugin architecture for custom functionality.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Plugin types."""

    SOURCE = "source"  # Data source plugin
    ANALYZER = "analyzer"  # Analysis plugin
    EXPORTER = "exporter"  # Export format plugin
    INTEGRATION = "integration"  # External service integration
    CUSTOM = "custom"  # Custom functionality


class PluginStatus(Enum):
    """Plugin status."""

    REGISTERED = "registered"
    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str
    version: str
    plugin_type: PluginType
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    status: PluginStatus = PluginStatus.REGISTERED
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.plugin_type.value,
            "description": self.description,
            "author": self.author,
            "status": self.status.value,
        }


class Plugin(ABC):
    """Base class for all plugins."""

    # Plugin metadata - override in subclass
    NAME: str = "base_plugin"
    VERSION: str = "1.0.0"
    PLUGIN_TYPE: PluginType = PluginType.CUSTOM
    DESCRIPTION: str = ""
    AUTHOR: str = ""
    DEPENDENCIES: list[str] = []

    def __init__(self):
        self._initialized = False

    @classmethod
    def get_info(cls) -> PluginInfo:
        """Get plugin info from class attributes."""
        return PluginInfo(
            name=cls.NAME,
            version=cls.VERSION,
            plugin_type=cls.PLUGIN_TYPE,
            description=cls.DESCRIPTION,
            author=cls.AUTHOR,
            dependencies=cls.DEPENDENCIES,
        )

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin.

        Returns:
            True if initialization successful.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the plugin's main functionality."""
        pass

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized


class SourcePlugin(Plugin):
    """Base class for data source plugins."""

    PLUGIN_TYPE = PluginType.SOURCE

    @abstractmethod
    def search(self, query: str, **kwargs) -> list[dict]:
        """Search for items."""
        pass

    @abstractmethod
    def fetch(self, item_id: str, **kwargs) -> dict | None:
        """Fetch a specific item."""
        pass

    def execute(self, action: str = "search", **kwargs) -> Any:
        """Execute source action."""
        if action == "search":
            return self.search(kwargs.get("query", ""), **kwargs)
        elif action == "fetch":
            return self.fetch(kwargs.get("item_id", ""), **kwargs)
        raise ValueError(f"Unknown action: {action}")


class AnalyzerPlugin(Plugin):
    """Base class for analyzer plugins."""

    PLUGIN_TYPE = PluginType.ANALYZER

    @abstractmethod
    def analyze(self, data: Any, **kwargs) -> dict[str, Any]:
        """Analyze data."""
        pass

    def execute(self, data: Any = None, **kwargs) -> dict[str, Any]:
        return self.analyze(data, **kwargs)


class ExporterPlugin(Plugin):
    """Base class for exporter plugins."""

    PLUGIN_TYPE = PluginType.EXPORTER

    @abstractmethod
    def export(self, data: Any, output_path: Path | None = None, **kwargs) -> str:
        """Export data to format.

        Returns:
            Exported content or path to file.
        """
        pass

    def execute(self, data: Any = None, **kwargs) -> str:
        return self.export(data, **kwargs)


class PluginRegistry:
    """Central registry for all plugins."""

    def __init__(self):
        self._plugins: dict[str, type[Plugin]] = {}
        self._instances: dict[str, Plugin] = {}
        self._hooks: dict[str, list[Callable]] = {}

    def register(self, plugin_class: type[Plugin]) -> bool:
        """Register a plugin class.

        Args:
            plugin_class: Plugin class to register.

        Returns:
            True if registration successful.
        """
        try:
            info = plugin_class.get_info()

            if info.name in self._plugins:
                logger.warning(f"Plugin {info.name} already registered, replacing")

            self._plugins[info.name] = plugin_class
            logger.info(f"Registered plugin: {info.name} v{info.version}")
            return True

        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            return False

    def unregister(self, name: str) -> bool:
        """Unregister a plugin."""
        if name in self._plugins:
            # Cleanup instance if exists
            if name in self._instances:
                self._instances[name].cleanup()
                del self._instances[name]

            del self._plugins[name]
            logger.info(f"Unregistered plugin: {name}")
            return True
        return False

    def get_plugin(self, name: str) -> Plugin | None:
        """Get an initialized plugin instance."""
        if name not in self._plugins:
            return None

        if name not in self._instances:
            # Create and initialize instance
            plugin_class = self._plugins[name]
            instance = plugin_class()

            try:
                if instance.initialize():
                    instance._initialized = True
                    self._instances[name] = instance
                else:
                    logger.error(f"Plugin {name} initialization failed")
                    return None
            except Exception as e:
                logger.error(f"Plugin {name} initialization error: {e}")
                return None

        return self._instances[name]

    def list_plugins(self, plugin_type: PluginType | None = None) -> list[PluginInfo]:
        """List all registered plugins."""
        plugins = []
        for name, plugin_class in self._plugins.items():
            info = plugin_class.get_info()

            if plugin_type and info.plugin_type != plugin_type:
                continue

            # Update status
            if name in self._instances:
                info.status = PluginStatus.ACTIVE

            plugins.append(info)

        return plugins

    def load_from_directory(self, directory: Path) -> int:
        """Load plugins from a directory.

        Args:
            directory: Path to plugins directory.

        Returns:
            Number of plugins loaded.
        """
        loaded = 0

        if not directory.exists():
            logger.warning(f"Plugin directory not found: {directory}")
            return 0

        for file in directory.glob("*.py"):
            if file.name.startswith("_"):
                continue

            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find Plugin subclasses
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (
                            isinstance(obj, type)
                            and issubclass(obj, Plugin)
                            and obj is not Plugin
                            and not name.startswith("_")
                        ):
                            if self.register(obj):
                                loaded += 1

            except Exception as e:
                logger.error(f"Failed to load plugin from {file}: {e}")

        return loaded

    def add_hook(self, hook_name: str, callback: Callable) -> None:
        """Add a hook callback."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def run_hook(self, hook_name: str, *args, **kwargs) -> list[Any]:
        """Run all callbacks for a hook."""
        results = []
        for callback in self._hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {hook_name} callback error: {e}")
        return results


# Global registry
_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Get global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_plugin(plugin_class: type[Plugin]) -> type[Plugin]:
    """Decorator to register a plugin."""
    get_registry().register(plugin_class)
    return plugin_class

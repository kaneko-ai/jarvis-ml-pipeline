"""Plugin Architecture.

Per RP-425, implements plugin system for extensibility.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Type
from pathlib import Path
import importlib.util


@dataclass
class PluginInfo:
    """Plugin metadata."""
    
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    entry_point: str
    dependencies: List[str]


class PluginInterface(ABC):
    """Base interface for all plugins."""
    
    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Unique plugin identifier."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        pass
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    @abstractmethod
    def activate(self, context: Dict[str, Any]) -> None:
        """Activate the plugin."""
        pass
    
    @abstractmethod
    def deactivate(self) -> None:
        """Deactivate the plugin."""
        pass


class RetrievalPlugin(PluginInterface):
    """Plugin for custom retrieval strategies."""
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Custom retrieval logic."""
        pass


class GenerationPlugin(PluginInterface):
    """Plugin for custom generation strategies."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: Dict[str, Any],
    ) -> str:
        """Custom generation logic."""
        pass


class EvaluationPlugin(PluginInterface):
    """Plugin for custom evaluation metrics."""
    
    @abstractmethod
    def evaluate(
        self,
        output: str,
        reference: str,
        context: Dict[str, Any],
    ) -> Dict[str, float]:
        """Custom evaluation logic."""
        pass


class PluginManager:
    """Manages plugin lifecycle.
    
    Per RP-425:
    - Plugin API definition
    - Sample plugins
    - Marketplace support
    """
    
    def __init__(
        self,
        plugins_dir: str = "plugins",
    ):
        self.plugins_dir = Path(plugins_dir)
        self._plugins: Dict[str, PluginInterface] = {}
        self._active: Dict[str, bool] = {}
    
    def discover_plugins(self) -> List[PluginInfo]:
        """Discover available plugins.
        
        Returns:
            List of available plugins.
        """
        plugins = []
        
        if not self.plugins_dir.exists():
            return plugins
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_path = plugin_dir / "plugin.json"
                if manifest_path.exists():
                    import json
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                        plugins.append(PluginInfo(
                            plugin_id=manifest.get("id", plugin_dir.name),
                            name=manifest.get("name", plugin_dir.name),
                            version=manifest.get("version", "1.0.0"),
                            description=manifest.get("description", ""),
                            author=manifest.get("author", ""),
                            entry_point=manifest.get("entry_point", "__init__.py"),
                            dependencies=manifest.get("dependencies", []),
                        ))
        
        return plugins
    
    def load_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """Load a plugin by ID.
        
        Args:
            plugin_id: Plugin identifier.
            
        Returns:
            Loaded plugin or None.
        """
        plugin_dir = self.plugins_dir / plugin_id
        
        if not plugin_dir.exists():
            return None
        
        # Load plugin module
        init_path = plugin_dir / "__init__.py"
        if not init_path.exists():
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_id}",
                init_path,
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for Plugin class
                if hasattr(module, "Plugin"):
                    plugin = module.Plugin()
                    self._plugins[plugin_id] = plugin
                    return plugin
        except Exception:
            pass
        
        return None
    
    def activate_plugin(
        self,
        plugin_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Activate a plugin.
        
        Args:
            plugin_id: Plugin identifier.
            context: Activation context.
            
        Returns:
            True if activated.
        """
        plugin = self._plugins.get(plugin_id)
        
        if not plugin:
            plugin = self.load_plugin(plugin_id)
        
        if plugin:
            try:
                plugin.activate(context or {})
                self._active[plugin_id] = True
                return True
            except Exception:
                pass
        
        return False
    
    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate a plugin.
        
        Args:
            plugin_id: Plugin identifier.
            
        Returns:
            True if deactivated.
        """
        plugin = self._plugins.get(plugin_id)
        
        if plugin and self._active.get(plugin_id):
            try:
                plugin.deactivate()
                self._active[plugin_id] = False
                return True
            except Exception:
                pass
        
        return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """Get a loaded plugin.
        
        Args:
            plugin_id: Plugin identifier.
            
        Returns:
            Plugin instance or None.
        """
        return self._plugins.get(plugin_id)
    
    def list_active_plugins(self) -> List[str]:
        """List active plugins.
        
        Returns:
            List of active plugin IDs.
        """
        return [pid for pid, active in self._active.items() if active]
    
    def register_plugin(self, plugin: PluginInterface) -> None:
        """Register a plugin instance directly.
        
        Args:
            plugin: Plugin instance.
        """
        self._plugins[plugin.plugin_id] = plugin

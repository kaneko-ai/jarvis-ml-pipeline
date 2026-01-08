"""
JARVIS Plugin Framework - プラグイン基盤

全プラグインの共通インターフェースを定義。
activate/run/deactivate APIを標準化。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, RuntimeConfig, TaskContext
)


@dataclass
class PluginMetadata:
    """
    プラグインメタデータ（plugin.jsonの内容）.
    """
    name: str
    version: str
    type: str  # retrieval, rerank, extract, summarize, score, graph, design, ui
    entrypoint: str
    requires: List[str] = field(default_factory=list)
    hardware: Dict[str, Any] = field(default_factory=dict)
    config_schema: Optional[str] = None
    description: str = ""

    @classmethod
    def from_json(cls, path: Path) -> "PluginMetadata":
        """Load from plugin.json."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            name=data["name"],
            version=data["version"],
            type=data["type"],
            entrypoint=data["entrypoint"],
            requires=data.get("requires", []),
            hardware=data.get("hardware", {}),
            config_schema=data.get("config_schema"),
            description=data.get("description", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.type,
            "entrypoint": self.entrypoint,
            "requires": self.requires,
            "hardware": self.hardware,
            "config_schema": self.config_schema,
            "description": self.description
        }


class BasePlugin(ABC):
    """
    プラグイン基底クラス.
    
    全プラグインはこのクラスを継承し、
    activate/run/deactivate を実装する。
    """

    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.is_active = False
        self.runtime: Optional[RuntimeConfig] = None
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        """
        プラグインをアクティベート（モデルロード、ウォームアップ等）.
        
        Args:
            runtime: ランタイム設定
            config: プラグイン固有設定
        """
        pass

    @abstractmethod
    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """
        プラグインを実行し、成果物の差分を返す.
        
        Args:
            context: タスクコンテキスト
            artifacts: 入力成果物
        
        Returns:
            成果物の差分（追加・更新された部分）
        """
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """
        プラグインを非アクティベート（GPU解放、キャッシュフラッシュ等）.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """プラグイン情報を取得."""
        return {
            **self.metadata.to_dict(),
            "is_active": self.is_active
        }


class PluginRegistry:
    """
    プラグインレジストリ.
    
    登録されたプラグインを管理する。
    """

    def __init__(self):
        self._plugins: Dict[str, Type[BasePlugin]] = {}
        self._instances: Dict[str, BasePlugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}

    def register(self, name: str, plugin_class: Type[BasePlugin],
                 metadata: PluginMetadata) -> None:
        """プラグインを登録."""
        self._plugins[name] = plugin_class
        self._metadata[name] = metadata

    def get(self, name: str) -> Optional[BasePlugin]:
        """インスタンスを取得（なければ作成）."""
        if name not in self._instances:
            if name not in self._plugins:
                return None
            self._instances[name] = self._plugins[name](self._metadata[name])
        return self._instances[name]

    def list_plugins(self) -> List[str]:
        """登録済みプラグイン名リスト."""
        return list(self._plugins.keys())

    def list_by_type(self, plugin_type: str) -> List[str]:
        """タイプ別プラグインリスト."""
        return [name for name, meta in self._metadata.items()
                if meta.type == plugin_type]

    def activate_all(self, runtime: RuntimeConfig,
                     configs: Dict[str, Dict[str, Any]]) -> None:
        """全プラグインをアクティベート."""
        for name in self._plugins:
            plugin = self.get(name)
            if plugin:
                config = configs.get(name, {})
                plugin.activate(runtime, config)

    def deactivate_all(self) -> None:
        """全プラグインを非アクティベート."""
        for instance in self._instances.values():
            if instance.is_active:
                instance.deactivate()


class PluginLoader:
    """
    プラグインローダー.
    
    plugins/ ディレクトリからプラグインを動的に読み込む。
    """

    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.registry = PluginRegistry()

    def discover(self) -> List[PluginMetadata]:
        """利用可能なプラグインを検出."""
        plugins = []

        if not self.plugins_dir.exists():
            return plugins

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest = plugin_dir / "plugin.json"
            if manifest.exists():
                try:
                    metadata = PluginMetadata.from_json(manifest)
                    plugins.append(metadata)
                except Exception as e:
                    print(f"Failed to load plugin {plugin_dir.name}: {e}")

        return plugins

    def load(self, name: str) -> Optional[BasePlugin]:
        """プラグインを読み込み."""
        plugin_dir = self.plugins_dir / name
        manifest = plugin_dir / "plugin.json"

        if not manifest.exists():
            return None

        metadata = PluginMetadata.from_json(manifest)

        # Dynamic import
        module_path = plugin_dir / "plugin.py"
        if not module_path.exists():
            return None

        # For now, return None - actual dynamic import would be implemented
        # based on security and sandboxing requirements
        return None

    def load_all(self) -> int:
        """全プラグインを読み込み."""
        count = 0
        for meta in self.discover():
            if self.load(meta.name):
                count += 1
        return count


# グローバルレジストリ
_global_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """グローバルレジストリを取得."""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry


def register_plugin(name: str, plugin_class: Type[BasePlugin],
                    metadata: PluginMetadata) -> None:
    """プラグインをグローバルレジストリに登録."""
    get_plugin_registry().register(name, plugin_class, metadata)

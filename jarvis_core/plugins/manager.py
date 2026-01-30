"""
JARVIS Plugin Manager - 完全統一仕様

plugin.json の単一仕様を強制。
違反するプラグインは即拒否。
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from jarvis_core.contracts.types import Artifacts, RuntimeConfig, TaskContext


class PluginError(Exception):
    """プラグインエラー。"""

    pass


class PluginValidationError(PluginError):
    """プラグイン検証エラー（CI失敗）。"""

    pass


class PluginProtocol(Protocol):
    """
    プラグインプロトコル。

    全プラグインは activate/run/deactivate を実装必須。
    """

    def activate(self, runtime: RuntimeConfig, config: dict[str, Any]) -> None:
        """プラグインをアクティベート。"""
        ...

    def run(self, context: TaskContext, artifacts: Artifacts) -> dict[str, Any]:
        """プラグインを実行。"""
        ...

    def deactivate(self) -> None:
        """プラグインを非アクティベート。"""
        ...


# ========================================
# 正式 plugin.json 仕様（唯一）
# ========================================
REQUIRED_KEYS = ["id", "entrypoint"]
OPTIONAL_KEYS = ["version", "type", "dependencies", "hardware"]
VALID_TYPES = ["retrieval", "extract", "summarize", "score", "graph", "design", "ops", "ui"]


@dataclass
class PluginManifest:
    """
    plugin.json の正式仕様。

    必須キー: id, entrypoint
    オプション: version, type, dependencies, hardware
    それ以外のキーは禁止。
    """

    id: str
    entrypoint: str
    version: str = "0.1.0"
    type: str = "ops"
    dependencies: list[str] = field(default_factory=list)
    hardware: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, path: Path) -> PluginManifest:
        """
        plugin.json から読み込み。

        不正なキーがあればPluginValidationError。
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # 必須キーチェック
        for key in REQUIRED_KEYS:
            if key not in data:
                raise PluginValidationError(f"Missing required key '{key}' in {path}")

        # 不正キーチェック（厳格検証 - 余剰キーは即エラー）
        # 後方互換: name/description/requires/enabled も許可
        all_valid_keys = set(
            REQUIRED_KEYS + OPTIONAL_KEYS + ["name", "description", "requires", "enabled"]
        )
        for key in data.keys():
            if key not in all_valid_keys:
                raise PluginValidationError(
                    f"Unknown key '{key}' in {path}. " f"Allowed keys: {sorted(all_valid_keys)}"
                )

        # typeチェック
        if "type" in data and data["type"] not in VALID_TYPES:
            raise PluginValidationError(
                f"Invalid type '{data['type']}' in {path}. " f"Valid types: {VALID_TYPES}"
            )

        return cls(
            id=data.get("id", data.get("name", "")),  # id or name
            entrypoint=data["entrypoint"],
            version=data.get("version", "0.1.0"),
            type=data.get("type", "ops"),
            dependencies=data.get("dependencies", data.get("requires", [])),
            hardware=data.get("hardware", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "type": self.type,
            "entrypoint": self.entrypoint,
            "dependencies": self.dependencies,
            "hardware": self.hardware,
        }


class PluginManager:
    """
    Plugin Manager - プラグインの統一管理。

    ロード条件:
    1. plugin.json が存在
    2. id, entrypoint が存在
    3. entrypoint が import 可能
    4. Plugin クラスが activate/run/deactivate を実装
    """

    def __init__(self, plugins_dir: Path | None = None):
        self.plugins_dir = plugins_dir or Path("plugins")
        self.manifests: dict[str, PluginManifest] = {}
        self.instances: dict[str, Any] = {}
        self.errors: list[str] = []

    def discover(self) -> list[PluginManifest]:
        """
        利用可能なプラグインを検出。

        Returns:
            有効なマニフェストのリスト
        """
        manifests = []
        self.errors = []

        if not self.plugins_dir.exists():
            return manifests

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest_path = plugin_dir / "plugin.json"

            if not manifest_path.exists():
                self.errors.append(f"Plugin '{plugin_dir.name}' missing plugin.json")
                continue

            try:
                manifest = PluginManifest.from_json(manifest_path)
                manifests.append(manifest)
                self.manifests[manifest.id] = manifest
            except PluginValidationError as e:
                self.errors.append(str(e))
            except Exception as e:
                self.errors.append(f"Failed to load plugin '{plugin_dir.name}': {e}")

        return manifests

    def validate_all(self) -> bool:
        """
        全プラグインを検証。

        Returns:
            全て有効ならTrue

        Raises:
            PluginValidationError: 1つでも不正なら
        """
        self.discover()

        if self.errors:
            raise PluginValidationError(
                "Plugin validation failed:\n" + "\n".join(f"  - {e}" for e in self.errors)
            )

        return True

    def load(self, plugin_id: str) -> Any:
        """
        プラグインをロード。

        Args:
            plugin_id: プラグインID

        Returns:
            プラグインインスタンス
        """
        if plugin_id in self.instances:
            return self.instances[plugin_id]

        if plugin_id not in self.manifests:
            self.discover()

        if plugin_id not in self.manifests:
            raise PluginError(f"Plugin '{plugin_id}' not found")

        manifest = self.manifests[plugin_id]

        # entrypoint パース: "plugin.py:PluginClass"
        parts = manifest.entrypoint.split(":")
        if len(parts) != 2:
            raise PluginValidationError(
                f"Invalid entrypoint format: {manifest.entrypoint}. "
                f"Expected 'module.py:ClassName'"
            )

        module_file, class_name = parts
        module_name = f"plugins.{plugin_id}.{module_file.replace('.py', '')}"

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
        except ImportError as e:
            raise PluginError(f"Failed to import {module_name}: {e}")
        except AttributeError:
            raise PluginError(f"Class '{class_name}' not found in {module_name}")

        # プロトコルチェック
        required_methods = ["activate", "run", "deactivate"]
        for method in required_methods:
            if not hasattr(plugin_class, method):
                raise PluginValidationError(
                    f"Plugin '{plugin_id}' missing required method: {method}"
                )

        instance = plugin_class()
        self.instances[plugin_id] = instance

        return instance

    def load_all(self) -> dict[str, Any]:
        """全プラグインをロード。"""
        self.discover()

        for plugin_id in self.manifests:
            try:
                self.load(plugin_id)
            except Exception as e:
                self.errors.append(f"Failed to load '{plugin_id}': {e}")

        return self.instances

    def get_errors(self) -> list[str]:
        """エラー一覧を取得。"""
        return self.errors

    def list_active_plugins(self) -> list[str]:
        """アクティブなプラグイン一覧を取得。

        Returns:
            ロード済みプラグインのIDリスト
        """
        return list(self.instances.keys())


# グローバルマネージャ
_manager: PluginManager | None = None


def get_plugin_manager(plugins_dir: Path | None = None) -> PluginManager:
    """PluginManagerを取得。"""
    global _manager
    if _manager is None:
        _manager = PluginManager(plugins_dir)
    return _manager
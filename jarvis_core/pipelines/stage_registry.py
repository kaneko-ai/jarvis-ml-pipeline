"""
JARVIS Stage Registry - 全ステージ解決保証機構

すべてのstage名がregistryに登録され、実行可能であることを保証。
未登録ステージが存在した場合、CIは必ず失敗する。
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from jarvis_core.contracts.types import Artifacts, TaskContext


class StageNotImplementedError(Exception):
    """未登録ステージエラー。CIでは捕捉せず落とす。"""
    pass


class StageRegistry:
    """
    Stage Registry - ステージ名→実行可能オブジェクトを一元管理。
    
    - 手動登録禁止（import時に自動登録）
    - 未登録ステージを検出したら即例外
    """

    _instance: StageRegistry | None = None

    def __new__(cls) -> StageRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers: dict[str, Callable] = {}
            cls._instance._metadata: dict[str, dict[str, Any]] = {}
        return cls._instance

    def register(self, name: str, handler: Callable,
                 description: str = "",
                 requires_provenance: bool = True) -> None:
        """
        ステージを登録。
        
        Args:
            name: ステージ名（例: "retrieval.query_expand"）
            handler: 実行可能オブジェクト
            description: 説明
            requires_provenance: provenance更新が必須か
        """
        if name in self._handlers:
            raise ValueError(f"Stage '{name}' is already registered")

        self._handlers[name] = handler
        self._metadata[name] = {
            "description": description,
            "requires_provenance": requires_provenance
        }

    def get(self, name: str) -> Callable:
        """
        ステージハンドラを取得。
        
        Args:
            name: ステージ名
        
        Returns:
            実行可能オブジェクト
        
        Raises:
            StageNotImplementedError: 未登録の場合
        """
        if name not in self._handlers:
            raise StageNotImplementedError(
                f"Stage '{name}' is not registered. "
                f"Registered stages: {list(self._handlers.keys())}"
            )
        return self._handlers[name]

    def validate_pipeline(self, stage_names: list[str]) -> None:
        """
        パイプラインの全ステージが登録済みか検証。
        
        Args:
            stage_names: ステージ名リスト
        
        Raises:
            StageNotImplementedError: 未登録ステージが1つでもあれば
        """
        missing = []
        for name in stage_names:
            if name not in self._handlers:
                missing.append(name)

        if missing:
            raise StageNotImplementedError(
                f"The following stages are not registered: {missing}. "
                f"Pipeline cannot execute. This is a CI failure."
            )

    def list_stages(self) -> list[str]:
        """登録済みステージ一覧。"""
        return list(self._handlers.keys())

    def is_registered(self, name: str) -> bool:
        """ステージが登録済みか。"""
        return name in self._handlers

    def get_metadata(self, name: str) -> dict[str, Any]:
        """ステージのメタデータを取得。"""
        return self._metadata.get(name, {})

    def clear(self) -> None:
        """テスト用：レジストリをクリア。"""
        self._handlers.clear()
        self._metadata.clear()


# グローバルレジストリ
_registry = StageRegistry()


def get_stage_registry() -> StageRegistry:
    """グローバルレジストリを取得。"""
    return _registry


def register_stage(name: str, description: str = "",
                   requires_provenance: bool = True) -> Callable:
    """
    ステージ登録デコレータ。
    
    使用例:
        @register_stage("retrieval.query_expand")
        def stage_query_expand(context, artifacts):
            ...
    
    Args:
        name: ステージ名
        description: 説明
        requires_provenance: provenance更新必須フラグ
    
    Returns:
        デコレータ
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(context: TaskContext, artifacts: Artifacts) -> Artifacts:
            return func(context, artifacts)

        _registry.register(name, wrapper, description, requires_provenance)
        return wrapper

    return decorator


def validate_all_stages(stage_names: list[str]) -> None:
    """
    全ステージの登録を検証（CI用）。
    
    Raises:
        StageNotImplementedError: 未登録ステージがあれば
    """
    _registry.validate_pipeline(stage_names)

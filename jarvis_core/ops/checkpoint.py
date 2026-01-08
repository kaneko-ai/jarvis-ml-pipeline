"""
JARVIS Operations - Checkpoint & Resume

M4: 運用完備のためのチェックポイント・再開機構
- ステージごとのチェックポイント保存
- 中断からの再開
- 監査ログへの追記
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StageStatus(Enum):
    """ステージ状態."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    DEGRADED = "degraded"


@dataclass
class StageCheckpoint:
    """ステージチェックポイント."""

    stage_id: str
    status: StageStatus
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    artifacts_hash: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunCheckpoint:
    """ラン全体のチェックポイント."""

    run_id: str
    pipeline: str
    status: str = "running"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    current_stage_idx: int = 0
    stages: dict[str, StageCheckpoint] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "run_id": self.run_id,
            "pipeline": self.pipeline,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_stage_idx": self.current_stage_idx,
            "stages": {
                k: {
                    "stage_id": v.stage_id,
                    "status": v.status.value,
                    "started_at": v.started_at,
                    "completed_at": v.completed_at,
                    "duration_ms": v.duration_ms,
                    "error": v.error,
                    "metadata": v.metadata,
                }
                for k, v in self.stages.items()
            },
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunCheckpoint:
        """辞書から生成."""
        checkpoint = cls(
            run_id=data["run_id"],
            pipeline=data["pipeline"],
            status=data.get("status", "running"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            current_stage_idx=data.get("current_stage_idx", 0),
            context=data.get("context", {}),
        )

        for stage_id, stage_data in data.get("stages", {}).items():
            checkpoint.stages[stage_id] = StageCheckpoint(
                stage_id=stage_data["stage_id"],
                status=StageStatus(stage_data["status"]),
                started_at=stage_data.get("started_at"),
                completed_at=stage_data.get("completed_at"),
                duration_ms=stage_data.get("duration_ms"),
                error=stage_data.get("error"),
                metadata=stage_data.get("metadata", {}),
            )

        return checkpoint


class CheckpointManager:
    """チェックポイントマネージャー."""

    def __init__(self, base_path: str = "artifacts"):
        """
        初期化.

        Args:
            base_path: チェックポイント保存先ベースパス
        """
        self.base_path = Path(base_path)

    def _get_checkpoint_path(self, run_id: str) -> Path:
        """チェックポイントパスを取得."""
        return self.base_path / run_id / "checkpoint.json"

    def save(self, checkpoint: RunCheckpoint) -> Path:
        """
        チェックポイントを保存.

        Args:
            checkpoint: 保存するチェックポイント

        Returns:
            保存先パス
        """
        path = self._get_checkpoint_path(checkpoint.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint.updated_at = datetime.now().isoformat()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"Checkpoint saved: {path}")
        return path

    def load(self, run_id: str) -> RunCheckpoint | None:
        """
        チェックポイントを読み込み.

        Args:
            run_id: 実行ID

        Returns:
            チェックポイント（存在しない場合None）
        """
        path = self._get_checkpoint_path(run_id)

        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return RunCheckpoint.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def exists(self, run_id: str) -> bool:
        """チェックポイントが存在するか."""
        return self._get_checkpoint_path(run_id).exists()

    def get_completed_stages(self, run_id: str) -> set[str]:
        """完了済みステージを取得."""
        checkpoint = self.load(run_id)
        if not checkpoint:
            return set()

        return {
            stage_id
            for stage_id, stage in checkpoint.stages.items()
            if stage.status == StageStatus.COMPLETED
        }

    def get_resume_point(self, run_id: str) -> int | None:
        """
        再開ポイントを取得.

        Args:
            run_id: 実行ID

        Returns:
            再開するステージのインデックス（存在しない場合None）
        """
        checkpoint = self.load(run_id)
        if not checkpoint:
            return None

        if checkpoint.status == "completed":
            return None  # 完了済み

        return checkpoint.current_stage_idx

    def update_stage(
        self,
        run_id: str,
        stage_id: str,
        status: StageStatus,
        started_at: str | None = None,
        completed_at: str | None = None,
        duration_ms: int | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        ステージ状態を更新.

        Args:
            run_id: 実行ID
            stage_id: ステージID
            status: 新しい状態
            started_at: 開始時刻
            completed_at: 完了時刻
            duration_ms: 実行時間（ミリ秒）
            error: エラーメッセージ
            metadata: 追加メタデータ
        """
        checkpoint = self.load(run_id)
        if not checkpoint:
            logger.warning(f"Checkpoint not found for run_id: {run_id}")
            return

        checkpoint.stages[stage_id] = StageCheckpoint(
            stage_id=stage_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            error=error,
            metadata=metadata or {},
        )

        self.save(checkpoint)

    def mark_run_completed(self, run_id: str, status: str = "completed"):
        """ランを完了としてマーク."""
        checkpoint = self.load(run_id)
        if checkpoint:
            checkpoint.status = status
            self.save(checkpoint)


# グローバルマネージャー
_manager: CheckpointManager | None = None


def get_checkpoint_manager(base_path: str = "artifacts") -> CheckpointManager:
    """チェックポイントマネージャーを取得."""
    global _manager
    if _manager is None:
        _manager = CheckpointManager(base_path)
    return _manager

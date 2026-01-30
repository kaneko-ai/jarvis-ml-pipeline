"""
JARVIS Outcome Tracker

Phase 3: 結果追跡
- 採用後n週で効果判定
- success / neutral / failure
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .decision_item import DecisionStore

logger = logging.getLogger(__name__)


class OutcomeStatus(Enum):
    """Outcome状態."""

    SUCCESS = "success"  # 効果あり
    NEUTRAL = "neutral"  # 影響なし
    FAILURE = "failure"  # 悪影響/無駄
    PENDING = "pending"  # 未評価


@dataclass
class OutcomeRecord:
    """Outcome記録."""

    decision_id: str
    status: OutcomeStatus
    effect_description: str  # 効果はあったか
    cost_justified: bool  # コストに見合ったか
    would_repeat: bool  # 次もやるか
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "decision_id": self.decision_id,
            "status": self.status.value,
            "effect_description": self.effect_description,
            "cost_justified": self.cost_justified,
            "would_repeat": self.would_repeat,
            "evaluated_at": self.evaluated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutcomeRecord:
        """辞書から生成."""
        return cls(
            decision_id=data["decision_id"],
            status=OutcomeStatus(data["status"]),
            effect_description=data["effect_description"],
            cost_justified=data["cost_justified"],
            would_repeat=data["would_repeat"],
            evaluated_at=data.get("evaluated_at", ""),
            metadata=data.get("metadata", {}),
        )


class OutcomeTracker:
    """Outcome追跡器.

    採用後n週間で評価。
    失敗判断はExperienceに強制保存。
    """

    def __init__(
        self,
        storage_path: str = "data/outcomes",
        decision_store: DecisionStore | None = None,
        evaluation_weeks: int = 2,
    ):
        """
        初期化.

        Args:
            storage_path: ストレージパス
            decision_store: DecisionStore
            evaluation_weeks: 評価までの週数
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.decision_store = decision_store or DecisionStore()
        self.evaluation_weeks = evaluation_weeks
        self._outcomes: list[OutcomeRecord] = []
        self._load()

    def _load(self) -> None:
        """ストレージから読み込み."""
        outcomes_file = self.storage_path / "outcomes.jsonl"
        if not outcomes_file.exists():
            return

        with open(outcomes_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self._outcomes.append(OutcomeRecord.from_dict(json.loads(line)))

        logger.info(f"Loaded {len(self._outcomes)} outcomes")

    def _save(self) -> None:
        """ストレージに保存."""
        outcomes_file = self.storage_path / "outcomes.jsonl"
        with open(outcomes_file, "w", encoding="utf-8") as f:
            for o in self._outcomes:
                f.write(json.dumps(o.to_dict(), ensure_ascii=False) + "\n")

    def record(self, record: OutcomeRecord) -> None:
        """Outcomeを記録."""
        self._outcomes.append(record)

        # DecisionStoreも更新
        self.decision_store.update_outcome(
            decision_id=record.decision_id,
            outcome=record.effect_description,
            outcome_status=record.status.value,
        )

        self._save()
        logger.info(f"Recorded outcome for {record.decision_id}: {record.status.value}")

    def get_pending_evaluations(self) -> list[str]:
        """評価待ちのDecision IDリストを取得."""
        cutoff = datetime.now() - timedelta(weeks=self.evaluation_weeks)

        pending = []
        evaluated_ids = {o.decision_id for o in self._outcomes}

        for d in self.decision_store.list_all():
            if d.decision == "accept" and d.decision_id not in evaluated_ids:
                # 採用からn週経過しているか
                try:
                    decision_time = datetime.fromisoformat(d.timestamp.replace("Z", "+00:00"))
                    if decision_time < cutoff:
                        pending.append(d.decision_id)
                except Exception:
                    pass

        return pending

    def summarize(self) -> dict[str, Any]:
        """Outcomeサマリーを生成."""
        if not self._outcomes:
            return {
                "total": 0,
                "success": 0,
                "neutral": 0,
                "failure": 0,
                "success_rate": 0.0,
            }

        status_counts = {
            OutcomeStatus.SUCCESS: 0,
            OutcomeStatus.NEUTRAL: 0,
            OutcomeStatus.FAILURE: 0,
        }

        for o in self._outcomes:
            if o.status in status_counts:
                status_counts[o.status] += 1

        total = len(self._outcomes)
        success_rate = status_counts[OutcomeStatus.SUCCESS] / total if total > 0 else 0.0

        return {
            "total": total,
            "success": status_counts[OutcomeStatus.SUCCESS],
            "neutral": status_counts[OutcomeStatus.NEUTRAL],
            "failure": status_counts[OutcomeStatus.FAILURE],
            "success_rate": success_rate,
        }

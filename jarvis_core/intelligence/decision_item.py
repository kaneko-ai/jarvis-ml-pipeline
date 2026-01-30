"""
JARVIS Decision Item

Phase 2: DecisionItem（再利用可能な判断単位）
- Issue ≠ Decision
- Decision は再利用可能な知識単位
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


class DecisionPattern(Enum):
    """判断パターン（型）.

    Decisionをクラスタリングして抽出。
    """

    EARLY_STAGE_REJECT = "early-stage-reject"  # 流行初期・根拠不足
    HIGH_EFFORT_DELAY = "high-effort-delay"  # コスト高→後回し
    EVALUATOR_FIRST = "evaluator-first"  # まず評価系を強化
    CORE_PRIORITY = "core-priority"  # 中核機能優先
    EVIDENCE_REQUIRED = "evidence-required"  # 根拠必須
    UNCLASSIFIED = "unclassified"


@dataclass
class DecisionItem:
    """判断単位（再利用可能な知識）.

    Issue はイベント、Decision は知識。
    """

    decision_id: str
    context: str  # 状況説明
    decision: str  # accept | reject
    pattern: DecisionPattern
    reason: str  # 判断理由
    outcome: str | None = None  # 結果（後日評価）
    outcome_status: str | None = None  # success | neutral | failure
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "decision_id": self.decision_id,
            "context": self.context,
            "decision": self.decision,
            "pattern": self.pattern.value,
            "reason": self.reason,
            "outcome": self.outcome,
            "outcome_status": self.outcome_status,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionItem:
        """辞書から生成."""
        return cls(
            decision_id=data["decision_id"],
            context=data["context"],
            decision=data["decision"],
            pattern=DecisionPattern(data.get("pattern", "unclassified")),
            reason=data["reason"],
            outcome=data.get("outcome"),
            outcome_status=data.get("outcome_status"),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}),
        )


class DecisionStore:
    """判断ストア.

    過去のDecisionを保存・検索。
    """

    def __init__(self, storage_path: str = "data/decisions"):
        """
        初期化.

        Args:
            storage_path: ストレージディレクトリ
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._decisions: list[DecisionItem] = []
        self._load()

    def _load(self) -> None:
        """ストレージから読み込み."""
        decisions_file = self.storage_path / "decisions.jsonl"
        if not decisions_file.exists():
            return

        with open(decisions_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self._decisions.append(DecisionItem.from_dict(json.loads(line)))

        logger.info(f"Loaded {len(self._decisions)} decisions")

    def _save(self) -> None:
        """ストレージに保存."""
        decisions_file = self.storage_path / "decisions.jsonl"
        with open(decisions_file, "w", encoding="utf-8") as f:
            for d in self._decisions:
                f.write(json.dumps(d.to_dict(), ensure_ascii=False) + "\n")

    def add(self, decision: DecisionItem) -> None:
        """判断を追加."""
        self._decisions.append(decision)
        self._save()
        logger.info(f"Added decision: {decision.decision_id}")

    def get(self, decision_id: str) -> DecisionItem | None:
        """IDで取得."""
        for d in self._decisions:
            if d.decision_id == decision_id:
                return d
        return None

    def list_all(self) -> list[DecisionItem]:
        """全件取得."""
        return self._decisions.copy()

    def filter_by_pattern(self, pattern: DecisionPattern) -> list[DecisionItem]:
        """パターンでフィルタ."""
        return [d for d in self._decisions if d.pattern == pattern]

    def filter_by_decision(self, decision: str) -> list[DecisionItem]:
        """accept/rejectでフィルタ."""
        return [d for d in self._decisions if d.decision == decision]

    def update_outcome(self, decision_id: str, outcome: str, outcome_status: str) -> bool:
        """Outcomeを更新."""
        for d in self._decisions:
            if d.decision_id == decision_id:
                d.outcome = outcome
                d.outcome_status = outcome_status
                self._save()
                logger.info(f"Updated outcome for {decision_id}: {outcome_status}")
                return True
        return False
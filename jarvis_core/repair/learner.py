"""ITER-06: Self-Repair学習 (Self-Repair Learning).

過去の修復成功パターンを学習。
- 成功パターン記録
- 最適な修復戦略選択
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RepairRecord:
    """修復記録."""
    fail_reason: str
    repair_action: str
    success: bool
    attempts: int
    timestamp: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "fail_reason": self.fail_reason,
            "repair_action": self.repair_action,
            "success": self.success,
            "attempts": self.attempts,
            "timestamp": self.timestamp,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RepairRecord:
        return cls(
            fail_reason=d.get("fail_reason", ""),
            repair_action=d.get("repair_action", ""),
            success=d.get("success", False),
            attempts=d.get("attempts", 1),
            timestamp=d.get("timestamp", ""),
            context=d.get("context", {}),
        )


@dataclass
class RepairStrategy:
    """修復戦略."""
    action: str
    success_rate: float
    avg_attempts: float
    total_uses: int
    recommended: bool = False

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "success_rate": self.success_rate,
            "avg_attempts": self.avg_attempts,
            "total_uses": self.total_uses,
            "recommended": self.recommended,
        }


class SelfRepairLearner:
    """Self-Repair学習器.
    
    過去の修復結果から最適な戦略を学習。
    """

    def __init__(self, history_path: Path | None = None):
        self.history_path = history_path or Path("logs/repair_history.jsonl")
        self._records: list[RepairRecord] = []
        self._load_history()

    def _load_history(self) -> None:
        """履歴を読み込み."""
        if not self.history_path.exists():
            return

        try:
            with open(self.history_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self._records.append(RepairRecord.from_dict(json.loads(line)))
        except Exception:
            pass

    def record(
        self,
        fail_reason: str,
        repair_action: str,
        success: bool,
        attempts: int = 1,
        context: dict[str, Any] | None = None,
    ) -> None:
        """修復結果を記録."""
        record = RepairRecord(
            fail_reason=fail_reason,
            repair_action=repair_action,
            success=success,
            attempts=attempts,
            timestamp=datetime.now(timezone.utc).isoformat(),
            context=context or {},
        )

        self._records.append(record)

        # 永続化
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def get_best_strategy(self, fail_reason: str) -> RepairStrategy | None:
        """最適な修復戦略を取得."""
        strategies = self.analyze_strategies(fail_reason)

        if not strategies:
            return None

        # 成功率が最高の戦略
        best = max(strategies, key=lambda s: s.success_rate)
        best.recommended = True

        return best

    def analyze_strategies(self, fail_reason: str) -> list[RepairStrategy]:
        """fail_reasonに対する戦略を分析."""
        # 該当する記録を抽出
        relevant = [r for r in self._records if r.fail_reason == fail_reason]

        if not relevant:
            return []

        # アクション別に集計
        action_stats: dict[str, dict[str, Any]] = {}

        for record in relevant:
            action = record.repair_action
            if action not in action_stats:
                action_stats[action] = {
                    "successes": 0,
                    "failures": 0,
                    "total_attempts": 0,
                }

            if record.success:
                action_stats[action]["successes"] += 1
            else:
                action_stats[action]["failures"] += 1

            action_stats[action]["total_attempts"] += record.attempts

        # 戦略リストに変換
        strategies = []
        for action, stats in action_stats.items():
            total = stats["successes"] + stats["failures"]
            strategies.append(RepairStrategy(
                action=action,
                success_rate=stats["successes"] / total if total > 0 else 0,
                avg_attempts=stats["total_attempts"] / total if total > 0 else 0,
                total_uses=total,
            ))

        # 成功率順でソート
        strategies.sort(key=lambda s: s.success_rate, reverse=True)

        return strategies

    def get_statistics(self) -> dict[str, Any]:
        """全体統計を取得."""
        total = len(self._records)
        successes = sum(1 for r in self._records if r.success)

        by_reason: dict[str, dict[str, int]] = {}
        for record in self._records:
            if record.fail_reason not in by_reason:
                by_reason[record.fail_reason] = {"success": 0, "failure": 0}

            if record.success:
                by_reason[record.fail_reason]["success"] += 1
            else:
                by_reason[record.fail_reason]["failure"] += 1

        return {
            "total_records": total,
            "success_rate": successes / total if total > 0 else 0,
            "by_reason": by_reason,
        }

    def recommend_actions(
        self,
        fail_reasons: list[str],
    ) -> list[dict[str, Any]]:
        """複数のfail_reasonに対する推奨アクションを取得."""
        recommendations = []

        for reason in fail_reasons:
            best = self.get_best_strategy(reason)
            if best:
                recommendations.append({
                    "fail_reason": reason,
                    "recommended_action": best.action,
                    "expected_success_rate": best.success_rate,
                })
            else:
                recommendations.append({
                    "fail_reason": reason,
                    "recommended_action": None,
                    "expected_success_rate": 0,
                })

        return recommendations


def get_learner() -> SelfRepairLearner:
    """グローバル学習器を取得."""
    return SelfRepairLearner()

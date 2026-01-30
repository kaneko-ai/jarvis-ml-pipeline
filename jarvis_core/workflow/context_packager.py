"""
JARVIS Context Packager

PDF知見統合（LayerX）: コンテキスト爆発対策
- 全ログをLLMに渡すのを禁止
- 下位K%のログだけ要約して渡す
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """ログエントリ."""

    run_id: str
    step_id: str
    score: float
    output_summary: str
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ScoreDiff:
    """スコア差分."""

    metric: str
    prev_best: float
    current: float
    diff: float
    is_regression: bool


class ContextPackager:
    """コンテキストパッケージャー.

    LayerXの3課題対策:
    1. コンテキスト爆発 → 下位K%のログだけ渡す
    2. モグラ叩き → 差分表を生成
    3. 回帰 → 回帰検知
    """

    def __init__(
        self, bottom_k_percent: float = 50.0, max_entries: int = 10, summary_max_chars: int = 500
    ):
        """
        初期化.

        Args:
            bottom_k_percent: 下位何%のログを取得するか
            max_entries: 最大エントリ数
            summary_max_chars: 要約の最大文字数
        """
        self.bottom_k_percent = bottom_k_percent
        self.max_entries = max_entries
        self.summary_max_chars = summary_max_chars
        self._logs: list[LogEntry] = []
        self._best_score: float | None = None
        self._best_run_id: str | None = None

    def add_log(self, entry: LogEntry):
        """ログを追加."""
        self._logs.append(entry)

        # ベストスコア更新
        if self._best_score is None or entry.score > self._best_score:
            self._best_score = entry.score
            self._best_run_id = entry.run_id

    def get_bottom_k_logs(self) -> list[LogEntry]:
        """
        下位K%のログを取得.

        コンテキスト爆発対策: 全ログではなく下位のみ。
        """
        if not self._logs:
            return []

        sorted_logs = sorted(self._logs, key=lambda x: x.score)
        k = max(1, int(len(sorted_logs) * self.bottom_k_percent / 100))
        return sorted_logs[: min(k, self.max_entries)]

    def generate_score_diff(
        self, current_scores: dict[str, float], prev_best_scores: dict[str, float] | None = None
    ) -> list[ScoreDiff]:
        """
        スコア差分表を生成.

        モグラ叩き対策: 前回ベストとの差分を明示。
        """
        if prev_best_scores is None:
            return []

        diffs = []
        for metric, current in current_scores.items():
            prev = prev_best_scores.get(metric, 0.0)
            diff = current - prev
            is_regression = diff < 0

            diffs.append(
                ScoreDiff(
                    metric=metric,
                    prev_best=prev,
                    current=current,
                    diff=diff,
                    is_regression=is_regression,
                )
            )

        return diffs

    def detect_regression(self, current_score: float, threshold: float = 0.0) -> bool:
        """
        回帰を検知.

        Args:
            current_score: 現在のスコア
            threshold: 許容する劣化幅

        Returns:
            回帰しているか
        """
        if self._best_score is None:
            return False

        return current_score < (self._best_score - threshold)

    def package_for_generator(
        self, current_scores: dict[str, float], prev_best_scores: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """
        Generatorに渡すコンテキストをパッケージング.

        全ログではなく、下位ログ＋差分表のみ。
        """
        bottom_logs = self.get_bottom_k_logs()
        score_diffs = self.generate_score_diff(current_scores, prev_best_scores)

        # 回帰したケースをハイライト
        regression_cases = [d for d in score_diffs if d.is_regression]

        return {
            "bottom_logs": [
                {
                    "run_id": log.run_id,
                    "step_id": log.step_id,
                    "score": log.score,
                    "summary": log.output_summary[: self.summary_max_chars],
                    "error": log.error,
                }
                for log in bottom_logs
            ],
            "score_diffs": [
                {
                    "metric": d.metric,
                    "prev_best": d.prev_best,
                    "current": d.current,
                    "diff": d.diff,
                    "is_regression": d.is_regression,
                }
                for d in score_diffs
            ],
            "regression_cases": [
                {
                    "metric": d.metric,
                    "degradation": abs(d.diff),
                }
                for d in regression_cases
            ],
            "best_score": self._best_score,
            "best_run_id": self._best_run_id,
        }

    def clear(self):
        """ログをクリア."""
        self._logs = []
        self._best_score = None
        self._best_run_id = None
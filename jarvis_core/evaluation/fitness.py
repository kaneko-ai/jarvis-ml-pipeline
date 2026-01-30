"""
JARVIS Fitness Evaluation

PDF知見統合（Findy）: 適応度関数
- "動いたらOK"を明示的に禁止
- Fitnessの最低条件を満たさないWorkflowは採用不可
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FitnessScore:
    """フィットネススコア."""

    correctness: float = 0.0  # 引用精度、スキーマ準拠
    regression: float = 0.0  # 回帰率（0=なし、1=全て回帰）
    reproducibility: float = 0.0  # 再現性
    cost: float = 0.0  # 推論コスト（正規化）
    latency: float = 0.0  # 時間（秒）
    security: float = 1.0  # セキュリティ（1=安全、0=危険）

    def total(self, weights: dict[str, float] | None = None) -> float:
        """重み付き総合スコア."""
        if weights is None:
            weights = {
                "correctness": 0.4,
                "regression": 0.2,
                "reproducibility": 0.2,
                "cost": 0.1,
                "latency": 0.1,
            }

        score = 0.0
        score += weights.get("correctness", 0.4) * self.correctness
        score += weights.get("regression", 0.2) * (1.0 - self.regression)
        score += weights.get("reproducibility", 0.2) * self.reproducibility
        score += weights.get("cost", 0.1) * (1.0 - min(1.0, self.cost / 10.0))
        score += weights.get("latency", 0.1) * (1.0 - min(1.0, self.latency / 100.0))

        return score

    def to_dict(self) -> dict[str, float]:
        """辞書に変換."""
        return {
            "correctness": self.correctness,
            "regression": self.regression,
            "reproducibility": self.reproducibility,
            "cost": self.cost,
            "latency": self.latency,
            "security": self.security,
        }


@dataclass
class FitnessGate:
    """フィットネスゲート.

    最低条件を満たさないWorkflowは採用不可。
    """

    min_correctness: float = 0.7
    max_regression: float = 0.1
    min_reproducibility: float = 0.8
    require_security: bool = True

    def check(self, score: FitnessScore) -> tuple[bool, list[str]]:
        """
        ゲートチェック.

        Returns:
            (合格したか, 失敗理由リスト)
        """
        failures = []

        if score.correctness < self.min_correctness:
            failures.append(f"correctness {score.correctness:.2f} < {self.min_correctness}")

        if score.regression > self.max_regression:
            failures.append(f"regression {score.regression:.2f} > {self.max_regression}")

        if score.reproducibility < self.min_reproducibility:
            failures.append(
                f"reproducibility {score.reproducibility:.2f} < {self.min_reproducibility}"
            )

        if self.require_security and score.security < 1.0:
            failures.append(f"security issue detected: {score.security:.2f}")

        passed = len(failures) == 0
        return passed, failures


class FitnessEvaluator:
    """フィットネス評価器."""

    def __init__(self, gate: FitnessGate | None = None):
        """
        初期化.

        Args:
            gate: フィットネスゲート
        """
        self.gate = gate or FitnessGate()
        self._prev_scores: FitnessScore | None = None

    def evaluate(
        self,
        correctness: float,
        reproducibility: float,
        cost: float,
        latency: float,
        security: float = 1.0,
        prev_scores: FitnessScore | None = None,
    ) -> tuple[FitnessScore, bool, list[str]]:
        """
        フィットネスを評価.

        Args:
            correctness: 正確性スコア
            reproducibility: 再現性スコア
            cost: コスト
            latency: レイテンシ
            security: セキュリティスコア
            prev_scores: 前回のスコア（回帰検知用）

        Returns:
            (FitnessScore, ゲート合格, 失敗理由)
        """
        # 回帰率を計算
        regression = 0.0
        if prev_scores or self._prev_scores:
            prev = prev_scores or self._prev_scores
            if correctness < prev.correctness:
                regression += 0.5
            if reproducibility < prev.reproducibility:
                regression += 0.5

        score = FitnessScore(
            correctness=correctness,
            regression=regression,
            reproducibility=reproducibility,
            cost=cost,
            latency=latency,
            security=security,
        )

        passed, failures = self.gate.check(score)

        # 保存
        if passed:
            self._prev_scores = score

        return score, passed, failures

    def evaluate_from_run(
        self,
        claims_count: int,
        claims_with_evidence: int,
        reproduced_count: int,
        total_runs: int,
        cost: float,
        latency: float,
    ) -> tuple[FitnessScore, bool, list[str]]:
        """
        実行結果からフィットネスを評価.

        Args:
            claims_count: Claim総数
            claims_with_evidence: 根拠付きClaim数
            reproduced_count: 再現成功数
            total_runs: 総実行回数
            cost: 総コスト
            latency: 総レイテンシ

        Returns:
            (FitnessScore, ゲート合格, 失敗理由)
        """
        correctness = claims_with_evidence / claims_count if claims_count > 0 else 0.0
        reproducibility = reproduced_count / total_runs if total_runs > 0 else 0.0

        return self.evaluate(
            correctness=correctness,
            reproducibility=reproducibility,
            cost=cost,
            latency=latency,
        )
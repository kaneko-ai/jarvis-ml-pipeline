"""
JARVIS Repeated Sampling

PDF知見統合（LayerX）: Repeated Sampling
- N本生成→評価→ベスト採用
- コスト上限でn_samples自動調整
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class SampleResult:
    """サンプル結果."""
    sample_id: str
    output: Any
    score: float
    cost: float
    is_valid: bool = True
    error: str | None = None


class RepeatedSampler:
    """Repeated Sampler.
    
    N本生成→評価→ベスト採用。
    採用済み「8」（推論コスト制御）と連携。
    """

    def __init__(
        self,
        n_samples: int = 3,
        max_cost: float = 10.0,
        min_samples: int = 1
    ):
        """
        初期化.
        
        Args:
            n_samples: サンプル数
            max_cost: 最大コスト
            min_samples: 最小サンプル数
        """
        self.n_samples = n_samples
        self.max_cost = max_cost
        self.min_samples = min_samples
        self._total_cost = 0.0

    def sample(
        self,
        generator: Callable[[], T],
        evaluator: Callable[[T], float],
        cost_estimator: Callable[[T], float] | None = None
    ) -> SampleResult | None:
        """
        Repeated Samplingを実行.
        
        Args:
            generator: 候補を生成する関数
            evaluator: スコアを評価する関数
            cost_estimator: コストを推定する関数
        
        Returns:
            ベストサンプル
        """
        results: list[SampleResult] = []

        # コスト制限に応じてサンプル数を調整
        effective_samples = self._adjust_samples()

        for i in range(effective_samples):
            sample_id = f"sample_{i}"

            try:
                output = generator()
                score = evaluator(output)
                cost = cost_estimator(output) if cost_estimator else 0.0

                self._total_cost += cost

                result = SampleResult(
                    sample_id=sample_id,
                    output=output,
                    score=score,
                    cost=cost,
                )
                results.append(result)

                logger.debug(f"Sample {sample_id}: score={score:.3f}, cost={cost:.3f}")

                # コスト上限チェック
                if self._total_cost >= self.max_cost:
                    logger.warning(f"Cost limit reached: {self._total_cost:.2f} >= {self.max_cost}")
                    break

            except Exception as e:
                logger.warning(f"Sample {sample_id} failed: {e}")
                results.append(SampleResult(
                    sample_id=sample_id,
                    output=None,
                    score=0.0,
                    cost=0.0,
                    is_valid=False,
                    error=str(e),
                ))

        # ベスト選択
        valid_results = [r for r in results if r.is_valid]
        if not valid_results:
            return None

        best = max(valid_results, key=lambda x: x.score)
        logger.info(f"Best sample: {best.sample_id} with score {best.score:.3f}")

        return best

    def _adjust_samples(self) -> int:
        """コスト制限に応じてサンプル数を調整."""
        remaining_budget = self.max_cost - self._total_cost

        if remaining_budget <= 0:
            return self.min_samples

        # 残り予算に応じて調整
        budget_ratio = remaining_budget / self.max_cost
        adjusted = max(
            self.min_samples,
            int(self.n_samples * budget_ratio)
        )

        return min(adjusted, self.n_samples)

    def reset_cost(self):
        """コストをリセット."""
        self._total_cost = 0.0

    @property
    def total_cost(self) -> float:
        """累計コストを取得."""
        return self._total_cost

"""
JARVIS Workflow Tuner

PDF知見統合（LayerX）: 自動改善ループ
Generator → Executor → Evaluator → Memory → Sampling
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .context_packager import ContextPackager, LogEntry
from .repeated_sampling import RepeatedSampler, SampleResult
from .runner import WorkflowRunner, WorkflowState
from .spec import WorkflowSpec

logger = logging.getLogger(__name__)


@dataclass
class TuneIteration:
    """チューニング反復."""

    iteration: int
    samples: list[SampleResult]
    best_sample: SampleResult | None
    fitness_score: float
    is_improvement: bool
    context_used: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TuneResult:
    """チューニング結果."""

    workflow_id: str
    iterations: list[TuneIteration]
    final_fitness: float
    best_config: dict[str, Any]
    total_cost: float
    converged: bool
    reason: str  # converged | max_iters | budget_exceeded | threshold_reached


class WorkflowTuner:
    """ワークフローチューナー.

    LayerXの Generator→Executor→Evaluator→Memory→Sampling を実装。
    """

    def __init__(self, spec: WorkflowSpec, goldset_path: str | None = None, logs_dir: str = "logs"):
        """
        初期化.

        Args:
            spec: ワークフロー仕様
            goldset_path: ゴールドセットファイルパス（必須推奨）
            logs_dir: ログディレクトリ
        """
        self.spec = spec
        self.goldset_path = goldset_path
        self.logs_dir = Path(logs_dir)

        self.context_packager = ContextPackager()
        self.sampler = RepeatedSampler(
            n_samples=spec.budgets.n_samples,
            max_cost=spec.budgets.max_cost,
        )

        self._iterations: list[TuneIteration] = []
        self._best_fitness = 0.0
        self._best_config: dict[str, Any] = {}
        self._prev_best_scores: dict[str, float] | None = None

    def tune(
        self,
        generator: Callable[[dict[str, Any]], WorkflowSpec],
        evaluator: Callable[[WorkflowState], dict[str, float]],
        fitness_threshold: float = 0.8,
    ) -> TuneResult:
        """
        ワークフローをチューニング.

        Args:
            generator: コンテキストから候補specを生成する関数
            evaluator: 実行結果からスコアを評価する関数
            fitness_threshold: 終了条件のフィットネス閾値

        Returns:
            TuneResult
        """
        logger.info(f"Starting tune for {self.spec.workflow_id}")

        if self.goldset_path is None:
            logger.warning("No goldset provided. Tuning without goldset is risky.")

        for iteration in range(self.spec.budgets.max_iters):
            logger.info(f"Iteration {iteration + 1}/{self.spec.budgets.max_iters}")

            # 1. Generate: コンテキストを使って候補を生成
            context = self._prepare_context()

            # 2. Execute + Evaluate: Repeated Samplingで候補を実行・評価
            best_sample = self._sample_and_evaluate(generator, evaluator, context)

            if best_sample is None:
                logger.warning("No valid samples in this iteration")
                continue

            # 3. Memory: 結果を記録
            current_scores = best_sample.output.get("scores", {}) if best_sample.output else {}
            fitness = self._calculate_fitness(current_scores)

            is_improvement = fitness > self._best_fitness
            if is_improvement:
                self._best_fitness = fitness
                self._best_config = (
                    best_sample.output.get("config", {}) if best_sample.output else {}
                )

            self._iterations.append(
                TuneIteration(
                    iteration=iteration + 1,
                    samples=[best_sample],
                    best_sample=best_sample,
                    fitness_score=fitness,
                    is_improvement=is_improvement,
                    context_used=context,
                )
            )

            # メモリ更新（次のイテレーションのコンテキスト用）
            self.context_packager.add_log(
                LogEntry(
                    run_id=best_sample.sample_id,
                    step_id="tune",
                    score=fitness,
                    output_summary=str(best_sample.output)[:500],
                )
            )
            self._prev_best_scores = current_scores

            # 4. 終了条件チェック
            if fitness >= fitness_threshold:
                return self._finalize("threshold_reached", True)

            if self.sampler.total_cost >= self.spec.budgets.max_cost:
                return self._finalize("budget_exceeded", False)

        return self._finalize("max_iters", self._best_fitness >= fitness_threshold * 0.8)

    def _prepare_context(self) -> dict[str, Any]:
        """Generatorに渡すコンテキストを準備."""
        current_scores = {"fitness": self._best_fitness}
        return self.context_packager.package_for_generator(current_scores, self._prev_best_scores)

    def _sample_and_evaluate(
        self,
        generator: Callable[[dict[str, Any]], WorkflowSpec],
        evaluator: Callable[[WorkflowState], dict[str, float]],
        context: dict[str, Any],
    ) -> SampleResult | None:
        """候補をサンプリング・評価."""

        def gen() -> dict[str, Any]:
            spec = generator(context)
            runner = WorkflowRunner(spec, logs_dir=str(self.logs_dir))
            state = runner.run()
            scores = evaluator(state)
            return {"state": state, "scores": scores, "config": spec.to_dict()}

        def score(output: dict[str, Any]) -> float:
            scores = output.get("scores", {})
            return self._calculate_fitness(scores)

        return self.sampler.sample(gen, score)

    def _calculate_fitness(self, scores: dict[str, float]) -> float:
        """フィットネスを計算."""
        weights = self.spec.fitness

        fitness = 0.0
        fitness += weights.correctness * scores.get("correctness", 0.0)
        fitness += weights.regression * (1.0 - scores.get("regression", 0.0))
        fitness += weights.reproducibility * scores.get("reproducibility", 0.0)
        fitness += weights.cost * (1.0 - min(1.0, scores.get("cost", 0.0) / 10.0))
        fitness += weights.latency * (1.0 - min(1.0, scores.get("latency", 0.0) / 100.0))

        return fitness

    def _finalize(self, reason: str, converged: bool) -> TuneResult:
        """結果をまとめる."""
        logger.info(
            f"Tune finished: {reason}, converged={converged}, fitness={self._best_fitness:.3f}"
        )

        return TuneResult(
            workflow_id=self.spec.workflow_id,
            iterations=self._iterations,
            final_fitness=self._best_fitness,
            best_config=self._best_config,
            total_cost=self.sampler.total_cost,
            converged=converged,
            reason=reason,
        )

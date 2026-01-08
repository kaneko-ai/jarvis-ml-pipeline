"""
JARVIS Operations - Metrics & Observability

M4: 運用完備のための観測性
- run単位のメトリクス
- 品質メトリクス
- 継続的蓄積
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RunMetrics:
    """ラン単位のメトリクス."""

    run_id: str
    pipeline: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None

    # 時間
    total_duration_ms: int = 0
    stage_durations: dict[str, int] = field(default_factory=dict)

    # API
    api_calls: int = 0
    api_errors: int = 0
    api_retries: int = 0

    # 失敗
    failed_stages: list[str] = field(default_factory=list)
    degraded_stages: list[str] = field(default_factory=list)
    degraded_reasons: list[str] = field(default_factory=list)

    # ステータス
    status: str = "running"  # running, completed, failed, degraded

    # Knowledge base
    kb_updates: int = 0
    packs_generated: int = 0


@dataclass
class QualityMetrics:
    """品質メトリクス."""

    run_id: str

    # Provenance
    provenance_rate: float = 0.0
    facts_with_evidence: int = 0
    facts_without_evidence: int = 0

    # 整合性ゲート
    pico_consistency_rate: float = 0.0
    direction_consistency_rate: float = 0.0

    # 抽出
    extraction_completeness: float = 0.0
    missing_fields_count: int = 0

    # 品質ゲート
    gates_passed: int = 0
    gates_failed: int = 0
    gate_results: dict[str, bool] = field(default_factory=dict)


class MetricsCollector:
    """メトリクス収集器."""

    def __init__(self, base_path: str = "artifacts"):
        """
        初期化.

        Args:
            base_path: メトリクス保存先ベースパス
        """
        self.base_path = Path(base_path)
        self._current_run: RunMetrics | None = None
        self._current_quality: QualityMetrics | None = None
        self._stage_start_times: dict[str, float] = {}

    def start_run(self, run_id: str, pipeline: str) -> RunMetrics:
        """ランを開始."""
        self._current_run = RunMetrics(run_id=run_id, pipeline=pipeline)
        self._current_quality = QualityMetrics(run_id=run_id)
        self._stage_start_times = {}

        logger.info(f"Metrics collection started for run: {run_id}")
        return self._current_run

    def start_stage(self, stage_id: str):
        """ステージを開始."""
        self._stage_start_times[stage_id] = time.time()

    def end_stage(self, stage_id: str, success: bool = True, degraded: bool = False):
        """ステージを終了."""
        if stage_id in self._stage_start_times:
            duration_ms = int((time.time() - self._stage_start_times[stage_id]) * 1000)

            if self._current_run:
                self._current_run.stage_durations[stage_id] = duration_ms

                if not success:
                    self._current_run.failed_stages.append(stage_id)
                elif degraded:
                    self._current_run.degraded_stages.append(stage_id)

    def record_api_call(self, success: bool = True, retried: bool = False):
        """API呼び出しを記録."""
        if self._current_run:
            self._current_run.api_calls += 1
            if not success:
                self._current_run.api_errors += 1
            if retried:
                self._current_run.api_retries += 1

    def record_degraded(self, reason: str):
        """degraded状態を記録."""
        if self._current_run:
            self._current_run.degraded_reasons.append(reason)

    def record_kb_update(self, count: int = 1):
        """KB更新数を記録."""
        if self._current_run:
            self._current_run.kb_updates += count

    def record_pack_generation(self, count: int = 1):
        """学習パック生成数を記録."""
        if self._current_run:
            self._current_run.packs_generated += count

    def update_quality(
        self,
        provenance_rate: float | None = None,
        pico_consistency_rate: float | None = None,
        direction_consistency_rate: float | None = None,
        extraction_completeness: float | None = None,
        gate_name: str | None = None,
        gate_passed: bool | None = None,
    ):
        """品質メトリクスを更新."""
        if not self._current_quality:
            return

        if provenance_rate is not None:
            self._current_quality.provenance_rate = provenance_rate
        if pico_consistency_rate is not None:
            self._current_quality.pico_consistency_rate = pico_consistency_rate
        if direction_consistency_rate is not None:
            self._current_quality.direction_consistency_rate = direction_consistency_rate
        if extraction_completeness is not None:
            self._current_quality.extraction_completeness = extraction_completeness

        if gate_name is not None and gate_passed is not None:
            self._current_quality.gate_results[gate_name] = gate_passed
            if gate_passed:
                self._current_quality.gates_passed += 1
            else:
                self._current_quality.gates_failed += 1

    def end_run(self, status: str = "completed") -> dict[str, Any]:
        """ランを終了."""
        if not self._current_run:
            return {}

        self._current_run.completed_at = datetime.now().isoformat()
        self._current_run.status = status
        self._current_run.total_duration_ms = sum(self._current_run.stage_durations.values())

        # 保存
        metrics = self._save_metrics()

        logger.info(f"Metrics collection ended for run: {self._current_run.run_id}")

        return metrics

    def _save_metrics(self) -> dict[str, Any]:
        """メトリクスを保存."""
        if not self._current_run:
            return {}

        run_id = self._current_run.run_id
        metrics_dir = self.base_path / run_id
        metrics_dir.mkdir(parents=True, exist_ok=True)

        # ランメトリクス
        run_metrics = asdict(self._current_run)
        with open(metrics_dir / "run_metrics.json", "w", encoding="utf-8") as f:
            json.dump(run_metrics, f, ensure_ascii=False, indent=2)

        # 品質メトリクス
        if self._current_quality:
            quality_metrics = asdict(self._current_quality)
            with open(metrics_dir / "quality_metrics.json", "w", encoding="utf-8") as f:
                json.dump(quality_metrics, f, ensure_ascii=False, indent=2)

        # 集約ファイルに追記
        self._append_to_aggregate(run_metrics)

        return {
            "run": run_metrics,
            "quality": asdict(self._current_quality) if self._current_quality else {},
        }

    def _append_to_aggregate(self, run_metrics: dict[str, Any]):
        """集約ファイルに追記."""
        aggregate_path = self.base_path / "metrics_aggregate.jsonl"

        with open(aggregate_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(run_metrics, ensure_ascii=False) + "\n")

    def get_current_metrics(self) -> dict[str, Any] | None:
        """現在のメトリクスを取得."""
        if not self._current_run:
            return None

        return {
            "run": asdict(self._current_run),
            "quality": asdict(self._current_quality) if self._current_quality else {},
        }


# グローバルコレクター
_collector: MetricsCollector | None = None


def get_metrics_collector(base_path: str = "artifacts") -> MetricsCollector:
    """メトリクスコレクターを取得."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector(base_path)
    return _collector

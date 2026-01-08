"""
JARVIS Pipelines - 統一パイプライン定義

YAML定義によるパイプライン実行エンジン。
StageRegistry一本化 - 手動stage_handlers廃止。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from jarvis_core.contracts.types import Artifacts, Metrics, ResultBundle, TaskContext
from jarvis_core.obs import metrics
from jarvis_core.obs.logger import get_logger
from jarvis_core.pipelines.stage_registry import get_stage_registry
from jarvis_core.supervisor.lyra import LyraSupervisor, get_lyra


@dataclass
class StageResult:
    """ステージ実行結果."""

    stage_name: str
    success: bool
    duration_ms: float
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    provenance_rate: float = 0.0


def _parse_stages(raw_stages: list) -> list[str]:
    """
    ステージリストをパース。

    辞書形式（id付き）と文字列形式の両方をサポート。
    """
    stages = []
    for s in raw_stages:
        if isinstance(s, dict):
            stages.append(s["id"])
        else:
            stages.append(s)
    return stages


@dataclass
class PipelineConfig:
    """
    パイプライン設定.
    """

    name: str
    stages: list[str]
    policies: dict[str, Any] = field(default_factory=dict)
    version: int = 1

    @classmethod
    def from_yaml(cls, path: Path) -> PipelineConfig:
        """
        YAMLから読み込み.

        正式スキーマ:
        pipeline: fullstack
        version: 1
        stages:
          - id: retrieval.query_expand
          - id: retrieval.search_bm25
        policies:
          provenance_required: true
        """
        if not HAS_YAML:
            raise ImportError("pyyaml is required for pipeline YAML loading")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        raw_stages = data.get("stages", [])
        stages = _parse_stages(raw_stages)

        return cls(
            name=data.get("pipeline", data.get("name", "default")),
            stages=stages,
            policies=data.get("policies", {}),
            version=data.get("version", 1),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        """辞書から作成."""
        raw_stages = data.get("stages", [])
        stages = _parse_stages(raw_stages)

        return cls(
            name=data.get("pipeline", "default"),
            stages=stages,
            policies=data.get("policies", {}),
            version=data.get("version", 1),
        )


class PipelineExecutor:
    """
    パイプライン実行エンジン.

    - StageRegistryから全ハンドラを取得
    - 手動stage_handlersは廃止
    - YAMLで定義されたステージを順次実行
    - Lyra Supervisorによる監査
    - 根拠付け率の検証
    """

    def __init__(self, config: PipelineConfig, lyra: LyraSupervisor | None = None):
        self.config = config
        self.lyra = lyra or get_lyra()
        self.results: list[StageResult] = []
        self._registry = get_stage_registry()

        # デフォルトポリシー
        self.provenance_required = config.policies.get("provenance_required", True)
        self.refuse_if_no_evidence = config.policies.get("refuse_if_no_evidence", True)
        self.cache_policy = config.policies.get("cache", "aggressive")
        self.default_timeout = config.policies.get("timeouts", {}).get("stage_default_sec", 120)

    def run(self, context: TaskContext, artifacts: Artifacts) -> ResultBundle:
        """
        パイプラインを実行.

        Args:
            context: タスクコンテキスト
            artifacts: 入力成果物

        Returns:
            ResultBundle with all outputs and provenance

        Raises:
            StageNotImplementedError: 未登録ステージがあれば即失敗
        """
        start_time = time.time()
        self.results = []

        result = ResultBundle()
        obs_logger = get_logger(run_id=context.run_id, job_id=context.run_id, component="pipeline")
        metrics.record_run_start(run_id=context.run_id, job_id=context.run_id, component="pipeline")
        result.add_log(f"Pipeline {self.config.name} started")

        # StageRegistry事前検証 - 未登録は即失敗
        self._registry.validate_pipeline(self.config.stages)
        result.add_log(f"All {len(self.config.stages)} stages validated in registry")

        # Lyra supervision: validate the pipeline config
        lyra_task = self.lyra.supervise(
            f"Execute pipeline: {self.config.name} with {len(self.config.stages)} stages",
            context={"goal": context.goal, "domain": context.domain},
            task_type="complex",
        )
        result.add_log(f"Lyra supervision: {lyra_task.task_id}")

        # Execute each stage via StageRegistry
        for stage_name in self.config.stages:
            stage_result = self._execute_stage(stage_name, context, artifacts, obs_logger)
            self.results.append(stage_result)

            if not stage_result.success:
                result.mark_error(f"Stage {stage_name} failed: {stage_result.error}")
                if self.refuse_if_no_evidence:
                    break
            else:
                # Merge outputs
                for key, value in stage_result.outputs.items():
                    result.outputs[key] = value

        # Calculate metrics
        total_time = (time.time() - start_time) * 1000
        result.metrics = Metrics(
            execution_time_ms=total_time,
            provenance_rate=artifacts.get_provenance_rate(),
            claims_total=len(artifacts.claims),
            claims_with_evidence=sum(1 for c in artifacts.claims if c.has_evidence()),
            papers_processed=len(artifacts.papers),
        )

        # Validate provenance if required
        if self.provenance_required:
            rate = artifacts.get_provenance_rate()
            if rate < 0.95:
                result.add_log(f"WARNING: Provenance rate {rate:.2%} below threshold 95%")
                if self.refuse_if_no_evidence:
                    result.mark_error(f"Provenance rate {rate:.2%} below required 95%")

        result.provenance = artifacts.claims
        result.add_log(f"Pipeline {self.config.name} completed in {total_time:.0f}ms")
        obs_logger.step_end("Pipeline", data={"duration_ms": total_time})
        metrics.record_run_end(
            run_id=context.run_id,
            job_id=context.run_id,
            status="failed" if not result.success else "success",
            duration_ms=total_time,
            error_type="PipelineError" if not result.success else None,
            error_message=result.error if not result.success else None,
        )

        return result

    def _execute_stage(
        self,
        stage_name: str,
        context: TaskContext,
        artifacts: Artifacts,
        obs_logger: Any | None = None,
    ) -> StageResult:
        """
        個別ステージを実行.

        StageRegistryから取得したハンドラを実行。
        """
        start = time.time()
        if obs_logger:
            obs_logger.step_start(stage_name, message="stage start")

        # StageRegistryから取得（事前検証済みなので必ず存在）
        handler = self._registry.get(stage_name)

        try:
            # ハンドラ呼び出し - Artifactsを返すかDictを返すか両対応
            result = handler(context, artifacts)
            duration = (time.time() - start) * 1000

            # 戻り値がArtifactsならoutputsは空辞書
            if isinstance(result, Artifacts):
                outputs = {}
            elif isinstance(result, dict):
                outputs = result
            else:
                outputs = {}

            duration = (time.time() - start) * 1000
            if obs_logger:
                obs_logger.step_end(stage_name, data={"duration_ms": duration})
            metrics.record_step_duration(context.run_id, stage_name, duration)
            return StageResult(
                stage_name=stage_name,
                success=True,
                duration_ms=duration,
                outputs=outputs,
                provenance_rate=artifacts.get_provenance_rate(),
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            if obs_logger:
                obs_logger.error(f"stage {stage_name} failed", step=stage_name, exc=e)
            metrics.record_step_duration(context.run_id, stage_name, duration)
            return StageResult(
                stage_name=stage_name, success=False, duration_ms=duration, error=str(e)
            )

    def get_summary(self) -> dict[str, Any]:
        """実行サマリーを取得."""
        return {
            "pipeline": self.config.name,
            "stages_total": len(self.config.stages),
            "stages_executed": len(self.results),
            "stages_success": sum(1 for r in self.results if r.success),
            "total_duration_ms": sum(r.duration_ms for r in self.results),
            "results": [
                {
                    "stage": r.stage_name,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


# Default pipeline configuration
# YAMLから生成可能だが、フォールバックとしてハードコード版も保持
DEFAULT_PIPELINE = PipelineConfig.from_dict(
    {
        "pipeline": "fullstack",
        "version": 1,
        "stages": [
            "retrieval.query_expand",
            "retrieval.query_decompose",
            "retrieval.search_bm25",
            "retrieval.embed_sectionwise",
            "retrieval.rerank_crossencoder",
            "screening.pico_extract",
            "screening.filter_rules",
            "extraction.claims",
            "extraction.evidence_link",
            "extraction.numeric",
            "summarization.multigrain",
            "scoring.importance_confidence_roi",
            "knowledge_graph.build_and_index",
            "design.gap_and_next_experiments",
            "ops.audit_log_emit",
            "ui.render_bundle",
        ],
        "policies": {
            "provenance_required": True,
            "refuse_if_no_evidence": True,
            "cache": "aggressive",
            "timeouts": {"stage_default_sec": 120},
        },
    }
)


def get_pipeline_executor(config: PipelineConfig | None = None) -> PipelineExecutor:
    """パイプライン実行器を取得."""
    return PipelineExecutor(config or DEFAULT_PIPELINE)


def load_pipeline_from_yaml(path: Path) -> PipelineExecutor:
    """YAMLからパイプライン実行器を生成."""
    config = PipelineConfig.from_yaml(path)
    return PipelineExecutor(config)

"""
JARVIS Pipelines - 統一パイプライン定義

YAML定義によるパイプライン実行エンジン。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from jarvis_core.contracts.types import (
    Artifacts, ResultBundle, RuntimeConfig, TaskContext, Metrics
)
from jarvis_core.supervisor.lyra import get_lyra, LyraSupervisor


@dataclass
class StageResult:
    """ステージ実行結果."""
    stage_name: str
    success: bool
    duration_ms: float
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    provenance_rate: float = 0.0


@dataclass
class PipelineConfig:
    """
    パイプライン設定.
    """
    name: str
    stages: List[str]
    policies: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "PipelineConfig":
        """YAMLから読み込み."""
        if not HAS_YAML:
            raise ImportError("pyyaml is required for pipeline YAML loading")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return cls(
            name=data.get("pipeline", "default"),
            stages=data.get("stages", []),
            policies=data.get("policies", {})
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """辞書から作成."""
        return cls(
            name=data.get("pipeline", "default"),
            stages=data.get("stages", []),
            policies=data.get("policies", {})
        )


class PipelineExecutor:
    """
    パイプライン実行エンジン.
    
    - YAMLで定義されたステージを順次実行
    - Lyra Supervisorによる監査
    - 根拠付け率の検証
    """
    
    def __init__(self, config: PipelineConfig, 
                 lyra: Optional[LyraSupervisor] = None):
        self.config = config
        self.lyra = lyra or get_lyra()
        self.stage_handlers: Dict[str, Callable] = {}
        self.results: List[StageResult] = []
        
        # デフォルトポリシー
        self.provenance_required = config.policies.get("provenance_required", True)
        self.refuse_if_no_evidence = config.policies.get("refuse_if_no_evidence", True)
        self.cache_policy = config.policies.get("cache", "aggressive")
        self.default_timeout = config.policies.get("timeouts", {}).get("stage_default_sec", 120)
    
    def register_handler(self, stage_name: str, 
                         handler: Callable[[TaskContext, Artifacts], Dict[str, Any]]) -> None:
        """ステージハンドラを登録."""
        self.stage_handlers[stage_name] = handler
    
    def run(self, context: TaskContext, 
            artifacts: Artifacts) -> ResultBundle:
        """
        パイプラインを実行.
        
        Args:
            context: タスクコンテキスト
            artifacts: 入力成果物
        
        Returns:
            ResultBundle with all outputs and provenance
        """
        start_time = time.time()
        self.results = []
        
        result = ResultBundle()
        result.add_log(f"Pipeline {self.config.name} started")
        
        # Lyra supervision: validate the pipeline config
        lyra_task = self.lyra.supervise(
            f"Execute pipeline: {self.config.name} with {len(self.config.stages)} stages",
            context={"goal": context.goal, "domain": context.domain},
            task_type="complex"
        )
        result.add_log(f"Lyra supervision: {lyra_task.task_id}")
        
        # Execute each stage
        for stage_name in self.config.stages:
            stage_result = self._execute_stage(stage_name, context, artifacts)
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
            papers_processed=len(artifacts.papers)
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
        
        return result
    
    def _execute_stage(self, stage_name: str, 
                       context: TaskContext, 
                       artifacts: Artifacts) -> StageResult:
        """個別ステージを実行."""
        start = time.time()
        
        handler = self.stage_handlers.get(stage_name)
        if not handler:
            return StageResult(
                stage_name=stage_name,
                success=False,
                duration_ms=0,
                error=f"No handler registered for stage: {stage_name}"
            )
        
        try:
            outputs = handler(context, artifacts)
            duration = (time.time() - start) * 1000
            
            return StageResult(
                stage_name=stage_name,
                success=True,
                duration_ms=duration,
                outputs=outputs,
                provenance_rate=artifacts.get_provenance_rate()
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return StageResult(
                stage_name=stage_name,
                success=False,
                duration_ms=duration,
                error=str(e)
            )
    
    def get_summary(self) -> Dict[str, Any]:
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
                    "error": r.error
                }
                for r in self.results
            ]
        }


# Default pipeline configuration
DEFAULT_PIPELINE = PipelineConfig.from_dict({
    "pipeline": "fullstack",
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
        "ui.render_bundle"
    ],
    "policies": {
        "provenance_required": True,
        "refuse_if_no_evidence": True,
        "cache": "aggressive",
        "timeouts": {
            "stage_default_sec": 120
        }
    }
})


def get_pipeline_executor(config: Optional[PipelineConfig] = None) -> PipelineExecutor:
    """パイプライン実行器を取得."""
    return PipelineExecutor(config or DEFAULT_PIPELINE)

"""
JARVIS Workflow Specification

PDF知見統合: データ構造
- Mode: durable | step | hitl
- StepSpec: ステップ定義
- WorkflowSpec: ワークフロー全体定義
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Mode(Enum):
    """主導権モード.
    
    - STEP: 状態遷移として割り込み（Stepごとの遷移と再実行が明確）- MVP
    - HITL: 人間の判断をイベントとして前提化（保留/承認/修正）
    - DURABLE: 処理の中で割り込み（同一プロセス内で再試行/待機）
    """
    STEP = "step"
    HITL = "hitl"
    DURABLE = "durable"


@dataclass
class RetryPolicy:
    """リトライポリシー."""
    max_attempts: int = 3
    backoff_sec: int = 1


@dataclass
class StepSpec:
    """ステップ仕様.
    
    tool/router/plannerへの委譲を定義。
    """
    step_id: str
    action: str  # tool | router | planner | evaluator
    tool: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False  # HITL時に承認が必要か
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_sec: int = 120
    depends_on: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepSpec:
        """辞書から生成."""
        retry_data = data.get("retry_policy", {})
        return cls(
            step_id=data["step_id"],
            action=data["action"],
            tool=data.get("tool"),
            config=data.get("config", {}),
            requires_approval=data.get("requires_approval", False),
            retry_policy=RetryPolicy(
                max_attempts=retry_data.get("max_attempts", 3),
                backoff_sec=retry_data.get("backoff_sec", 1)
            ),
            timeout_sec=data.get("timeout_sec", 120),
            depends_on=data.get("depends_on", []),
        )


@dataclass
class FitnessWeights:
    """適応度関数の重み.
    
    Findyの"適応度関数"をJavisのゲートに落とす。
    """
    correctness: float = 0.4  # 引用精度、スキーマ準拠
    regression: float = 0.2   # 前回ベストより悪化していないか
    reproducibility: float = 0.2  # 再現性
    cost: float = 0.1         # 推論コスト
    latency: float = 0.1      # 時間

    def to_dict(self) -> dict[str, float]:
        """辞書に変換."""
        return {
            "correctness": self.correctness,
            "regression": self.regression,
            "reproducibility": self.reproducibility,
            "cost": self.cost,
            "latency": self.latency,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FitnessWeights:
        """辞書から生成."""
        return cls(
            correctness=data.get("correctness", 0.4),
            regression=data.get("regression", 0.2),
            reproducibility=data.get("reproducibility", 0.2),
            cost=data.get("cost", 0.1),
            latency=data.get("latency", 0.1),
        )


@dataclass
class Budgets:
    """予算制限.
    
    採用済み「8」に対応: コスト上限でn_samples自動調整。
    """
    max_tokens: int = 100000
    max_cost: float = 10.0
    max_iters: int = 10
    n_samples: int = 3  # Repeated Sampling のデフォルト

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Budgets:
        """辞書から生成."""
        return cls(
            max_tokens=data.get("max_tokens", 100000),
            max_cost=data.get("max_cost", 10.0),
            max_iters=data.get("max_iters", 10),
            n_samples=data.get("n_samples", 3),
        )


@dataclass
class WorkflowSpec:
    """ワークフロー仕様.
    
    Step Functions型でワークフローを定義。
    主導権（durable/step/hitl）を明示。
    """
    workflow_id: str
    mode: Mode
    objective: str
    steps: list[StepSpec]
    fitness: FitnessWeights = field(default_factory=FitnessWeights)
    budgets: Budgets = field(default_factory=Budgets)
    artifacts_dir: str = "artifacts"
    goldset: str | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> WorkflowSpec:
        """YAMLファイルから読み込み."""
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowSpec:
        """辞書から生成."""
        steps = [StepSpec.from_dict(s) for s in data.get("steps", [])]
        fitness = FitnessWeights.from_dict(data.get("fitness", {}))
        budgets = Budgets.from_dict(data.get("budgets", {}))

        return cls(
            workflow_id=data["workflow_id"],
            mode=Mode(data.get("mode", "step")),
            objective=data["objective"],
            steps=steps,
            fitness=fitness,
            budgets=budgets,
            artifacts_dir=data.get("artifacts", {}).get("output_dir", "artifacts"),
            goldset=data.get("goldset"),
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "workflow_id": self.workflow_id,
            "mode": self.mode.value,
            "objective": self.objective,
            "steps": [
                {
                    "step_id": s.step_id,
                    "action": s.action,
                    "tool": s.tool,
                    "config": s.config,
                    "requires_approval": s.requires_approval,
                }
                for s in self.steps
            ],
            "fitness": self.fitness.to_dict(),
            "budgets": {
                "max_tokens": self.budgets.max_tokens,
                "max_cost": self.budgets.max_cost,
                "max_iters": self.budgets.max_iters,
                "n_samples": self.budgets.n_samples,
            },
        }

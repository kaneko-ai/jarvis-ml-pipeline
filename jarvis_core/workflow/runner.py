"""
JARVIS Workflow Runner

PDF知見統合: Workflow実行エンジン
- step単位で実行
- 入出力・コスト・証拠・失敗を記録
- 状態は logs/runs/<run_id>/workflow_state.json に保存
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .spec import Mode, StepSpec, WorkflowSpec

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """ステップ状態."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"  # HITL
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class StepResult:
    """ステップ実行結果."""
    step_id: str
    status: StepStatus
    output: Any = None
    error: str | None = None
    cost: float = 0.0
    latency_sec: float = 0.0
    evidence: list[str] = field(default_factory=list)
    attempts: int = 1
    started_at: str | None = None
    completed_at: str | None = None


@dataclass
class WorkflowState:
    """ワークフロー状態.
    
    Step modeのMVP: step単位で状態を保存・再開。
    """
    run_id: str
    workflow_id: str
    mode: Mode
    current_step_index: int = 0
    step_results: list[StepResult] = field(default_factory=list)
    total_cost: float = 0.0
    total_latency_sec: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    status: str = "running"  # running | completed | failed | paused

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "mode": self.mode.value,
            "current_step_index": self.current_step_index,
            "step_results": [
                {
                    "step_id": r.step_id,
                    "status": r.status.value,
                    "output": r.output,
                    "error": r.error,
                    "cost": r.cost,
                    "latency_sec": r.latency_sec,
                    "attempts": r.attempts,
                }
                for r in self.step_results
            ],
            "total_cost": self.total_cost,
            "total_latency_sec": self.total_latency_sec,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
        }

    def save(self, logs_dir: Path):
        """状態を保存."""
        run_dir = logs_dir / "runs" / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        state_file = run_dir / "workflow_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, logs_dir: Path, run_id: str) -> WorkflowState:
        """状態を読み込み."""
        state_file = logs_dir / "runs" / run_id / "workflow_state.json"
        with open(state_file, encoding='utf-8') as f:
            data = json.load(f)

        state = cls(
            run_id=data["run_id"],
            workflow_id=data["workflow_id"],
            mode=Mode(data["mode"]),
            current_step_index=data["current_step_index"],
            total_cost=data["total_cost"],
            total_latency_sec=data["total_latency_sec"],
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            status=data["status"],
        )

        for r in data.get("step_results", []):
            state.step_results.append(StepResult(
                step_id=r["step_id"],
                status=StepStatus(r["status"]),
                output=r.get("output"),
                error=r.get("error"),
                cost=r.get("cost", 0),
                latency_sec=r.get("latency_sec", 0),
                attempts=r.get("attempts", 1),
            ))

        return state


class WorkflowRunner:
    """ワークフローランナー.
    
    Step mode MVP: step単位で順次実行。
    失敗時はstep単位で再試行。
    """

    def __init__(
        self,
        spec: WorkflowSpec,
        logs_dir: str = "logs",
        step_handlers: dict[str, Callable] | None = None
    ):
        """
        初期化.
        
        Args:
            spec: ワークフロー仕様
            logs_dir: ログディレクトリ
            step_handlers: ステップハンドラー辞書
        """
        self.spec = spec
        self.logs_dir = Path(logs_dir)
        self.step_handlers = step_handlers or {}
        self._state: WorkflowState | None = None

    def run(self, run_id: str | None = None) -> WorkflowState:
        """
        ワークフローを実行.
        
        Args:
            run_id: 実行ID（指定時は再開）
        
        Returns:
            WorkflowState
        """
        if run_id and self._try_resume(run_id):
            logger.info(f"Resuming workflow {self.spec.workflow_id} from run {run_id}")
        else:
            self._state = WorkflowState(
                run_id=run_id or str(uuid.uuid4())[:8],
                workflow_id=self.spec.workflow_id,
                mode=self.spec.mode,
            )

        logger.info(f"Running workflow {self.spec.workflow_id} in {self.spec.mode.value} mode")

        try:
            self._execute_steps()
            self._state.status = "completed"
            self._state.completed_at = datetime.now().isoformat()
        except Exception as e:
            self._state.status = "failed"
            logger.error(f"Workflow failed: {e}")

        self._state.save(self.logs_dir)
        return self._state

    def _try_resume(self, run_id: str) -> bool:
        """再開を試みる."""
        try:
            self._state = WorkflowState.load(self.logs_dir, run_id)
            return True
        except FileNotFoundError:
            return False

    def _execute_steps(self):
        """ステップを順次実行."""
        while self._state.current_step_index < len(self.spec.steps):
            step = self.spec.steps[self._state.current_step_index]

            # HITL: 承認待ちチェック
            if self.spec.mode == Mode.HITL and step.requires_approval:
                result = self._wait_for_approval(step)
                if result.status == StepStatus.REJECTED:
                    raise RuntimeError(f"Step {step.step_id} rejected")
            else:
                result = self._execute_step(step)

            self._state.step_results.append(result)
            self._state.total_cost += result.cost
            self._state.total_latency_sec += result.latency_sec

            if result.status == StepStatus.FAILED:
                raise RuntimeError(f"Step {step.step_id} failed: {result.error}")

            self._state.current_step_index += 1
            self._state.save(self.logs_dir)

    def _execute_step(self, step: StepSpec) -> StepResult:
        """単一ステップを実行."""
        started_at = datetime.now().isoformat()
        start_time = time.time()

        handler = self.step_handlers.get(step.action)
        if not handler:
            handler = self._default_handler

        attempts = 0
        last_error = None

        while attempts < step.retry_policy.max_attempts:
            attempts += 1
            try:
                output = handler(step)
                elapsed = time.time() - start_time

                return StepResult(
                    step_id=step.step_id,
                    status=StepStatus.COMPLETED,
                    output=output,
                    latency_sec=elapsed,
                    attempts=attempts,
                    started_at=started_at,
                    completed_at=datetime.now().isoformat(),
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Step {step.step_id} attempt {attempts} failed: {e}")
                if attempts < step.retry_policy.max_attempts:
                    time.sleep(step.retry_policy.backoff_sec)

        return StepResult(
            step_id=step.step_id,
            status=StepStatus.FAILED,
            error=last_error,
            attempts=attempts,
            started_at=started_at,
            completed_at=datetime.now().isoformat(),
        )

    def _wait_for_approval(self, step: StepSpec) -> StepResult:
        """承認待ち（HITL mode）."""
        logger.info(f"Step {step.step_id} waiting for approval")

        # MVP: 自動承認（本番では外部入力を待つ）
        return StepResult(
            step_id=step.step_id,
            status=StepStatus.APPROVED,
        )

    def _default_handler(self, step: StepSpec) -> Any:
        """デフォルトハンドラー."""
        logger.info(f"Executing step {step.step_id} with action {step.action}")
        return {"step_id": step.step_id, "action": step.action, "status": "executed"}

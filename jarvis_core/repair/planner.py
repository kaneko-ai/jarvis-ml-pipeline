"""Repair Planner (R-01).

失敗時の自己修正戦略。fail_reason別の処方箋を定義し、
適切な修復アクションを提案する。

Per BUNDLE_CONTRACT.md fail_reasons:
- CITATION_MISSING: 引用がゼロ
- EVIDENCE_WEAK: 根拠が薄い
- LOCATOR_MISSING: 根拠位置情報がない
- ASSERTION_DANGER: 断定の危険
- PII_DETECTED: PII検出
- FETCH_FAIL: 取得失敗
- INDEX_MISSING: 索引なし
- BUDGET_EXCEEDED: 予算超過
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class RepairAction(Enum):
    """修復アクション種別."""

    EXPAND_QUERY = "expand_query"  # クエリ拡張
    RELAX_FILTERS = "relax_filters"  # フィルタ緩和
    ADD_SYNONYMS = "add_synonyms"  # 同義語追加
    INCREASE_PAPERS = "increase_papers"  # 論文数増加
    RERUN_EXTRACTION = "rerun_extraction"  # 抽出再実行
    LOWER_THRESHOLD = "lower_threshold"  # 閾値緩和
    ADD_LOCATORS = "add_locators"  # locator補完
    REDACT_PII = "redact_pii"  # PII削除
    RETRY_FETCH = "retry_fetch"  # 再取得
    REBUILD_INDEX = "rebuild_index"  # 索引再構築
    REDUCE_SCOPE = "reduce_scope"  # スコープ縮小
    REFUSE_ANSWER = "refuse_answer"  # 回答拒否（不明）


@dataclass
class RepairStep:
    """修復ステップ."""

    action: RepairAction
    params: dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=高, 3=低
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "params": self.params,
            "priority": self.priority,
            "reason": self.reason,
        }


@dataclass
class RepairPlan:
    """修復計画."""

    fail_code: str
    steps: list[RepairStep] = field(default_factory=list)
    max_retries: int = 3
    should_refuse: bool = False
    refuse_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "fail_code": self.fail_code,
            "steps": [s.to_dict() for s in self.steps],
            "max_retries": self.max_retries,
            "should_refuse": self.should_refuse,
            "refuse_reason": self.refuse_reason,
        }


# 処方箋定義: fail_code -> 修復ステップリスト
REMEDY_CATALOG: dict[str, list[RepairStep]] = {
    "CITATION_MISSING": [
        RepairStep(
            action=RepairAction.EXPAND_QUERY,
            priority=1,
            reason="検索クエリを拡張してより多くの論文を取得",
            params={"expansion_strategy": "synonyms"},
        ),
        RepairStep(
            action=RepairAction.ADD_SYNONYMS,
            priority=1,
            reason="専門用語の同義語を追加",
            params={"use_mesh": True},
        ),
        RepairStep(
            action=RepairAction.INCREASE_PAPERS,
            priority=2,
            reason="取得論文数を増加",
            params={"increase_by": 10},
        ),
    ],
    "EVIDENCE_WEAK": [
        RepairStep(
            action=RepairAction.LOWER_THRESHOLD,
            priority=1,
            reason="根拠スコア閾値を緩和",
            params={"new_threshold": 0.4},
        ),
        RepairStep(
            action=RepairAction.RERUN_EXTRACTION,
            priority=2,
            reason="異なるプロンプトで抽出再実行",
            params={"prompt_variant": "detailed"},
        ),
    ],
    "LOCATOR_MISSING": [
        RepairStep(
            action=RepairAction.ADD_LOCATORS,
            priority=1,
            reason="PDFから位置情報を再抽出",
            params={"use_pdf_parser": True},
        ),
        RepairStep(
            action=RepairAction.RERUN_EXTRACTION,
            priority=2,
            reason="locator必須モードで再抽出",
            params={"require_locator": True},
        ),
    ],
    "ASSERTION_DANGER": [
        RepairStep(
            action=RepairAction.REFUSE_ANSWER,
            priority=1,
            reason="断定を避け「不明」として回答",
            params={"add_uncertainty_note": True},
        ),
    ],
    "PII_DETECTED": [
        RepairStep(
            action=RepairAction.REDACT_PII,
            priority=1,
            reason="検出されたPIIを削除",
            params={"patterns": ["email", "phone", "address"]},
        ),
    ],
    "FETCH_FAIL": [
        RepairStep(
            action=RepairAction.RETRY_FETCH,
            priority=1,
            reason="取得を再試行",
            params={"delay_seconds": 5, "max_retries": 3},
        ),
        RepairStep(
            action=RepairAction.RELAX_FILTERS,
            priority=2,
            reason="OA以外も許可",
            params={"allow_non_oa": True},
        ),
    ],
    "INDEX_MISSING": [
        RepairStep(
            action=RepairAction.REBUILD_INDEX,
            priority=1,
            reason="ベクトル索引を再構築",
            params={"force": True},
        ),
    ],
    "BUDGET_EXCEEDED": [
        RepairStep(
            action=RepairAction.REDUCE_SCOPE,
            priority=1,
            reason="処理範囲を縮小",
            params={"reduce_papers_by": 0.5},
        ),
        RepairStep(
            action=RepairAction.REFUSE_ANSWER,
            priority=2,
            reason="予算内では回答不可と報告",
            params={"add_budget_note": True},
        ),
    ],
    "EXECUTION_ERROR": [
        RepairStep(
            action=RepairAction.REFUSE_ANSWER,
            priority=1,
            reason="システムエラーにより回答不可",
            params={"report_error": True},
        ),
    ],
}


class RepairPlanner:
    """修復計画立案器."""

    def __init__(
        self,
        history_file: Path | None = None,
        max_retries_per_code: int = 3,
    ):
        self.history_file = history_file or Path("logs/repair_history.jsonl")
        self.max_retries_per_code = max_retries_per_code
        self._history: list[dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        """修復履歴を読み込み."""
        if self.history_file.exists():
            try:
                with open(self.history_file, encoding="utf-8") as f:
                    self._history = [json.loads(line) for line in f if line.strip()]
            except Exception:
                self._history = []

    def _save_history_entry(self, entry: dict) -> None:
        """履歴エントリを追加."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._history.append(entry)

    def plan(
        self,
        fail_reasons: list[dict[str, Any]],
        run_id: str,
        attempt: int = 1,
    ) -> RepairPlan:
        """失敗理由から修復計画を立案.

        Args:
            fail_reasons: [{code, msg}] 形式の失敗理由リスト
            run_id: 現在のrun_id
            attempt: 現在の試行回数

        Returns:
            RepairPlan: 修復計画
        """
        if not fail_reasons:
            return RepairPlan(
                fail_code="UNKNOWN", should_refuse=True, refuse_reason="No fail reasons provided"
            )

        # 主要な失敗コードを特定
        primary_code = fail_reasons[0].get("code", "UNKNOWN")

        # 同一コードの過去試行回数をチェック
        past_attempts = sum(
            1
            for h in self._history
            if h.get("run_id") == run_id and h.get("fail_code") == primary_code
        )

        if past_attempts >= self.max_retries_per_code:
            # リトライ上限到達 → 拒否
            return RepairPlan(
                fail_code=primary_code,
                should_refuse=True,
                refuse_reason=f"Maximum retries ({self.max_retries_per_code}) reached for {primary_code}",
            )

        # 処方箋カタログから取得
        steps = REMEDY_CATALOG.get(primary_code, [])

        if not steps:
            # 未知のコード → 拒否
            return RepairPlan(
                fail_code=primary_code,
                should_refuse=True,
                refuse_reason=f"No remedy available for {primary_code}",
            )

        # 優先度順にソート
        sorted_steps = sorted(steps, key=lambda s: s.priority)

        # 計画作成
        plan = RepairPlan(
            fail_code=primary_code,
            steps=sorted_steps,
            max_retries=self.max_retries_per_code - past_attempts,
        )

        # REFUSE_ANSWERが最初のステップならshould_refuse=True
        if sorted_steps and sorted_steps[0].action == RepairAction.REFUSE_ANSWER:
            plan.should_refuse = True
            plan.refuse_reason = sorted_steps[0].reason

        # 履歴記録
        self._save_history_entry(
            {
                "run_id": run_id,
                "fail_code": primary_code,
                "attempt": attempt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "plan": plan.to_dict(),
            }
        )

        return plan

    def should_refuse(self, plan: RepairPlan) -> bool:
        """計画が回答拒否を示しているか."""
        return plan.should_refuse

    def get_next_action(self, plan: RepairPlan, step_index: int = 0) -> RepairStep | None:
        """次の修復アクションを取得."""
        if step_index >= len(plan.steps):
            return None
        return plan.steps[step_index]

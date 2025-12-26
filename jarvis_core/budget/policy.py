"""
JARVIS Budget Policy

予算に基づく意思決定ポリシー
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .budget import BudgetSpec, BudgetTracker


@dataclass(frozen=True)
class BudgetDecision:
    """予算決定."""
    should_search: bool
    num_results: int
    summary_depth: int
    allow_retry: bool
    degrade_reason: Optional[str] = None


class BudgetPolicy:
    """予算ポリシー.
    
    予算状況に応じて探索/要約/リトライの可否を決定する。
    """
    
    def decide(self, spec: BudgetSpec, tracker: BudgetTracker) -> BudgetDecision:
        """
        予算に基づいて決定を下す.
        
        Args:
            spec: 予算仕様
            tracker: 予算追跡器
        
        Returns:
            BudgetDecision
        """
        # 予算超過チェック
        if tracker.tool_calls_used >= spec.max_tool_calls:
            return BudgetDecision(
                should_search=False,
                num_results=0,
                summary_depth=1,
                allow_retry=False,
                degrade_reason="max_tool_calls reached"
            )
        
        # リトライ可否
        allow_retry = tracker.retries_used < spec.max_retries
        
        # 残り予算に応じた調整
        remaining_ratio = tracker.get_remaining_tool_calls(spec) / spec.max_tool_calls
        
        # モードに応じた基本設定
        if spec.mode == "fast":
            return BudgetDecision(
                should_search=True,
                num_results=min(3, spec.max_search_results),
                summary_depth=1,
                allow_retry=allow_retry
            )
        
        if spec.mode == "high":
            return BudgetDecision(
                should_search=True,
                num_results=spec.max_search_results,
                summary_depth=spec.max_summary_depth,
                allow_retry=allow_retry
            )
        
        # standard: 残り予算で調整
        if remaining_ratio < 0.3:
            # 残り少ない：控えめに
            return BudgetDecision(
                should_search=True,
                num_results=min(3, spec.max_search_results),
                summary_depth=1,
                allow_retry=False,
                degrade_reason="budget_low"
            )
        
        return BudgetDecision(
            should_search=True,
            num_results=min(6, spec.max_search_results),
            summary_depth=min(2, spec.max_summary_depth),
            allow_retry=allow_retry
        )
    
    def check_and_record(
        self, 
        spec: BudgetSpec, 
        tracker: BudgetTracker,
        action: str
    ) -> BudgetDecision:
        """
        チェックして記録.
        
        Args:
            spec: 予算仕様
            tracker: 予算追跡器
            action: アクション名（"search", "retry", etc）
        
        Returns:
            BudgetDecision
        """
        decision = self.decide(spec, tracker)
        
        # degrade理由があれば記録
        if decision.degrade_reason:
            tracker.record_degrade(decision.degrade_reason)
        
        return decision

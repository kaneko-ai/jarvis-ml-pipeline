"""
JARVIS Budget Control

推論コスト制御（test-time scaling）
- 検索・再試行・要約深度をBudgetで統制
- 無限探索禁止
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BudgetSpec:
    """予算仕様.
    
    mode:
        - fast: 最小限の探索、高速応答優先
        - standard: バランス型（デフォルト）
        - high: 深い探索、品質優先
    """
    mode: str = "standard"  # fast | standard | high
    max_tool_calls: int = 30
    max_retries: int = 2
    max_search_results: int = 10
    max_summary_depth: int = 3  # 粒度（段落/セクション数の上限）
    hard_timeout_sec: int | None = None
    allow_fallback: bool = True

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> BudgetSpec:
        """設定辞書から生成."""
        budget_config = config.get("budget", {})
        return cls(
            mode=budget_config.get("mode", "standard"),
            max_tool_calls=budget_config.get("max_tool_calls", 30),
            max_retries=budget_config.get("max_retries", 2),
            max_search_results=budget_config.get("max_search_results", 10),
            max_summary_depth=budget_config.get("max_summary_depth", 3),
            hard_timeout_sec=budget_config.get("hard_timeout_sec"),
            allow_fallback=budget_config.get("allow_fallback", True),
        )

    @classmethod
    def fast(cls) -> BudgetSpec:
        """高速モード."""
        return cls(mode="fast", max_tool_calls=10, max_retries=1,
                   max_search_results=3, max_summary_depth=1)

    @classmethod
    def high(cls) -> BudgetSpec:
        """高品質モード."""
        return cls(mode="high", max_tool_calls=50, max_retries=3,
                   max_search_results=20, max_summary_depth=5)


@dataclass
class BudgetEvent:
    """予算イベント."""
    kind: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetTracker:
    """予算追跡器."""
    tool_calls_used: int = 0
    retries_used: int = 0
    search_results_used: int = 0
    summary_depth_used: int = 0
    events: list[BudgetEvent] = field(default_factory=list)
    degraded: bool = False
    degrade_reasons: list[str] = field(default_factory=list)

    def log(self, kind: str, **detail: Any) -> None:
        """イベントを記録."""
        self.events.append(BudgetEvent(kind=kind, detail=dict(detail)))

    def record_tool_call(self, n: int = 1) -> None:
        """ツール呼び出しを記録."""
        self.tool_calls_used += n
        self.log("tool_call", count=n, total=self.tool_calls_used)

    def record_retry(self) -> None:
        """リトライを記録."""
        self.retries_used += 1
        self.log("retry", total=self.retries_used)

    def record_search_results(self, n: int) -> None:
        """検索結果を記録."""
        self.search_results_used += n
        self.log("search_results", count=n, total=self.search_results_used)

    def record_degrade(self, reason: str) -> None:
        """degrade状態を記録."""
        self.degraded = True
        self.degrade_reasons.append(reason)
        self.log("degrade", reason=reason)

    def can_call_tool(self, spec: BudgetSpec, n: int = 1) -> bool:
        """ツール呼び出し可能か."""
        return (self.tool_calls_used + n) <= spec.max_tool_calls

    def can_retry(self, spec: BudgetSpec) -> bool:
        """リトライ可能か."""
        return self.retries_used < spec.max_retries

    def get_remaining_tool_calls(self, spec: BudgetSpec) -> int:
        """残りツール呼び出し数."""
        return max(0, spec.max_tool_calls - self.tool_calls_used)

    def to_summary(self, spec: BudgetSpec) -> dict[str, Any]:
        """サマリーを出力."""
        return {
            "mode": spec.mode,
            "tool_calls": f"{self.tool_calls_used}/{spec.max_tool_calls}",
            "retries": f"{self.retries_used}/{spec.max_retries}",
            "degraded": self.degraded,
            "degrade_reasons": self.degrade_reasons if self.degraded else None,
        }

"""Retry Controller - fail_reason → action マップ.

Phase Loop 3: 半自律（自動改善）
- fail_reason に基づく再試行
- 回数上限あり
- 変更点を必ずログ化
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetryAction(Enum):
    """再試行アクション."""
    RE_SEARCH = "re_search"           # 再検索
    RE_EXTRACT = "re_extract"         # chunk再抽出
    EXPAND_QUERY = "expand_query"     # クエリ拡張
    ADD_SOURCES = "add_sources"       # ソース追加
    NONE = "none"                     # 再試行なし


# fail_reason → action マップ（コード固定・例外禁止）
FAIL_ACTION_MAP: Dict[str, RetryAction] = {
    "CITATION_MISSING": RetryAction.RE_SEARCH,
    "EVIDENCE_WEAK": RetryAction.RE_EXTRACT,
    "LOCATOR_MISSING": RetryAction.RE_EXTRACT,
    "FETCH_FAIL": RetryAction.RE_SEARCH,
    "INDEX_MISSING": RetryAction.ADD_SOURCES,
    # 以下は再試行不可
    "ASSERTION_DANGER": RetryAction.NONE,
    "PII_DETECTED": RetryAction.NONE,
    "BUDGET_EXCEEDED": RetryAction.NONE,
    "VERIFY_NOT_RUN": RetryAction.NONE,
}


@dataclass
class RetryAttempt:
    """再試行の記録."""
    attempt_number: int
    fail_reason: str
    action_taken: RetryAction
    changes_made: Dict[str, Any]
    result: str  # "improved", "unchanged", "degraded"


@dataclass
class RetryResult:
    """Retry結果."""
    success: bool
    attempts: List[RetryAttempt] = field(default_factory=list)
    final_status: str = "failed"
    max_retries_reached: bool = False


class RetryController:
    """再試行コントローラー.
    
    Phase Loop 3: 自動改善の最小実装
    - fail_reason → action マップ固定
    - 回数上限あり
    - 変更点をログ化
    """
    
    # 最大再試行回数（固定）
    MAX_RETRIES = 3
    
    def __init__(
        self,
        max_retries: int = MAX_RETRIES,
        action_handlers: Optional[Dict[RetryAction, Callable]] = None,
    ):
        """初期化.
        
        Args:
            max_retries: 最大再試行回数
            action_handlers: アクション→ハンドラーのマップ
        """
        self.max_retries = max_retries
        self.action_handlers = action_handlers or {}
        self.attempts: List[RetryAttempt] = []
    
    def get_action_for_fail_reason(self, fail_reason: str) -> RetryAction:
        """fail_reasonに対応するアクションを取得.
        
        Args:
            fail_reason: 失敗理由コード
        
        Returns:
            対応するRetryAction
        """
        return FAIL_ACTION_MAP.get(fail_reason, RetryAction.NONE)
    
    def should_retry(self, fail_reasons: List[str]) -> bool:
        """再試行すべきかを判定.
        
        Args:
            fail_reasons: 失敗理由コードのリスト
        
        Returns:
            再試行すべきならTrue
        """
        if len(self.attempts) >= self.max_retries:
            return False
        
        # 再試行可能なfail_reasonが1つでもあるか
        for reason in fail_reasons:
            action = self.get_action_for_fail_reason(reason)
            if action != RetryAction.NONE:
                return True
        
        return False
    
    def execute_retry(
        self,
        fail_reasons: List[str],
        context: Dict[str, Any],
    ) -> RetryAttempt:
        """再試行を実行.
        
        Args:
            fail_reasons: 失敗理由コードのリスト
            context: 実行コンテキスト
        
        Returns:
            RetryAttempt
        """
        attempt_number = len(self.attempts) + 1
        
        # 最初のactionable fail_reasonを使用
        target_reason = None
        action = RetryAction.NONE
        
        for reason in fail_reasons:
            action = self.get_action_for_fail_reason(reason)
            if action != RetryAction.NONE:
                target_reason = reason
                break
        
        if action == RetryAction.NONE:
            logger.warning(f"No actionable retry for {fail_reasons}")
            return RetryAttempt(
                attempt_number=attempt_number,
                fail_reason=fail_reasons[0] if fail_reasons else "UNKNOWN",
                action_taken=RetryAction.NONE,
                changes_made={},
                result="unchanged",
            )
        
        # ハンドラーを実行
        changes_made = {}
        result = "unchanged"
        
        handler = self.action_handlers.get(action)
        if handler:
            try:
                changes_made = handler(context)
                result = "improved" if changes_made else "unchanged"
            except Exception as e:
                logger.error(f"Retry handler failed: {e}")
                result = "degraded"
        else:
            logger.warning(f"No handler for action {action}")
        
        attempt = RetryAttempt(
            attempt_number=attempt_number,
            fail_reason=target_reason or "UNKNOWN",
            action_taken=action,
            changes_made=changes_made,
            result=result,
        )
        
        self.attempts.append(attempt)
        
        # ログ出力
        logger.info(
            f"Retry attempt {attempt_number}: "
            f"{target_reason} → {action.value} → {result}"
        )
        
        return attempt
    
    def get_result(self, final_success: bool) -> RetryResult:
        """最終結果を取得.
        
        Args:
            final_success: 最終的に成功したか
        
        Returns:
            RetryResult
        """
        return RetryResult(
            success=final_success,
            attempts=self.attempts,
            final_status="success" if final_success else "failed",
            max_retries_reached=len(self.attempts) >= self.max_retries,
        )
    
    def log_summary(self) -> Dict[str, Any]:
        """再試行のサマリーをログ用に生成."""
        return {
            "total_attempts": len(self.attempts),
            "max_retries": self.max_retries,
            "attempts": [
                {
                    "attempt": a.attempt_number,
                    "fail_reason": a.fail_reason,
                    "action": a.action_taken.value,
                    "result": a.result,
                    "changes": list(a.changes_made.keys()) if a.changes_made else [],
                }
                for a in self.attempts
            ],
        }

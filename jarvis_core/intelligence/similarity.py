"""
JARVIS Similarity Searcher

Phase 2: 類似Decision検索
- 新Issue生成時に過去の類似判断Top3を必ず提示
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from .decision_item import DecisionItem, DecisionStore

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """類似度検索結果."""
    decision: DecisionItem
    similarity_score: float
    match_reason: str


class SimilaritySearcher:
    """類似Decision検索器.
    
    新しいIssue生成時：
    - 過去のDecisionを検索
    - 類似度の高いもの Top3 を必ず提示
    """
    
    def __init__(self, store: Optional[DecisionStore] = None):
        """
        初期化.
        
        Args:
            store: DecisionStore
        """
        self.store = store or DecisionStore()
    
    def search(
        self,
        context: str,
        top_k: int = 3
    ) -> List[SimilarityResult]:
        """
        類似Decisionを検索.
        
        Args:
            context: 新しいIssueのコンテキスト
            top_k: 上位何件
        
        Returns:
            SimilarityResult リスト（類似度降順）
        """
        decisions = self.store.list_all()
        if not decisions:
            return []
        
        results = []
        for d in decisions:
            score, reason = self._calc_similarity(context, d)
            if score > 0:
                results.append(SimilarityResult(
                    decision=d,
                    similarity_score=score,
                    match_reason=reason,
                ))
        
        # スコア降順でソート
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results[:top_k]
    
    def _calc_similarity(
        self,
        context: str,
        decision: DecisionItem
    ) -> tuple[float, str]:
        """
        類似度を計算.
        
        Args:
            context: 新しいコンテキスト
            decision: 過去のDecision
        
        Returns:
            (スコア, 理由)
        """
        context_lower = context.lower()
        decision_context_lower = decision.context.lower()
        
        # キーワードマッチ（簡易）
        # 本番ではベクトル類似度を使用
        context_words = set(context_lower.split())
        decision_words = set(decision_context_lower.split())
        
        if not context_words or not decision_words:
            return 0.0, ""
        
        intersection = context_words & decision_words
        union = context_words | decision_words
        
        if not union:
            return 0.0, ""
        
        jaccard = len(intersection) / len(union)
        
        if jaccard > 0.3:
            matched = list(intersection)[:3]
            reason = f"Matched keywords: {', '.join(matched)}"
            return jaccard, reason
        
        return 0.0, ""
    
    def format_for_prompt(
        self,
        results: List[SimilarityResult]
    ) -> str:
        """
        プロンプト用にフォーマット.
        
        Args:
            results: 検索結果
        
        Returns:
            文字列
        """
        if not results:
            return "No similar past decisions found."
        
        lines = ["## Similar Past Decisions\n"]
        
        for i, r in enumerate(results, 1):
            lines.append(f"### {i}. {r.decision.context[:50]}...")
            lines.append(f"- **Decision**: {r.decision.decision}")
            lines.append(f"- **Pattern**: {r.decision.pattern.value}")
            lines.append(f"- **Reason**: {r.decision.reason}")
            if r.decision.outcome_status:
                lines.append(f"- **Outcome**: {r.decision.outcome_status}")
            lines.append(f"- **Match**: {r.match_reason} (score: {r.similarity_score:.2f})")
            lines.append("")
        
        return "\n".join(lines)

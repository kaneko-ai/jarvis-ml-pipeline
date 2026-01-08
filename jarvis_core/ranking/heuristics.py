"""
JARVIS Heuristic Ranker

ルールベースのランキング実装
"""

from __future__ import annotations

from typing import Any

from .base import Ranker, RankingItem


class HeuristicRanker(Ranker):
    """ヒューリスティックランカー.
    
    シンプルなスコアリング関数でランキング。
    LightGBM導入前の初期実装。
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None
    ):
        """
        初期化.
        
        Args:
            weights: 特徴量の重み
        """
        self.weights = weights or {
            "relevance": 1.0,
            "recency_days": -0.001,
            "cost_estimate": -0.1,
            "priority": 0.5,
        }

    def score(self, item: RankingItem) -> float:
        """
        アイテムのスコアを計算.
        
        Args:
            item: ランキングアイテム
        
        Returns:
            スコア（高いほど優先）
        """
        total = 0.0

        for feature_name, weight in self.weights.items():
            value = item.get_feature(feature_name, 0.0)
            total += float(value) * weight

        return total

    def rank(
        self,
        items: list[RankingItem],
        context: dict[str, Any]
    ) -> list[RankingItem]:
        """
        アイテムをランキング.
        
        Args:
            items: ランキング対象
            context: コンテキスト（将来的なコンテキスト依存スコアリング用）
        
        Returns:
            スコア降順でソートされたアイテム
        """
        return sorted(items, key=self.score, reverse=True)

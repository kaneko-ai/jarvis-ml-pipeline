"""
JARVIS Ranking Base

ランキングの基礎インターフェース
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass
class RankingItem:
    """ランキング対象アイテム."""
    item_id: str
    item_type: str  # paper | subtask | retry | ...
    features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_feature(self, name: str, default: Any = 0.0) -> Any:
        """特徴量を取得."""
        return self.features.get(name, default)


class Ranker(Protocol):
    """ランカープロトコル."""
    
    def rank(
        self, 
        items: List[RankingItem], 
        context: Dict[str, Any]
    ) -> List[RankingItem]:
        """
        アイテムをランキング.
        
        Args:
            items: ランキング対象アイテム
            context: コンテキスト情報
        
        Returns:
            ランキング済みアイテム（降順）
        """
        ...

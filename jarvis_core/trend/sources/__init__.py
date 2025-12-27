"""
JARVIS Trend Sources Base

トレンドソースの基底クラス
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TrendItem:
    """トレンドアイテム."""
    id: str
    title: str
    source: str
    url: str
    published_date: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    bibtex: Optional[str] = None
    pdf_url: Optional[str] = None
    is_oa: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrendSource(ABC):
    """トレンドソース基底クラス."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """ソース名."""
        pass
    
    @abstractmethod
    def fetch(
        self,
        queries: List[str],
        max_results: int = 50
    ) -> List[TrendItem]:
        """
        トレンドを取得.
        
        Args:
            queries: 検索クエリリスト
            max_results: 最大取得数
        
        Returns:
            TrendItemリスト
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """利用可能かどうか."""
        pass

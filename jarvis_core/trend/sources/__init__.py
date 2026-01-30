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
    published_date: str | None = None
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    bibtex: str | None = None
    pdf_url: str | None = None
    is_oa: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class TrendSource(ABC):
    """トレンドソース基底クラス."""

    @property
    @abstractmethod
    def name(self) -> str:
        """ソース名."""
        pass

    @abstractmethod
    def fetch(self, queries: list[str], max_results: int = 50) -> list[TrendItem]:
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
"""
JARVIS arXiv Trend Source

arXiv / alphaXiv からのトレンド収集
"""

from __future__ import annotations

import logging

from . import TrendItem, TrendSource

logger = logging.getLogger(__name__)


class ArxivSource(TrendSource):
    """arXivトレンドソース."""

    @property
    def name(self) -> str:
        return "arxiv"

    def fetch(
        self,
        queries: list[str],
        max_results: int = 50
    ) -> list[TrendItem]:
        """
        arXivからトレンドを取得.
        
        絶対ルール:
        - arXivはOAなので自動取得可
        """
        items = []

        for query in queries:
            try:
                fetched = self._search_arxiv(query, max_results // len(queries))
                items.extend(fetched)
            except Exception as e:
                logger.error(f"arXiv search failed for '{query}': {e}")

        return items

    def _search_arxiv(self, query: str, max_results: int) -> list[TrendItem]:
        """arXiv APIで検索."""
        # プレースホルダー（実際はarxiv-pythonまたはAPIを使用）
        logger.info(f"arXiv search: {query}, max={max_results}")

        # モック結果
        return [
            TrendItem(
                id=f"arxiv:2401.{i:05d}",
                title=f"[Mock] arXiv paper about {query}",
                source="arxiv",
                url=f"https://arxiv.org/abs/2401.{i:05d}",
                is_oa=True,  # arXivは常にOA
                abstract=f"This paper discusses {query}...",
            )
            for i in range(min(3, max_results))
        ]

    def is_available(self) -> bool:
        """利用可能かどうか."""
        return True

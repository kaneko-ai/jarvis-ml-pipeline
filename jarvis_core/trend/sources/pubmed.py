"""
JARVIS PubMed Trend Source

PubMed からのトレンド収集（Cell/Nature/Science含む）
"""

from __future__ import annotations

import logging
from typing import List

from . import TrendSource, TrendItem

logger = logging.getLogger(__name__)


class PubMedSource(TrendSource):
    """PubMedトレンドソース."""
    
    @property
    def name(self) -> str:
        return "pubmed"
    
    def fetch(
        self,
        queries: List[str],
        max_results: int = 50
    ) -> List[TrendItem]:
        """
        PubMedからトレンドを取得.
        
        絶対ルール:
        - PDF自動取得はPMC OAのみ
        - 有料購読のVPN経由自動取得は禁止
        - メタデータ + 要旨 + BibTeXまでは可
        """
        items = []
        
        for query in queries:
            try:
                fetched = self._search_pubmed(query, max_results // len(queries))
                items.extend(fetched)
            except Exception as e:
                logger.error(f"PubMed search failed for '{query}': {e}")
        
        return items
    
    def _search_pubmed(self, query: str, max_results: int) -> List[TrendItem]:
        """PubMed E-utilitiesで検索."""
        # プレースホルダー（既存のjarvis_tools/pubmed/を使用可能）
        logger.info(f"PubMed search: {query}, max={max_results}")
        
        # モック結果
        return [
            TrendItem(
                id=f"pmid:{38000000 + i}",
                title=f"[Mock] PubMed paper about {query}",
                source="pubmed",
                url=f"https://pubmed.ncbi.nlm.nih.gov/{38000000 + i}/",
                is_oa=False,  # OA判定は別途必要
                abstract=f"This study investigates {query}...",
            )
            for i in range(min(3, max_results))
        ]
    
    def is_available(self) -> bool:
        """利用可能かどうか."""
        return True

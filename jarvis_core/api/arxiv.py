"""
JARVIS arXiv API Client

実API接続: arXiv API
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)


ARXIV_API_URL = "http://export.arxiv.org/api/query"


@dataclass
class ArxivPaper:
    """arXiv論文."""
    arxiv_id: str
    title: str
    authors: list[str]
    year: int
    abstract: str
    categories: list[str]
    pdf_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": f"arXiv:{self.arxiv_id}",
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "source": "arxiv",
            "url": f"https://arxiv.org/abs/{self.arxiv_id}",
            "pdf_url": self.pdf_url,
            "categories": self.categories,
        }


class ArxivClient:
    """arXiv API Client.
    
    arXiv API を使用して論文を検索・取得
    """

    def __init__(self, rate_limit: float = 3.0):  # 3 seconds between requests
        """初期化."""
        self.rate_limit = rate_limit
        self._last_request = 0.0

    def _rate_limit_wait(self) -> None:
        """レート制限."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def search(
        self,
        query: str,
        max_results: int = 10,
        categories: list[str] | None = None,
    ) -> list[ArxivPaper]:
        """論文を検索.
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            categories: カテゴリフィルタ（例: cs.LG, q-bio.BM）
        
        Returns:
            論文リスト
        """
        self._rate_limit_wait()

        # クエリ構築
        search_query = f"all:{query}"
        if categories:
            cat_query = " OR ".join([f"cat:{c}" for c in categories])
            search_query = f"({search_query}) AND ({cat_query})"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            response = requests.get(ARXIV_API_URL, params=params, timeout=30)
            response.raise_for_status()

            papers = self._parse_arxiv_xml(response.text)
            logger.info(f"arXiv search: found {len(papers)} papers for '{query}'")
            return papers

        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []

    def _parse_arxiv_xml(self, xml_text: str) -> list[ArxivPaper]:
        """arXiv Atom XMLをパース."""
        papers = []

        # エントリを分割
        entries = re.findall(r'<entry>(.*?)</entry>', xml_text, re.DOTALL)

        for entry in entries:
            # arXiv ID
            id_match = re.search(r'<id>http://arxiv.org/abs/(.+?)</id>', entry)
            arxiv_id = id_match.group(1) if id_match else ""

            # タイトル
            title_match = re.search(r'<title>(.+?)</title>', entry, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            title = re.sub(r'\s+', ' ', title)

            # 著者
            author_matches = re.findall(r'<name>(.+?)</name>', entry)
            authors = author_matches[:5]  # 最大5名

            # Abstract
            summary_match = re.search(r'<summary>(.+?)</summary>', entry, re.DOTALL)
            abstract = summary_match.group(1).strip() if summary_match else ""
            abstract = re.sub(r'\s+', ' ', abstract)

            # 公開日
            published_match = re.search(r'<published>(\d{4})-', entry)
            year = int(published_match.group(1)) if published_match else 2024

            # カテゴリ
            category_matches = re.findall(r'<category[^>]*term="([^"]+)"', entry)

            # PDF URL
            pdf_match = re.search(r'<link[^>]*title="pdf"[^>]*href="([^"]+)"', entry)
            pdf_url = pdf_match.group(1) if pdf_match else ""

            if arxiv_id and title:
                papers.append(ArxivPaper(
                    arxiv_id=arxiv_id,
                    title=title,
                    authors=authors,
                    year=year,
                    abstract=abstract,
                    categories=category_matches,
                    pdf_url=pdf_url,
                ))

        return papers

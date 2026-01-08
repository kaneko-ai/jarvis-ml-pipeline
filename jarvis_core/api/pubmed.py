"""
JARVIS PubMed API Client

実API接続: PubMed E-Utilities
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)


PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


@dataclass
class PubMedPaper:
    """PubMed論文."""
    pmid: str
    title: str
    authors: list[str]
    year: int
    abstract: str
    journal: str
    doi: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": f"PMID:{self.pmid}",
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "source": "pubmed",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}",
            "journal": self.journal,
            "doi": self.doi,
        }


class PubMedClient:
    """PubMed API Client.
    
    E-Utilities API を使用して論文を検索・取得
    """

    def __init__(
        self,
        email: str | None = None,
        api_key: str | None = None,
        rate_limit: float = 0.34,  # 3 requests/sec
    ):
        """初期化."""
        self.email = email or "jarvis@example.com"
        self.api_key = api_key
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
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[str]:
        """論文を検索してPMIDリストを返す.
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            date_from: 開始日（YYYY/MM/DD）
            date_to: 終了日（YYYY/MM/DD）
        
        Returns:
            PMIDリスト
        """
        self._rate_limit_wait()

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        if date_from:
            params["mindate"] = date_from
        if date_to:
            params["maxdate"] = date_to
            params["datetype"] = "pdat"

        try:
            response = requests.get(PUBMED_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            logger.info(f"PubMed search: found {len(pmids)} papers for '{query}'")
            return pmids

        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    def fetch(self, pmids: list[str]) -> list[PubMedPaper]:
        """PMIDから論文詳細を取得.
        
        Args:
            pmids: PMIDリスト
        
        Returns:
            論文リスト
        """
        if not pmids:
            return []

        self._rate_limit_wait()

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = requests.get(PUBMED_FETCH_URL, params=params, timeout=30)
            response.raise_for_status()

            # XMLパース（簡易版）
            papers = self._parse_pubmed_xml(response.text)
            logger.info(f"Fetched {len(papers)} papers from PubMed")
            return papers

        except Exception as e:
            logger.error(f"PubMed fetch failed: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> list[PubMedPaper]:
        """PubMed XMLをパース（簡易版）."""
        import re

        papers = []

        # PMIDを抽出
        pmid_matches = re.findall(r'<PMID[^>]*>(\d+)</PMID>', xml_text)

        # タイトルを抽出
        title_matches = re.findall(r'<ArticleTitle>(.+?)</ArticleTitle>', xml_text, re.DOTALL)

        # Abstractを抽出
        abstract_matches = re.findall(r'<AbstractText[^>]*>(.+?)</AbstractText>', xml_text, re.DOTALL)

        # 年を抽出
        year_matches = re.findall(r'<PubDate>.*?<Year>(\d{4})</Year>.*?</PubDate>', xml_text, re.DOTALL)

        for i, pmid in enumerate(pmid_matches):
            title = title_matches[i] if i < len(title_matches) else "Unknown"
            abstract = abstract_matches[i] if i < len(abstract_matches) else ""
            year = int(year_matches[i]) if i < len(year_matches) else 2024

            # HTMLタグを削除
            title = re.sub(r'<[^>]+>', '', title)
            abstract = re.sub(r'<[^>]+>', '', abstract)

            papers.append(PubMedPaper(
                pmid=pmid,
                title=title.strip(),
                authors=["Author"],  # 簡易版では省略
                year=year,
                abstract=abstract.strip(),
                journal="",
            ))

        return papers

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[PubMedPaper]:
        """検索と取得を一括実行."""
        pmids = self.search(query, max_results)
        return self.fetch(pmids)

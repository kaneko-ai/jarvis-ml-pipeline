"""PubMed/PMC Collector (AG-10).

PubMed/PMC OA論文収集。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request


PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PMC_OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"


@dataclass
class CollectedPaper:
    """収集された論文."""

    pmid: str
    pmcid: str = ""
    title: str = ""
    abstract: str = ""
    year: int = 0
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    doi: str = ""
    is_oa: bool = False
    pdf_url: str = ""
    xml_url: str = ""

    def to_dict(self) -> dict:
        return {
            "paper_id": self.pmcid or f"PMID:{self.pmid}",
            "pmid": self.pmid,
            "pmcid": self.pmcid,
            "title": self.title,
            "abstract": self.abstract,
            "year": self.year,
            "authors": self.authors,
            "journal": self.journal,
            "doi": self.doi,
            "is_oa": self.is_oa,
            "source": "pubmed",
        }


@dataclass
class CollectionResult:
    """収集結果."""

    papers: List[CollectedPaper] = field(default_factory=list)
    total_found: int = 0
    collected: int = 0
    query: str = ""
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "papers": [p.to_dict() for p in self.papers],
            "total_found": self.total_found,
            "collected": self.collected,
            "query": self.query,
            "warnings": self.warnings,
        }


class PubMedCollector:
    """PubMed論文収集器.

    E-utilities APIを使用してPubMed/PMCから論文を収集。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        email: str = "jarvis@example.com",
        delay: float = 0.34,  # NCBI制限: 3リクエスト/秒
    ):
        self.api_key = api_key
        self.email = email
        self.delay = delay
        self._last_request = 0.0

    def search(
        self,
        query: str,
        max_results: int = 100,
        oa_only: bool = False,
    ) -> CollectionResult:
        """PubMed検索.

        Args:
            query: 検索クエリ
            max_results: 最大結果数
            oa_only: OAのみ

        Returns:
            CollectionResult
        """
        result = CollectionResult(query=query)

        # OAフィルタ追加
        search_query = query
        if oa_only:
            search_query = f"({query}) AND (free full text[filter])"

        # Step 1: esearch でPMID取得
        try:
            pmids = self._esearch(search_query, max_results)
            result.total_found = len(pmids)
        except Exception as e:
            result.warnings.append(
                {
                    "code": "SEARCH_ERROR",
                    "message": str(e),
                }
            )
            return result

        if not pmids:
            return result

        # Step 2: efetch でメタデータ取得
        try:
            papers = self._efetch(pmids)
            result.papers = papers
            result.collected = len(papers)
        except Exception as e:
            result.warnings.append(
                {
                    "code": "FETCH_ERROR",
                    "message": str(e),
                }
            )

        return result

    def _esearch(self, query: str, retmax: int) -> List[str]:
        """E-Search APIでPMIDリストを取得."""
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "retmode": "json",
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        self._rate_limit()

        url = f"{PUBMED_ESEARCH}?{urlencode(params)}"
        req = Request(url, headers={"User-Agent": "JARVIS-ML-Pipeline/1.0"})

        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        result = data.get("esearchresult", {})
        pmids = result.get("idlist", [])

        return pmids

    def _efetch(self, pmids: List[str]) -> List[CollectedPaper]:
        """E-Fetch APIで詳細情報を取得."""
        papers = []

        # バッチ処理（最大200件ずつ）
        for i in range(0, len(pmids), 200):
            batch = pmids[i : i + 200]

            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "xml",
                "email": self.email,
            }

            if self.api_key:
                params["api_key"] = self.api_key

            self._rate_limit()

            url = f"{PUBMED_EFETCH}?{urlencode(params)}"
            req = Request(url, headers={"User-Agent": "JARVIS-ML-Pipeline/1.0"})

            try:
                with urlopen(req, timeout=60) as response:
                    xml_content = response.read().decode()

                batch_papers = self._parse_pubmed_xml(xml_content)
                papers.extend(batch_papers)
            except Exception:
                # バッチ失敗時はスキップ
                continue

        return papers

    def _parse_pubmed_xml(self, xml_content: str) -> List[CollectedPaper]:
        """PubMed XMLをパース."""
        import re

        papers = []

        # 簡易XMLパース（完全なXMLパーサーを使うべきだが、軽量化のため）
        article_pattern = r"<PubmedArticle>(.*?)</PubmedArticle>"

        for match in re.finditer(article_pattern, xml_content, re.DOTALL):
            article_xml = match.group(1)

            # PMID
            pmid_match = re.search(r"<PMID[^>]*>(\d+)</PMID>", article_xml)
            pmid = pmid_match.group(1) if pmid_match else ""

            # Title
            title_match = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", article_xml, re.DOTALL)
            title = title_match.group(1) if title_match else ""
            title = re.sub(r"<[^>]+>", "", title)  # HTMLタグ除去

            # Abstract
            abstract_match = re.search(
                r"<AbstractText[^>]*>(.*?)</AbstractText>", article_xml, re.DOTALL
            )
            abstract = abstract_match.group(1) if abstract_match else ""
            abstract = re.sub(r"<[^>]+>", "", abstract)

            # Year
            year_match = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", article_xml, re.DOTALL)
            year = int(year_match.group(1)) if year_match else 0

            # Journal
            journal_match = re.search(r"<Title>(.*?)</Title>", article_xml)
            journal = journal_match.group(1) if journal_match else ""

            # DOI
            doi_match = re.search(r'<ArticleId IdType="doi">(.*?)</ArticleId>', article_xml)
            doi = doi_match.group(1) if doi_match else ""

            # PMC ID
            pmcid_match = re.search(r'<ArticleId IdType="pmc">(PMC\d+)</ArticleId>', article_xml)
            pmcid = pmcid_match.group(1) if pmcid_match else ""

            papers.append(
                CollectedPaper(
                    pmid=pmid,
                    pmcid=pmcid,
                    title=title,
                    abstract=abstract,
                    year=year,
                    journal=journal,
                    doi=doi,
                    is_oa=bool(pmcid),
                )
            )

        return papers

    def _rate_limit(self):
        """レート制限."""
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.time()


def collect_papers(
    query: str,
    max_results: int = 100,
    oa_only: bool = False,
) -> CollectionResult:
    """便利関数: 論文を収集."""
    collector = PubMedCollector()
    return collector.search(query, max_results, oa_only)

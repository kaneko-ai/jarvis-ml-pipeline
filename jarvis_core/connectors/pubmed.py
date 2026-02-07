"""
JARVIS PubMed Connector - E-utilities経由の検索・取得

Task 4: retrieval.search_bm25 実API化
- search(query, retmax, filters) -> list[pmid]
- fetch_details(pmids) -> list[PaperDoc]
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any
from defusedxml import ElementTree as ET


@dataclass
class PaperDoc:
    """
    論文ドキュメント（正規化済み）.

    Attributes:
        pmid: PubMed ID
        pmcid: PMC ID（OAの場合）
        title: タイトル
        abstract: アブストラクト
        sections: セクション辞書（title -> text）
        references: 参照文献リスト
        identifiers: 識別子辞書（doi, pmid, pmcid等）
        chunks: チャンク辞書（chunk_id -> text）
        char_spans: チャンクのspan情報（chunk_id -> (start, end)）
    """

    pmid: str
    title: str
    abstract: str = ""
    pmcid: str | None = None
    doi: str | None = None
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    pub_date: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    references: list[dict[str, Any]] = field(default_factory=list)
    identifiers: dict[str, str] = field(default_factory=dict)
    chunks: dict[str, str] = field(default_factory=dict)
    char_spans: dict[str, tuple] = field(default_factory=dict)
    is_oa: bool = False
    fulltext_source: str | None = None

    def to_paper(self):
        """jarvis_core.contracts.types.Paper に変換."""
        from jarvis_core.contracts.types import Paper

        return Paper(
            doc_id=f"pmid:{self.pmid}",
            title=self.title,
            abstract=self.abstract,
            authors=self.authors,
            year=int(self.pub_date[:4]) if self.pub_date and self.pub_date[:4].isdigit() else None,
            journal=self.journal,
            doi=self.doi,
            pmid=self.pmid,
            sections=self.sections,
            chunks=self.chunks,
        )

    def generate_chunks(self, chunk_size: int = 500) -> None:
        """セクションからチャンクを生成."""
        chunk_id = 0

        # タイトルチャンク
        if self.title:
            cid = f"chunk_{chunk_id}"
            self.chunks[cid] = self.title
            self.char_spans[cid] = (0, len(self.title))
            chunk_id += 1

        # アブストラクトチャンク
        if self.abstract:
            for i in range(0, len(self.abstract), chunk_size):
                cid = f"chunk_{chunk_id}"
                text = self.abstract[i : i + chunk_size]
                self.chunks[cid] = text
                self.char_spans[cid] = (i, i + len(text))
                chunk_id += 1

        # セクションチャンク
        for section_name, section_text in self.sections.items():
            for i in range(0, len(section_text), chunk_size):
                cid = f"chunk_{chunk_id}"
                text = section_text[i : i + chunk_size]
                self.chunks[cid] = text
                self.char_spans[cid] = (i, i + len(text))
                chunk_id += 1


class PubMedConnector:
    """
    PubMed E-utilities Connector.

    実APIを使用してPubMed検索・詳細取得を実行。
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: str | None = None, email: str | None = None):
        """
        初期化.

        Args:
            api_key: NCBI API key（レート制限緩和用）
            email: E-utilities利用規約に基づくメールアドレス
        """
        self.api_key = api_key or os.environ.get("NCBI_API_KEY")
        self.email = email or os.environ.get("NCBI_EMAIL", "jarvis@example.com")
        self._last_request_time = 0
        self._request_interval = 0.34 if self.api_key else 1.0  # API keyありで3req/s

    def _rate_limit(self):
        """レート制限."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_interval:
            time.sleep(self._request_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, url: str, timeout: int = 30) -> bytes:
        """HTTP GETリクエスト."""
        self._rate_limit()

        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-ResearchOS/1.0"})

        with urllib.request.urlopen(
            req, timeout=timeout
        ) as response:  # nosec B310: trusted NCBI endpoint
            return response.read()

    def search(
        self, query: str, retmax: int = 20, filters: dict[str, str] | None = None
    ) -> list[str]:
        """
        PubMed検索.

        Args:
            query: 検索クエリ
            retmax: 最大取得件数
            filters: 追加フィルタ（例: {"datetype": "pdat", "mindate": "2020"}）

        Returns:
            PMIDリスト
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "retmode": "json",
            "sort": "relevance",
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        if filters:
            params.update(filters)

        url = f"{self.BASE_URL}/esearch.fcgi?{urllib.parse.urlencode(params)}"

        try:
            data = self._make_request(url)
            result = json.loads(data.decode("utf-8"))
            return result.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def fetch_details(self, pmids: list[str]) -> list[PaperDoc]:
        """
        論文詳細を取得.

        Args:
            pmids: PMIDリスト

        Returns:
            PaperDocリスト
        """
        if not pmids:
            return []

        # efetchでXML取得（より詳細な情報）
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/efetch.fcgi?{urllib.parse.urlencode(params)}"

        try:
            data = self._make_request(url)
            return self._parse_pubmed_xml(data)
        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []

    def _parse_pubmed_xml(self, xml_data: bytes) -> list[PaperDoc]:
        """PubMed XMLをパース."""
        papers = []

        try:
            root = ET.fromstring(xml_data)

            for article in root.findall(".//PubmedArticle"):
                try:
                    paper = self._parse_article(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    print(f"Article parse error: {e}")
                    continue
        except ET.ParseError as e:
            print(f"XML parse error: {e}")

        return papers

    def _parse_article(self, article: ET.Element) -> PaperDoc | None:
        """個別記事をパース."""
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None

        # PMID
        pmid_elem = medline.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""
        if not pmid:
            return None

        # タイトル
        title_elem = medline.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""

        # アブストラクト
        abstract_parts = []
        for abs_elem in medline.findall(".//AbstractText"):
            label = abs_elem.get("Label", "")
            text = abs_elem.text or ""
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

        # 著者
        authors = []
        for author in medline.findall(".//Author"):
            lastname = author.find("LastName")
            initials = author.find("Initials")
            if lastname is not None:
                name = lastname.text or ""
                if initials is not None:
                    name += f" {initials.text}"
                authors.append(name)

        # ジャーナル
        journal_elem = medline.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # 日付
        pub_date = ""
        year_elem = medline.find(".//PubDate/Year")
        if year_elem is not None:
            pub_date = year_elem.text or ""

        # DOI
        doi = None
        for eid in article.findall(".//ArticleId"):
            if eid.get("IdType") == "doi":
                doi = eid.text
                break

        # PMCID
        pmcid = None
        for eid in article.findall(".//ArticleId"):
            if eid.get("IdType") == "pmc":
                pmcid = eid.text
                break

        paper = PaperDoc(
            pmid=pmid,
            title=title,
            abstract=abstract,
            pmcid=pmcid,
            doi=doi,
            authors=authors,
            journal=journal,
            pub_date=pub_date,
            identifiers={"pmid": pmid, "doi": doi or "", "pmcid": pmcid or ""},
            is_oa=pmcid is not None,
        )

        # チャンク生成
        paper.generate_chunks()

        return paper

    def search_and_fetch(
        self, query: str, max_results: int = 20, filters: dict[str, str] | None = None
    ) -> list[PaperDoc]:
        """
        検索と詳細取得を一括実行.

        Args:
            query: 検索クエリ
            max_results: 最大取得件数
            filters: 追加フィルタ

        Returns:
            PaperDocリスト
        """
        pmids = self.search(query, max_results, filters)
        return self.fetch_details(pmids)


# 便利関数
_connector: PubMedConnector | None = None


def get_pubmed_connector() -> PubMedConnector:
    """グローバルコネクタを取得."""
    global _connector
    if _connector is None:
        _connector = PubMedConnector()
    return _connector


def search_pubmed(
    query: str, max_results: int = 20, filters: dict[str, str] | None = None
) -> list[str]:
    """PubMed検索（便利関数）."""
    return get_pubmed_connector().search(query, max_results, filters)


def fetch_paper_details(pmids: list[str]) -> list[PaperDoc]:
    """論文詳細取得（便利関数）."""
    return get_pubmed_connector().fetch_details(pmids)

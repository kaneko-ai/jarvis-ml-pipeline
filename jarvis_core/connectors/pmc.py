"""
JARVIS PMC Connector - PMC Central経由のフルテキスト取得

Task 4: OA論文のフルテキスト取得
- resolve_pmcid(pmid) -> pmcid | None
- fetch_fulltext(pmcid) -> structured_text
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
class FulltextResult:
    """
    フルテキスト取得結果.

    Attributes:
        pmcid: PMC ID
        title: タイトル
        abstract: アブストラクト
        sections: セクション辞書（タイトル -> テキスト）
        references: 参照文献リスト
        success: 取得成功フラグ
        source: 取得元（pmc_xml, pmc_html, etc）
        error: エラーメッセージ
    """

    pmcid: str
    title: str = ""
    abstract: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    references: list[dict[str, Any]] = field(default_factory=list)
    success: bool = True
    source: str = "pmc_xml"
    error: str | None = None


class PMCConnector:
    """
    PMC Connector - フルテキスト取得.

    PMC OA Serviceを使用してOpen Access論文のフルテキストを取得。
    """

    # PMC OA Service
    PMC_OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
    # PMC ID Converter
    PMC_IDCONV_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    # PMC efetch (XML)
    PMC_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self, api_key: str | None = None, email: str | None = None):
        """初期化."""
        self.api_key = api_key or os.environ.get("NCBI_API_KEY")
        self.email = email or os.environ.get("NCBI_EMAIL", "jarvis@example.com")
        self._last_request_time = 0
        self._request_interval = 0.34 if self.api_key else 1.0

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

        try:
            with urllib.request.urlopen(
                req, timeout=timeout
            ) as response:  # nosec B310: trusted NCBI endpoint
                return response.read()
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}")

    def resolve_pmcid(self, pmid: str) -> str | None:
        """
        PMIDからPMCIDを解決.

        Args:
            pmid: PubMed ID

        Returns:
            PMCID（例: PMC1234567）またはNone
        """
        params = {"ids": pmid, "idtype": "pmid", "format": "json", "email": self.email}

        if self.api_key:
            params["tool"] = "jarvis"

        url = f"{self.PMC_IDCONV_URL}?{urllib.parse.urlencode(params)}"

        try:
            data = self._make_request(url)
            result = json.loads(data.decode("utf-8"))

            records = result.get("records", [])
            if records and len(records) > 0:
                pmcid = records[0].get("pmcid")
                if pmcid:
                    return pmcid
        except Exception as e:
            print(f"PMCID resolve error for {pmid}: {e}")

        return None

    def fetch_fulltext(self, pmcid: str) -> FulltextResult:
        """
        PMCからフルテキストを取得.

        Args:
            pmcid: PMC ID（例: PMC1234567）

        Returns:
            FulltextResult
        """
        # PMCIDの正規化
        if not pmcid.startswith("PMC"):
            pmcid = f"PMC{pmcid}"

        # efetchでXML取得を試行
        result = self._fetch_pmc_xml(pmcid)

        if not result.success:
            # フォールバック: OA Serviceを試行
            result = self._fetch_via_oa_service(pmcid)

        return result

    def _fetch_pmc_xml(self, pmcid: str) -> FulltextResult:
        """PMC efetchでXMLを取得."""
        # PMCIDから数字部分を抽出
        pmc_num = pmcid.replace("PMC", "")

        params = {"db": "pmc", "id": pmc_num, "retmode": "xml", "email": self.email}

        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.PMC_EFETCH_URL}?{urllib.parse.urlencode(params)}"

        try:
            data = self._make_request(url)
            return self._parse_pmc_xml(pmcid, data)
        except Exception as e:
            return FulltextResult(pmcid=pmcid, success=False, error=f"PMC XML fetch failed: {e}")

    def _parse_pmc_xml(self, pmcid: str, xml_data: bytes) -> FulltextResult:
        """PMC XMLをパース."""
        try:
            root = ET.fromstring(xml_data)

            # タイトル
            title = ""
            title_elem = root.find(".//article-title")
            if title_elem is not None:
                title = "".join(title_elem.itertext())

            # アブストラクト
            abstract = ""
            abs_elem = root.find(".//abstract")
            if abs_elem is not None:
                abstract = " ".join("".join(p.itertext()) for p in abs_elem.findall(".//p"))

            # セクション
            sections: dict[str, str] = {}
            for sec in root.findall(".//body//sec"):
                sec_title_elem = sec.find("title")
                sec_title = sec_title_elem.text if sec_title_elem is not None else "Section"

                paragraphs = []
                for p in sec.findall(".//p"):
                    text = "".join(p.itertext())
                    if text.strip():
                        paragraphs.append(text.strip())

                if paragraphs:
                    sections[sec_title] = " ".join(paragraphs)

            # 参照文献
            references: list[dict[str, Any]] = []
            for ref in root.findall(".//ref"):
                ref_id = ref.get("id", "")
                citation = ref.find(".//mixed-citation")
                if citation is None:
                    citation = ref.find(".//element-citation")

                if citation is not None:
                    ref_text = "".join(citation.itertext())
                    references.append({"ref_id": ref_id, "raw": ref_text.strip()[:500]})

            return FulltextResult(
                pmcid=pmcid,
                title=title,
                abstract=abstract,
                sections=sections,
                references=references,
                success=True,
                source="pmc_xml",
            )

        except ET.ParseError as e:
            return FulltextResult(pmcid=pmcid, success=False, error=f"XML parse error: {e}")

    def _fetch_via_oa_service(self, pmcid: str) -> FulltextResult:
        """OA Serviceでフルテキストを取得（フォールバック）."""
        params = {"id": pmcid, "format": "tgz"}

        url = f"{self.PMC_OA_URL}?{urllib.parse.urlencode(params)}"

        try:
            data = self._make_request(url)
            # OA Serviceの応答をパース（XMLレスポンス）
            root = ET.fromstring(data)

            # エラーチェック
            error = root.find(".//error")
            if error is not None:
                return FulltextResult(
                    pmcid=pmcid,
                    success=False,
                    source="oa_service",
                    error=error.text or "OA not available",
                )

            # 成功の場合はダウンロードURLを取得
            link = root.find(".//link")
            if link is not None:
                href = link.get("href")
                return FulltextResult(
                    pmcid=pmcid,
                    success=True,
                    source="oa_service",
                    sections={"download_url": href or ""},
                )

            return FulltextResult(
                pmcid=pmcid, success=False, source="oa_service", error="No download link found"
            )

        except Exception as e:
            return FulltextResult(pmcid=pmcid, success=False, source="oa_service", error=str(e))

    def fetch_fulltext_for_pmid(self, pmid: str) -> FulltextResult:
        """
        PMIDからフルテキストを取得.

        PMCIDに解決してからフルテキストを取得。

        Args:
            pmid: PubMed ID

        Returns:
            FulltextResult
        """
        pmcid = self.resolve_pmcid(pmid)

        if not pmcid:
            return FulltextResult(pmcid="", success=False, error=f"No PMCID found for PMID {pmid}")

        return self.fetch_fulltext(pmcid)


# 便利関数
_connector: PMCConnector | None = None


def get_pmc_connector() -> PMCConnector:
    """グローバルコネクタを取得."""
    global _connector
    if _connector is None:
        _connector = PMCConnector()
    return _connector


def resolve_pmcid(pmid: str) -> str | None:
    """PMCIDを解決（便利関数）."""
    return get_pmc_connector().resolve_pmcid(pmid)


def fetch_fulltext(pmcid: str) -> FulltextResult:
    """フルテキスト取得（便利関数）."""
    return get_pmc_connector().fetch_fulltext(pmcid)

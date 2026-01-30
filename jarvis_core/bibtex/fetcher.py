"""
JARVIS BibTeX Fetcher

全件自動取得: arXiv / DOI / Crossref / PubMed
保存: data/papers/bibtex/master.bib
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BibTeXEntry:
    """BibTeXエントリ."""

    key: str
    entry_type: str  # article, inproceedings, etc.
    title: str
    authors: list[str]
    year: str
    raw: str  # 生のBibTeX文字列
    source: str  # arxiv, crossref, pubmed
    doi: str | None = None
    url: str | None = None
    journal: str | None = None
    abstract: str | None = None


class BibTeXFetcher:
    """BibTeX取得器.

    絶対ルール:
    - 全件自動取得可（メタデータのみ）
    - PDF取得は別ルール（OAのみ）
    """

    def __init__(self, master_bib_path: str = "data/papers/bibtex/master.bib"):
        """
        初期化.

        Args:
            master_bib_path: master.bibのパス
        """
        self.master_bib_path = Path(master_bib_path)
        self.master_bib_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, BibTeXEntry] = {}
        self._load_master()

    def _load_master(self) -> None:
        """master.bibを読み込み."""
        if not self.master_bib_path.exists():
            return

        with open(self.master_bib_path, encoding="utf-8") as f:
            content = f.read()

        # 簡易パース（実際はbibtexparserを使用）
        logger.info(f"Loaded master.bib: {len(content)} bytes")

    def fetch_from_arxiv(self, arxiv_id: str) -> BibTeXEntry | None:
        """arXivからBibTeXを取得."""
        logger.info(f"Fetching BibTeX from arXiv: {arxiv_id}")

        # プレースホルダー（実際はarXiv APIを使用）
        raw = f"""@article{{{arxiv_id.replace(':', '_')},
  title = {{Mock arXiv paper}},
  author = {{Author, First}},
  year = {{2024}},
  eprint = {{{arxiv_id}}},
  archivePrefix = {{arXiv}},
}}"""

        return BibTeXEntry(
            key=arxiv_id.replace(":", "_"),
            entry_type="article",
            title="Mock arXiv paper",
            authors=["Author, First"],
            year="2024",
            raw=raw,
            source="arxiv",
        )

    def fetch_from_doi(self, doi: str) -> BibTeXEntry | None:
        """DOIからBibTeXを取得（Crossref経由）."""
        logger.info(f"Fetching BibTeX from DOI: {doi}")

        # プレースホルダー（実際はCrossref APIを使用）
        key = re.sub(r"[^a-zA-Z0-9]", "_", doi)[:30]
        raw = f"""@article{{{key},
  title = {{Mock DOI paper}},
  author = {{Author, First}},
  year = {{2024}},
  doi = {{{doi}}},
}}"""

        return BibTeXEntry(
            key=key,
            entry_type="article",
            title="Mock DOI paper",
            authors=["Author, First"],
            year="2024",
            raw=raw,
            source="crossref",
            doi=doi,
        )

    def fetch_from_pubmed(self, pmid: str) -> BibTeXEntry | None:
        """PubMedからBibTeXを取得."""
        logger.info(f"Fetching BibTeX from PubMed: {pmid}")

        # プレースホルダー（実際はPubMed E-utilitiesを使用）
        raw = f"""@article{{pmid{pmid},
  title = {{Mock PubMed paper}},
  author = {{Author, First}},
  year = {{2024}},
  pmid = {{{pmid}}},
}}"""

        return BibTeXEntry(
            key=f"pmid{pmid}",
            entry_type="article",
            title="Mock PubMed paper",
            authors=["Author, First"],
            year="2024",
            raw=raw,
            source="pubmed",
        )

    def add_to_master(self, entry: BibTeXEntry) -> None:
        """master.bibに追加."""
        if entry.key in self._entries:
            logger.debug(f"Entry already exists: {entry.key}")
            return

        self._entries[entry.key] = entry

        with open(self.master_bib_path, "a", encoding="utf-8") as f:
            f.write(f"\n{entry.raw}\n")

        logger.info(f"Added to master.bib: {entry.key}")

    def get_entry(self, key: str) -> BibTeXEntry | None:
        """エントリを取得."""
        return self._entries.get(key)

    def list_entries(self) -> list[str]:
        """全エントリキーを取得."""
        return list(self._entries.keys())

"""Paper deduplication engine for research-grade ingestion."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

from jarvis_core.metadata.normalize import normalize_title


@dataclass
class DedupResult:
    canonical_papers: List[Dict[str, Any]]
    merged_count: int


class DedupEngine:
    """Deduplicate papers by DOI, PMID, normalized title, or similarity."""

    def __init__(self, similarity_threshold: float = 0.92) -> None:
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, papers: List[Dict[str, Any]]) -> DedupResult:
        canonical: List[Dict[str, Any]] = []
        merged_count = 0
        seen_doi: Dict[str, Dict[str, Any]] = {}
        seen_pmid: Dict[str, Dict[str, Any]] = {}
        seen_title: Dict[str, Dict[str, Any]] = {}

        for paper in papers:
            paper = dict(paper)
            paper_id = paper.get("paper_id") or ""
            paper["merged_from"] = [paper_id] if paper_id else []
            canonical_id = self._canonical_id(paper)
            paper["canonical_paper_id"] = canonical_id

            match = self._match_existing(paper, canonical, seen_doi, seen_pmid, seen_title)
            if match:
                match["merged_from"].extend(paper["merged_from"])
                merged_count += 1
                continue

            canonical.append(paper)
            if paper.get("doi"):
                seen_doi[paper["doi"]] = paper
            if paper.get("pmid"):
                seen_pmid[paper["pmid"]] = paper
            if paper.get("title"):
                seen_title[normalize_title(paper["title"])] = paper

        return DedupResult(canonical_papers=canonical, merged_count=merged_count)

    def _canonical_id(self, paper: Dict[str, Any]) -> str:
        if paper.get("doi"):
            return f"doi:{paper['doi']}"
        if paper.get("pmid"):
            return f"pmid:{paper['pmid']}"
        if paper.get("pmcid"):
            return f"pmc:{paper['pmcid']}"
        title = normalize_title(paper.get("title") or "")
        hashed = hashlib.sha1(title.encode("utf-8")).hexdigest()
        return f"title:{hashed[:12]}"

    def _match_existing(
        self,
        paper: Dict[str, Any],
        canonical: List[Dict[str, Any]],
        seen_doi: Dict[str, Dict[str, Any]],
        seen_pmid: Dict[str, Dict[str, Any]],
        seen_title: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any] | None:
        doi = paper.get("doi")
        if doi and doi in seen_doi:
            return seen_doi[doi]
        pmid = paper.get("pmid")
        if pmid and pmid in seen_pmid:
            return seen_pmid[pmid]
        title = paper.get("title")
        if title:
            norm_title = normalize_title(title)
            if norm_title in seen_title:
                return seen_title[norm_title]

        text = " ".join([paper.get("title") or "", paper.get("abstract") or ""]).strip().lower()
        if not text:
            return None
        for existing in canonical:
            existing_text = " ".join(
                [existing.get("title") or "", existing.get("abstract") or ""]
            ).strip().lower()
            if not existing_text:
                continue
            if SequenceMatcher(None, text, existing_text).ratio() >= self.similarity_threshold:
                return existing
        return None

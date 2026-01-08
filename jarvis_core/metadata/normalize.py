"""Metadata normalization and audit utilities."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any


def normalize_doi(doi: str) -> str:
    return doi.strip().lower()


def normalize_title(title: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in title).split())


def normalize_record(paper: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(paper)
    normalized["title"] = (paper.get("title") or "").strip()
    normalized["abstract"] = (paper.get("abstract") or "").strip()
    normalized["journal"] = (paper.get("journal") or "").strip()
    normalized["doi"] = normalize_doi(paper.get("doi") or "")
    normalized["pmid"] = (paper.get("pmid") or "").strip()
    normalized["pmcid"] = (paper.get("pmcid") or "").strip()
    return normalized


def audit_records(papers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    current_year = datetime.utcnow().year
    normalized = [normalize_record(p) for p in papers]

    doi_titles: dict[str, set] = {}
    for paper in normalized:
        doi = paper.get("doi")
        if doi:
            doi_titles.setdefault(doi, set()).add(normalize_title(paper.get("title") or ""))

    for paper in normalized:
        flags: list[str] = []
        if not paper.get("doi"):
            flags.append("missing_doi")
        if not paper.get("pmid"):
            flags.append("missing_pmid")
        if not paper.get("pmcid"):
            flags.append("missing_pmcid")
        year = int(paper.get("year") or 0)
        if year <= 0 or year > current_year:
            flags.append("year_out_of_range")
        if not paper.get("journal"):
            flags.append("missing_journal")
        if not paper.get("title"):
            flags.append("missing_title")
        if not paper.get("abstract"):
            flags.append("missing_abstract")
        if not paper.get("pdf_url"):
            flags.append("missing_pdf_url")
        if not paper.get("fulltext_url"):
            flags.append("missing_fulltext_url")

        doi = paper.get("doi")
        if doi and len(doi_titles.get(doi, set())) > 1:
            flags.append("doi_title_conflict")

        paper["audit_flags"] = flags
        paper["audit_score"] = max(0, 100 - 10 * len(flags))

    summary = _build_summary(normalized)
    return normalized, summary


def _build_summary(papers: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(papers) or 1
    missing_counts = Counter()
    conflict_count = 0
    for paper in papers:
        flags = paper.get("audit_flags") or []
        for flag in flags:
            if flag == "doi_title_conflict":
                conflict_count += 1
            if flag.startswith("missing_"):
                missing_counts[flag] += 1

    missing_rates = {flag: count / total for flag, count in missing_counts.items()}
    return {
        "total_papers": len(papers),
        "missing_rates": missing_rates,
        "conflict_count": conflict_count,
    }

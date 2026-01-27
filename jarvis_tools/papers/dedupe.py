"""Duplicate Detector.

Per RP-115, detects and deduplicates papers.
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from typing import List, Optional, Dict, Set, Tuple


@dataclass
class DedupeResult:
    """Result of deduplication."""

    canonical_id: str
    duplicate_ids: List[str]
    reason: str


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    if not title:
        return ""

    # Lowercase
    title = title.lower()

    # Remove punctuation
    title = re.sub(r"[^\w\s]", "", title)

    # Normalize whitespace
    title = " ".join(title.split())

    return title


def title_similarity(title1: str, title2: str) -> float:
    """Calculate title similarity (Jaccard on words)."""
    if not title1 or not title2:
        return 0.0

    words1 = set(normalize_title(title1).split())
    words2 = set(normalize_title(title2).split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def canonical_paper_id(
    pmid: Optional[str] = None,
    pmcid: Optional[str] = None,
    doi: Optional[str] = None,
    title: Optional[str] = None,
) -> str:
    """Generate canonical paper ID with priority.

    Priority: PMID > PMCID > DOI > title hash
    """
    if pmid:
        return f"pmid:{pmid.strip()}"
    if pmcid:
        return f"pmcid:{pmcid.strip()}"
    if doi:
        # Normalize DOI
        doi = doi.strip().lower()
        if doi.startswith("https://doi.org/"):
            doi = doi[16:]
        elif doi.startswith("http://doi.org/"):
            doi = doi[15:]
        elif doi.startswith("doi:"):
            doi = doi[4:]
        return f"doi:{doi}"
    if title:
        normalized = normalize_title(title)
        title_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"title:{title_hash}"

    return "unknown"


@dataclass
class PaperIdentifiers:
    """Paper identifiers for deduplication."""

    paper_id: str  # Internal ID
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None
    title: Optional[str] = None


def find_duplicates(
    papers: List[PaperIdentifiers],
    title_threshold: float = 0.9,
) -> List[DedupeResult]:
    """Find duplicate papers.

    Args:
        papers: List of paper identifiers.
        title_threshold: Minimum title similarity for match.

    Returns:
        List of DedupeResult showing duplicates.
    """
    results: List[DedupeResult] = []

    # Group by canonical ID
    canonical_groups: Dict[str, List[PaperIdentifiers]] = {}

    for paper in papers:
        canonical = canonical_paper_id(
            pmid=paper.pmid,
            pmcid=paper.pmcid,
            doi=paper.doi,
            title=paper.title,
        )

        if canonical not in canonical_groups:
            canonical_groups[canonical] = []
        canonical_groups[canonical].append(paper)

    # Find duplicates within groups
    for canonical, group in canonical_groups.items():
        if len(group) > 1:
            # First one is canonical, rest are duplicates
            canonical_paper = group[0]
            duplicates = [p.paper_id for p in group[1:]]

            results.append(
                DedupeResult(
                    canonical_id=canonical_paper.paper_id,
                    duplicate_ids=duplicates,
                    reason=f"Same canonical ID: {canonical}",
                )
            )

    # Cross-check titles for papers without strong IDs
    title_only = [p for p in papers if not p.pmid and not p.pmcid and not p.doi]

    seen_titles: Dict[str, str] = {}  # normalized_title -> paper_id

    for paper in title_only:
        if not paper.title:
            continue

        normalized = normalize_title(paper.title)

        # Check against seen titles
        for seen_norm, seen_id in seen_titles.items():
            sim = title_similarity(paper.title, seen_norm)
            if sim >= title_threshold:
                # Add to existing result or create new
                found = False
                for result in results:
                    if result.canonical_id == seen_id:
                        if paper.paper_id not in result.duplicate_ids:
                            result.duplicate_ids.append(paper.paper_id)
                        found = True
                        break

                if not found:
                    results.append(
                        DedupeResult(
                            canonical_id=seen_id,
                            duplicate_ids=[paper.paper_id],
                            reason=f"Title similarity: {sim:.2f}",
                        )
                    )
                break
        else:
            seen_titles[normalized] = paper.paper_id

    return results


def dedupe_papers(
    papers: List[PaperIdentifiers],
    title_threshold: float = 0.9,
) -> Tuple[List[PaperIdentifiers], List[DedupeResult]]:
    """Deduplicate papers, returning unique papers and duplicate info.

    Returns:
        (unique_papers, duplicate_results)
    """
    duplicates = find_duplicates(papers, title_threshold)

    # Build set of duplicate IDs
    duplicate_ids: Set[str] = set()
    for result in duplicates:
        duplicate_ids.update(result.duplicate_ids)

    # Filter to unique
    unique = [p for p in papers if p.paper_id not in duplicate_ids]

    return unique, duplicates

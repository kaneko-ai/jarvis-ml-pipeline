"""Reference structure for academic citation management.

This module provides:
- Reference: A bibliographic reference (PDF/URL/local)
- extract_references(): Extract references from citations

Per RP14, this enables generating academic reference lists
(Vancouver/APA) from evidence citations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .agents import Citation
    from .evidence import EvidenceStore


@dataclass
class Reference:
    """A bibliographic reference.

    Represents a single source (PDF/URL/local) that may be cited
    multiple times at different pages/locations.

    Attributes:
        id: Unique reference ID (e.g., "R1").
        source_type: Type of source ("pdf", "url", "local").
        locator: Base locator (without page/chunk info).
        title: Title of the source (if known).
        authors: List of author names (if known).
        year: Publication year (if known).
        pages: List of page numbers cited.
        accessed_at: When the source was accessed.
        chunk_ids: List of chunk_ids that map to this reference.
    """

    id: str
    source_type: Literal["pdf", "url", "local"]
    locator: str
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    pages: list[int] = field(default_factory=list)
    accessed_at: datetime = field(default_factory=datetime.now)
    chunk_ids: list[str] = field(default_factory=list)
    # RP22: Extended metadata from resolvers
    doi: str | None = None
    pmid: str | None = None
    journal: str | None = None

    def get_pages_display(self) -> str:
        """Get pages as display string (e.g., 'pp. 1-3, 5')."""
        if not self.pages:
            return ""

        pages = sorted(set(self.pages))
        if len(pages) == 1:
            return f"p. {pages[0]}"

        # Group consecutive pages
        ranges: list[str] = []
        start = pages[0]
        end = pages[0]

        for p in pages[1:]:
            if p == end + 1:
                end = p
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = p

        # Add last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return f"pp. {', '.join(ranges)}"

    def get_display_locator(self) -> str:
        """Get human-readable locator."""
        if self.source_type == "pdf":
            # Extract filename from path
            match = re.search(r"pdf:(.+?)(?:#|$)", self.locator)
            if match:
                path = match.group(1)
                return Path(path).name
        elif self.source_type == "url":
            match = re.search(r"url:(.+?)(?:#|$)", self.locator)
            if match:
                return match.group(1)
        return self.locator

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source_type": self.source_type,
            "locator": self.locator,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "pages": self.pages,
            "accessed_at": self.accessed_at.isoformat(),
            "chunk_ids": self.chunk_ids,
            # RP22 fields
            "doi": self.doi,
            "pmid": self.pmid,
            "journal": self.journal,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Reference:
        """Create from dictionary."""
        accessed_at = data.get("accessed_at")
        if isinstance(accessed_at, str):
            accessed_at = datetime.fromisoformat(accessed_at)
        elif accessed_at is None:
            accessed_at = datetime.now()

        return cls(
            id=data["id"],
            source_type=data["source_type"],
            locator=data["locator"],
            title=data.get("title"),
            authors=data.get("authors", []),
            year=data.get("year"),
            pages=data.get("pages", []),
            accessed_at=accessed_at,
            chunk_ids=data.get("chunk_ids", []),
            doi=data.get("doi"),
            pmid=data.get("pmid"),
            journal=data.get("journal"),
        )


def _parse_locator(locator: str) -> tuple[str, str | None, int | None]:
    """Parse locator into base, type, and page number.

    Args:
        locator: Full locator (e.g., "pdf:path#page:3#chunk:0")

    Returns:
        Tuple of (base_locator, source_type, page_number).
    """
    source_type: str | None = None
    page: int | None = None

    # Detect source type
    if locator.startswith("pdf:"):
        source_type = "pdf"
    elif locator.startswith("url:"):
        source_type = "url"
    elif locator.startswith("local:"):
        source_type = "local"
    else:
        source_type = "local"

    # Extract page number
    page_match = re.search(r"#page:(\d+)", locator)
    if page_match:
        page = int(page_match.group(1))

    # Get base locator (remove page and chunk info)
    base = re.sub(r"#page:\d+", "", locator)
    base = re.sub(r"#chunk:\d+", "", base)

    return base, source_type, page


def extract_references(
    citations: list[Citation],
    store: EvidenceStore | None = None,
) -> list[Reference]:
    """Extract and normalize references from citations.

    Multiple citations from the same source are consolidated
    into a single Reference.

    Args:
        citations: List of citations to process.
        store: Optional EvidenceStore for additional metadata.

    Returns:
        List of normalized Reference objects.
    """
    # Group citations by base locator
    ref_map: dict[str, Reference] = {}
    ref_counter = 1

    for citation in citations:
        locator = citation.locator
        base, source_type, page = _parse_locator(locator)

        if base not in ref_map:
            ref_map[base] = Reference(
                id=f"R{ref_counter}",
                source_type=source_type or "local",
                locator=base,
                accessed_at=datetime.now(),
            )
            ref_counter += 1

        ref = ref_map[base]

        # Add page if present
        if page is not None and page not in ref.pages:
            ref.pages.append(page)

        # Add chunk_id
        if citation.chunk_id not in ref.chunk_ids:
            ref.chunk_ids.append(citation.chunk_id)

    # Sort references by ID
    refs = sorted(ref_map.values(), key=lambda r: r.id)

    # Sort pages within each reference
    for ref in refs:
        ref.pages.sort()

    return refs


def resolve_references(
    refs: list[Reference],
    use_crossref: bool = True,
    use_pubmed: bool = True,
    timeout: float = 5.0,
) -> list[Reference]:
    """Resolve and enrich references with metadata from external APIs.

    Per RP22, this queries CrossRef and PubMed to fill in
    DOI, PMID, title, authors, year, and journal.

    Args:
        refs: List of references to resolve.
        use_crossref: Whether to use CrossRef API.
        use_pubmed: Whether to use PubMed API.
        timeout: Request timeout per API call.

    Returns:
        The same list of references, mutated with additional metadata.
    """
    from .resolvers.crossref_resolver import resolve_crossref
    from .resolvers.pubmed_resolver import resolve_pubmed

    for ref in refs:
        # Try CrossRef first (more general)
        if use_crossref:
            try:
                resolve_crossref(ref, timeout=timeout)
            except Exception:
                pass  # Don't fail on resolver errors

        # Try PubMed for biomedical content
        if use_pubmed and ref.title:
            try:
                resolve_pubmed(ref, timeout=timeout)
            except Exception:
                pass  # Don't fail on resolver errors

    return refs

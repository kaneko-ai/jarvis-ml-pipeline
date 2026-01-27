"""Paper data models.

Per RP-04/RP-05, defines data structures for paper processing with provenance.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class Locator:
    """Source locator for citations.

    Per JARVIS_MASTER.md Section 5.4.2, locators must be machine-traceable.
    Format: "pmid:12345678 page:3 span:120-450"
    """

    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None
    page: Optional[int] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    url: Optional[str] = None

    def to_string(self) -> str:
        """Convert to locator string."""
        parts = []
        if self.pmid:
            parts.append(f"pmid:{self.pmid}")
        if self.pmcid:
            parts.append(f"pmcid:{self.pmcid}")
        if self.doi:
            parts.append(f"doi:{self.doi}")
        if self.page is not None:
            parts.append(f"page:{self.page}")
        elif self.page_start is not None:
            if self.page_end and self.page_end != self.page_start:
                parts.append(f"page:{self.page_start}-{self.page_end}")
            else:
                parts.append(f"page:{self.page_start}")
        if self.span_start is not None:
            parts.append(f"span:{self.span_start}-{self.span_end or self.span_start}")
        return " ".join(parts)

    @classmethod
    def from_string(cls, s: str) -> "Locator":
        """Parse locator string."""
        loc = cls()
        for part in s.split():
            if ":" in part:
                key, val = part.split(":", 1)
                if key == "pmid":
                    loc.pmid = val
                elif key == "pmcid":
                    loc.pmcid = val
                elif key == "doi":
                    loc.doi = val
                elif key == "page":
                    if "-" in val:
                        start, end = val.split("-")
                        loc.page_start = int(start)
                        loc.page_end = int(end)
                    else:
                        loc.page = int(val)
                elif key == "span":
                    if "-" in val:
                        start, end = val.split("-")
                        loc.span_start = int(start)
                        loc.span_end = int(end)
        return loc


@dataclass
class PaperRecord:
    """Paper metadata record."""

    paper_id: str  # Unique ID (prefer PMID)
    title: str
    authors: List[str] = field(default_factory=list)
    pubdate: Optional[str] = None
    journal: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    pdf_path: Optional[str] = None
    source: str = "pubmed"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChunkRecord:
    """Chunk record with provenance.

    Per RP-05, chunks must have:
    - chunk_id (stable)
    - paper_id
    - locator with page/span
    """

    chunk_id: str
    paper_id: str
    source: str  # e.g., "pubmed"
    locator: str  # Locator string
    page_start: int
    page_end: int
    text: str
    span_start: Optional[int] = None
    span_end: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def create(
        cls,
        paper_id: str,
        text: str,
        page: int,
        span_start: int = 0,
        span_end: Optional[int] = None,
        source: str = "pubmed",
        pmid: Optional[str] = None,
    ) -> "ChunkRecord":
        """Create a chunk with stable ID.

        chunk_id = sha256(pmid + page + span)
        """
        span_end = span_end or (span_start + len(text))

        # Stable chunk ID
        id_content = f"{paper_id}:{page}:{span_start}-{span_end}"
        chunk_id = hashlib.sha256(id_content.encode()).hexdigest()[:16]

        # Build locator
        loc = Locator(
            pmid=pmid,
            page=page,
            span_start=span_start,
            span_end=span_end,
        )

        return cls(
            chunk_id=chunk_id,
            paper_id=paper_id,
            source=source,
            locator=loc.to_string(),
            page_start=page,
            page_end=page,
            text=text,
            span_start=span_start,
            span_end=span_end,
        )

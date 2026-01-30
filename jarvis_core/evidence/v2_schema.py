"""Evidence models for systematic reviews (Phase 21).

Defines the contract for claims, evidence, and supporting spans.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class SupportSpan(BaseModel):
    """Specific location of evidence within a source."""

    chunk_id: str
    char_range: Tuple[int, int]  # (start, end)
    text_snippet: str
    page: Optional[int] = None


class Evidence(BaseModel):
    """A piece of supporting evidence for a claim."""

    source_url: str
    source_title: str
    spans: List[SupportSpan] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1.0)


class Claim(BaseModel):
    """An individual assertion with supporting evidence."""

    statement: str
    evidence: List[Evidence] = Field(default_factory=list)
    importance: float = Field(default=1.0, ge=0, le=1.0)

    def has_evidence(self) -> bool:
        """Check if the claim has any supporting evidence."""
        return len(self.evidence) > 0 and any(len(e.spans) > 0 for e in self.evidence)


class EvidenceReport(BaseModel):
    """The collection of claims and evidence forming a report."""

    title: str
    claims: List[Claim] = Field(default_factory=list)
    summary: str
    schema_version: str = "v2"

    def validate_audit(self) -> bool:
        """Verify that every claim has at least one piece of evidence."""
        return all(c.has_evidence() for c in self.claims)
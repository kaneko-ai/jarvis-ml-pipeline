"""Structured result types for Evidence QA.

This module provides structured result types that enable:
- Post-processing (citation lists, reference management)
- External tool integration (PPT/Word/Obsidian/NotebookLM)
- Audit and reproduction (which chunks were used)

Per RP12, this maintains backward compatibility while adding
structured data access. RP13 adds claim-level tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from .agents import Citation

if TYPE_CHECKING:
    pass


@dataclass
class EvidenceQAResult:
    """Structured result from Evidence QA pipeline.

    This contains all information needed for audit, reproduction,
    and external tool integration.

    Attributes:
        answer: The final answer text.
        status: Quality status ("success", "partial", "fail").
        citations: List of citations used in the answer.
        inputs: List of input paths/URLs that were ingested.
        chunks_used: List of chunk_ids from citations.
        query: The original query.
        claims: Optional ClaimSet with claim-level citations (RP13).
        meta: Additional metadata (provider, k, timestamp, etc).
    """

    answer: str
    status: Literal["success", "partial", "fail"]
    citations: list[Citation]
    inputs: list[str]
    query: str
    chunks_used: list[str] = field(default_factory=list)
    claims: Any = None  # ClaimSet, but avoiding import for initialization
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        """Extract chunk_ids from citations."""
        if not self.chunks_used and self.citations:
            self.chunks_used = [c.chunk_id for c in self.citations]

        # Add timestamp if not present
        if "timestamp" not in self.meta:
            self.meta["timestamp"] = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "answer": self.answer,
            "status": self.status,
            "query": self.query,
            "inputs": self.inputs,
            "chunks_used": self.chunks_used,
            "citations": [
                {
                    "chunk_id": c.chunk_id,
                    "source": c.source,
                    "locator": c.locator,
                    "quote": c.quote,
                }
                for c in self.citations
            ],
            "meta": self.meta,
        }

        # Add claims if present
        if self.claims is not None:
            result["claims"] = (
                self.claims.to_dict() if hasattr(self.claims, "to_dict") else self.claims
            )

        return result

    @classmethod
    def from_dict(cls, data: dict) -> EvidenceQAResult:
        """Create from dictionary."""
        from .claim import ClaimSet

        citations = [
            Citation(
                chunk_id=c["chunk_id"],
                source=c["source"],
                locator=c["locator"],
                quote=c["quote"],
            )
            for c in data.get("citations", [])
        ]

        claims = None
        if "claims" in data:
            claims = ClaimSet.from_dict(data["claims"])

        return cls(
            answer=data["answer"],
            status=data["status"],
            citations=citations,
            inputs=data.get("inputs", []),
            query=data.get("query", ""),
            chunks_used=data.get("chunks_used", []),
            claims=claims,
            meta=data.get("meta", {}),
        )

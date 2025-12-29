"""Schema definitions for retrieval chunks and provenance."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: str) -> str:
    import hashlib

    return hashlib.sha1(value.encode("utf-8")).hexdigest()


@dataclass
class Provenance:
    run_id: Optional[str] = None
    pmid: Optional[str] = None
    doi: Optional[str] = None
    section: Optional[str] = None
    locator: Optional[str] = None
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "run_id": self.run_id,
            "pmid": self.pmid,
            "doi": self.doi,
            "section": self.section,
            "locator": self.locator,
            "file_path": self.file_path,
        }


@dataclass
class ChunkMeta:
    year: Optional[int] = None
    journal: Optional[str] = None
    tier: Optional[str] = None
    score: Optional[float] = None
    oa: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    lang: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "year": self.year,
            "journal": self.journal,
            "tier": self.tier,
            "score": self.score,
            "oa": self.oa,
            "topics": list(self.topics),
            "lang": self.lang,
        }


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    source_type: str
    title: str
    text: str
    provenance: Provenance
    meta: ChunkMeta
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "title": self.title,
            "text": self.text,
            "provenance": self.provenance.to_dict(),
            "meta": self.meta.to_dict(),
            "updated_at": self.updated_at,
        }


@dataclass
class SearchResult:
    chunk: Chunk
    score: float
    snippet: str
    jump_link: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.chunk.doc_id,
            "chunk_id": self.chunk.chunk_id,
            "title": self.chunk.title,
            "score": self.score,
            "snippet": self.snippet,
            "provenance": self.chunk.provenance.to_dict(),
            "meta": self.chunk.meta.to_dict(),
            "jump_link": self.jump_link,
        }

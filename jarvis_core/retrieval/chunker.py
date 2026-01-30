"""Deterministic chunker for retrieval indexing."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from jarvis_core.retrieval.schema import Chunk, ChunkMeta, Provenance, stable_hash, utc_now_iso


@dataclass
class ChunkRule:
    max_chars: int = 1200
    overlap_chars: int = 120


class Chunker:
    def __init__(self, rule: ChunkRule | None = None):
        self.rule = rule or ChunkRule()

    def _split_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        clean = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
        buffer = ""
        for paragraph in paragraphs:
            if not buffer:
                buffer = paragraph
                continue
            if len(buffer) + len(paragraph) + 2 <= self.rule.max_chars:
                buffer = f"{buffer}\n\n{paragraph}"
            else:
                chunks.append(buffer)
                buffer = paragraph
        if buffer:
            chunks.append(buffer)
        return self._apply_overlap(chunks)

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        if not chunks or self.rule.overlap_chars <= 0:
            return chunks
        overlapped: list[str] = []
        prev_tail = ""
        for chunk in chunks:
            if prev_tail:
                combined = f"{prev_tail}{chunk}"
                overlapped.append(combined)
            else:
                overlapped.append(chunk)
            prev_tail = chunk[-self.rule.overlap_chars :]
        return overlapped

    def create_chunks(
        self,
        *,
        doc_id: str,
        title: str,
        text: str,
        source_type: str,
        provenance: Provenance,
        meta: ChunkMeta | None = None,
        updated_at: str | None = None,
    ) -> Iterable[Chunk]:
        if not provenance or not provenance.file_path and not provenance.run_id:
            return []
        meta = meta or ChunkMeta()
        updated_at = updated_at or utc_now_iso()
        segments = self._split_text(text)
        chunks: list[Chunk] = []
        for index, segment in enumerate(segments):
            locator = f"chunk={index}"
            stable_seed = f"{doc_id}|{index}|{segment}"
            chunk_id = stable_hash(stable_seed)
            provenance_copy = Provenance(
                run_id=provenance.run_id,
                pmid=provenance.pmid,
                doi=provenance.doi,
                section=provenance.section,
                locator=provenance.locator or locator,
                file_path=provenance.file_path,
            )
            chunks.append(
                Chunk(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    source_type=source_type,
                    title=title,
                    text=segment,
                    provenance=provenance_copy,
                    meta=meta,
                    updated_at=updated_at,
                )
            )
        return chunks

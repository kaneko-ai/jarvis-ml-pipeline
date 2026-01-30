"""Hybrid search (vector + keyword) with reranking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from jarvis_core.retrieval.bm25_store import BM25Store
from jarvis_core.retrieval.embeddings import EmbeddingProvider, HashEmbeddingProvider
from jarvis_core.retrieval.filters import apply_filters
from jarvis_core.retrieval.schema import Chunk, ChunkMeta, Provenance, SearchResult
from jarvis_core.retrieval.vector_store import VectorStore


@dataclass
class HybridSearchResult:
    took_ms: int
    total_candidates: int
    results: list[SearchResult]

    def to_dict(self) -> dict:
        return {
            "took_ms": self.took_ms,
            "total_candidates": self.total_candidates,
            "results": [result.to_dict() for result in self.results],
        }


class HybridSearchEngine:
    def __init__(
        self,
        index_dir: Path | str = Path("data/index/v2"),
        embedding_provider: EmbeddingProvider | None = None,
    ):
        self.index_dir = Path(index_dir)
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self.vector_store = VectorStore.load(self.index_dir / "vector.faiss")
        self.bm25_store = BM25Store(self.index_dir / "bm25.sqlite")
        self.chunks_path = self.index_dir / "chunks.jsonl"
        self.chunk_map = self._load_chunks()

    def _load_chunks(self) -> dict[str, Chunk]:
        if not self.chunks_path.exists():
            return {}
        chunk_map: dict[str, Chunk] = {}
        with open(self.chunks_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                provenance_payload = payload.get("provenance", {})
                meta_payload = payload.get("meta", {})
                chunk = Chunk(
                    doc_id=payload.get("doc_id"),
                    chunk_id=payload.get("chunk_id"),
                    source_type=payload.get("source_type"),
                    title=payload.get("title"),
                    text=payload.get("text"),
                    provenance=Provenance(**provenance_payload),
                    meta=ChunkMeta(**meta_payload),
                    updated_at=payload.get("updated_at"),
                )
                chunk_map[chunk.chunk_id] = chunk
        return chunk_map

    def _normalize_scores(self, scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}
        values = np.array(list(scores.values()))
        max_val = float(values.max()) if values.size else 0.0
        min_val = float(values.min()) if values.size else 0.0
        if max_val == min_val:
            return dict.fromkeys(scores, 1.0)
        return {key: (score - min_val) / (max_val - min_val) for key, score in scores.items()}

    def search(
        self, query: str, filters: dict | None = None, top_k: int = 20, mode: str = "hybrid"
    ) -> HybridSearchResult:
        import time

        start_time = time.time()
        if not self.chunk_map:
            return HybridSearchResult(took_ms=0, total_candidates=0, results=[])
        filters = filters or {}
        candidate_count = max(top_k * 10, 200)
        bm25_scores: dict[str, float] = {}
        vector_scores: dict[str, float] = {}
        if mode in {"hybrid", "keyword"}:
            bm25_scores = {
                chunk_id: score
                for chunk_id, score in self.bm25_store.search(query, candidate_count)
            }
        if mode in {"hybrid", "vector"}:
            embedding = self.embedding_provider.embed([query])
            query_vector = embedding.vectors[0]
            vector_scores = {
                chunk_id: score
                for chunk_id, score in self.vector_store.search(query_vector, candidate_count)
            }

        bm25_norm = self._normalize_scores(bm25_scores)
        vector_norm = self._normalize_scores(vector_scores)
        candidates = set(bm25_scores) | set(vector_scores)
        scored = []
        for chunk_id in candidates:
            chunk = self.chunk_map.get(chunk_id)
            if not chunk:
                continue
            if not chunk.provenance or not (chunk.provenance.run_id or chunk.provenance.file_path):
                continue
            bm25_score = bm25_norm.get(chunk_id, 0.0)
            vector_score = vector_norm.get(chunk_id, 0.0)
            if mode == "keyword":
                combined = bm25_score
            elif mode == "vector":
                combined = vector_score
            else:
                combined = 0.6 * vector_score + 0.4 * bm25_score
            scored.append((chunk, combined))
        filtered_chunks = apply_filters([item[0] for item in scored], filters)
        filtered_set = {chunk.chunk_id for chunk in filtered_chunks}
        scored = [(chunk, score) for chunk, score in scored if chunk.chunk_id in filtered_set]
        scored.sort(key=lambda item: item[1], reverse=True)
        results = []
        for chunk, score in scored[:top_k]:
            snippet = chunk.text.strip().replace("\n", " ")
            if len(snippet) > 240:
                snippet = snippet[:237] + "..."
            jump_link = self._build_jump_link(chunk)
            results.append(
                SearchResult(chunk=chunk, score=score, snippet=snippet, jump_link=jump_link)
            )
        took_ms = int((time.time() - start_time) * 1000)
        return HybridSearchResult(
            took_ms=took_ms, total_candidates=len(candidates), results=results
        )

    def _build_jump_link(self, chunk: Chunk) -> dict[str, str]:
        if chunk.provenance.run_id:
            return {"type": "run", "url": f"/dashboard/run.html?id={chunk.provenance.run_id}"}
        if chunk.doc_id.startswith("kb:"):
            return {"type": "kb", "url": f"/dashboard/kb.html?id={chunk.doc_id}"}
        return {"type": "kb", "url": "/dashboard/kb.html"}

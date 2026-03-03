"""High-level paper vector store for JARVIS CLI.

Uses ChromaDB's built-in embedding (all-MiniLM-L6-v2 by default)
so callers can pass raw text instead of pre-computed embeddings.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class PaperStore:
    """High-level ChromaDB store: accepts text, returns ranked results."""

    def __init__(self, persist_dir: Optional[str] = None):
        import chromadb

        if persist_dir is None:
            persist_dir = str(
                Path.home()
                / "Documents"
                / "jarvis-work"
                / "jarvis-ml-pipeline"
                / ".chroma"
            )
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="jarvis_papers",
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Add / Upsert
    # ------------------------------------------------------------------
    def add_papers(self, papers: list[dict]) -> int:
        """Upsert papers into the store.

        Each paper dict should have at least 'title'.
        Optional keys: 'abstract', 'doi', 'pmid', 'year', 'source'.
        Returns number of papers upserted.
        """
        ids, docs, metas = [], [], []
        seen = set()
        for p in papers:
            pid = p.get("doi") or p.get("pmid") or p.get("title", "")[:60]
            if not pid:
                continue
            pid = str(pid).strip()
            if pid in seen:
                continue
            seen.add(pid)
            text = f"{p.get('title', '')} {p.get('abstract', '')}"
            if len(text.strip()) < 5:
                continue
            ids.append(pid)
            docs.append(text)
            metas.append(
                {
                    "title": str(p.get("title", ""))[:500],
                    "year": str(p.get("year", "")),
                    "source": str(p.get("source", "")),
                    "doi": str(p.get("doi", "")),
                }
            )
        if ids:
            self.collection.upsert(ids=ids, documents=docs, metadatas=metas)
        return len(ids)

    # ------------------------------------------------------------------
    # Search (text query -> ranked results)
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Semantic search by text query.

        Returns list of dicts with keys: id, score, metadata.
        Score is cosine similarity (0-1, higher = more relevant).
        """
        count = self.collection.count()
        if count == 0:
            return []
        n = min(top_k, count)
        results = self.collection.query(query_texts=[query], n_results=n)
        output = []
        for i, doc_id in enumerate(results["ids"][0]):
            dist = results["distances"][0][i] if results["distances"] else 0
            score = round(1.0 - dist, 4)
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            output.append({"id": doc_id, "score": score, "metadata": meta})
        return output

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def count(self) -> int:
        """Return total number of documents in the collection."""
        return self.collection.count()

    def delete_all(self) -> None:
        """Delete all documents (for testing)."""
        self.client.delete_collection("jarvis_papers")
        self.collection = self.client.get_or_create_collection(
            name="jarvis_papers",
            metadata={"hnsw:space": "cosine"},
        )

    def add_from_json(self, json_path: str) -> int:
        """Load papers from a JSON file and upsert them.

        JSON can be a list of paper dicts, or {"papers": [...]}.
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Not found: {json_path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        papers = data if isinstance(data, list) else data.get("papers", [])
        return self.add_papers(papers)

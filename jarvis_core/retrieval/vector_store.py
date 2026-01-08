"""Vector store with simple numpy persistence."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class VectorStore:
    index_path: Path
    chunk_ids: list[str]
    vectors: np.ndarray
    model_name: str

    @classmethod
    def load(cls, index_path: Path) -> VectorStore:
        if not index_path.exists():
            return cls(index_path=index_path, chunk_ids=[], vectors=np.zeros((0, 1), dtype=np.float32), model_name="")
        data = np.load(index_path, allow_pickle=True)
        chunk_ids = data["chunk_ids"].tolist()
        vectors = data["vectors"]
        model_name = str(data["model_name"])
        return cls(index_path=index_path, chunk_ids=chunk_ids, vectors=vectors, model_name=model_name)

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            self.index_path,
            chunk_ids=np.array(self.chunk_ids, dtype=object),
            vectors=self.vectors,
            model_name=np.array(self.model_name),
        )

    def add(self, chunk_ids: Iterable[str], vectors: np.ndarray, model_name: str) -> None:
        chunk_ids = list(chunk_ids)
        if not chunk_ids:
            return
        self.model_name = model_name or self.model_name
        if self.vectors.size == 0:
            self.chunk_ids = list(chunk_ids)
            self.vectors = vectors
        else:
            self.chunk_ids.extend(chunk_ids)
            self.vectors = np.vstack([self.vectors, vectors])

    def search(self, query_vector: np.ndarray, top_k: int = 20) -> list[tuple[str, float]]:
        if self.vectors.size == 0:
            return []
        query = query_vector.reshape(1, -1)
        vectors = self.vectors
        scores = vectors @ query.T
        scores = scores.reshape(-1)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append((self.chunk_ids[idx], float(scores[idx])))
        return results

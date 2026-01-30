"""Semantic Deduplication v2.

Per RP-305, detects semantic duplicates using embeddings.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class DuplicateCluster:
    """A cluster of duplicate chunks."""

    cluster_id: str
    representative_id: str
    member_ids: list[str]
    similarity_scores: dict[str, float]


class SemanticDeduplicator:
    """Semantic deduplication using embeddings.

    Per RP-305:
    - Cosine similarity > 0.95 for duplicate detection
    - Separate logic for intra/inter-document
    - Duplicate chain visualization
    """

    def __init__(
        self,
        threshold_same_doc: float = 0.98,
        threshold_cross_doc: float = 0.95,
        embedder=None,
    ):
        self.threshold_same = threshold_same_doc
        self.threshold_cross = threshold_cross_doc
        self.embedder = embedder

    def find_duplicates(
        self,
        chunks: list[dict],
        embeddings: list[list[float]] | None = None,
    ) -> list[DuplicateCluster]:
        """Find duplicate chunks.

        Args:
            chunks: List of chunks with text, chunk_id, doc_id.
            embeddings: Optional precomputed embeddings.

        Returns:
            List of duplicate clusters.
        """
        if not chunks:
            return []

        # Generate embeddings if not provided
        if embeddings is None:
            if self.embedder:
                texts = [c.get("text", "") for c in chunks]
                embeddings = self.embedder.embed(texts)
            else:
                # Fallback: use text hash similarity
                return self._text_based_dedup(chunks)

        # Build similarity matrix
        n = len(chunks)
        clusters: list[DuplicateCluster] = []
        processed: set[int] = set()

        for i in range(n):
            if i in processed:
                continue

            cluster_members = [i]
            similarities = {chunks[i]["chunk_id"]: 1.0}

            for j in range(i + 1, n):
                if j in processed:
                    continue

                sim = self._cosine_similarity(embeddings[i], embeddings[j])

                # Use appropriate threshold
                same_doc = chunks[i].get("doc_id") == chunks[j].get("doc_id")
                threshold = self.threshold_same if same_doc else self.threshold_cross

                if sim >= threshold:
                    cluster_members.append(j)
                    similarities[chunks[j]["chunk_id"]] = sim
                    processed.add(j)

            if len(cluster_members) > 1:
                cluster_id = hashlib.md5(
                    str(cluster_members).encode(), usedforsecurity=False
                ).hexdigest()[:8]

                clusters.append(
                    DuplicateCluster(
                        cluster_id=cluster_id,
                        representative_id=chunks[i]["chunk_id"],
                        member_ids=[chunks[m]["chunk_id"] for m in cluster_members],
                        similarity_scores=similarities,
                    )
                )
                processed.add(i)

        return clusters

    def _cosine_similarity(
        self,
        a: list[float],
        b: list[float],
    ) -> float:
        """Calculate cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _text_based_dedup(
        self,
        chunks: list[dict],
    ) -> list[DuplicateCluster]:
        """Fallback text-based deduplication."""
        text_to_chunks: dict[str, list[int]] = {}

        for i, chunk in enumerate(chunks):
            # Normalize text
            text = chunk.get("text", "").lower().strip()
            text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()

            if text_hash not in text_to_chunks:
                text_to_chunks[text_hash] = []
            text_to_chunks[text_hash].append(i)

        clusters = []
        for text_hash, indices in text_to_chunks.items():
            if len(indices) > 1:
                clusters.append(
                    DuplicateCluster(
                        cluster_id=text_hash[:8],
                        representative_id=chunks[indices[0]]["chunk_id"],
                        member_ids=[chunks[i]["chunk_id"] for i in indices],
                        similarity_scores={chunks[i]["chunk_id"]: 1.0 for i in indices},
                    )
                )

        return clusters

    def deduplicate(
        self,
        chunks: list[dict],
        embeddings: list[list[float]] | None = None,
    ) -> list[dict]:
        """Remove duplicates, keeping representatives.

        Args:
            chunks: List of chunks.
            embeddings: Optional embeddings.

        Returns:
            Deduplicated chunk list.
        """
        clusters = self.find_duplicates(chunks, embeddings)

        # Get all duplicate IDs (non-representatives)
        duplicate_ids: set[str] = set()
        for cluster in clusters:
            for member_id in cluster.member_ids:
                if member_id != cluster.representative_id:
                    duplicate_ids.add(member_id)

        # Filter chunks
        return [c for c in chunks if c.get("chunk_id") not in duplicate_ids]
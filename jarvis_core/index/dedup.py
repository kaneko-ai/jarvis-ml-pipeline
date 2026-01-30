"""Dedup Filter.

Per V4.2 Sprint 2, this provides hash + near-duplicate detection.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass
class DedupResult:
    """Result of deduplication."""

    unique: list[Any]
    duplicates: list[Any]
    duplicate_pairs: list[tuple]  # (dup, original) pairs


class DedupFilter:
    """Filter for exact and near-duplicate detection."""

    def __init__(self, similarity_threshold: float = 0.9):
        self.similarity_threshold = similarity_threshold
        self.seen_hashes: set[str] = set()
        self.hash_to_item: dict[str, Any] = {}

    def compute_hash(self, item: Any) -> str:
        """Compute hash for item."""
        if isinstance(item, str):
            content = item
        elif isinstance(item, dict):
            content = item.get("text", str(item))
        else:
            content = str(item)

        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def compute_shingles(self, text: str, k: int = 3) -> set[str]:
        """Compute k-shingles for near-duplicate detection."""
        words = text.lower().split()
        if len(words) < k:
            return {text.lower()}

        shingles = set()
        for i in range(len(words) - k + 1):
            shingle = " ".join(words[i : i + k])
            shingles.add(shingle)

        return shingles

    def jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """Calculate Jaccard similarity."""
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def is_near_duplicate(self, item1: Any, item2: Any) -> bool:
        """Check if two items are near-duplicates."""
        text1 = item1 if isinstance(item1, str) else item1.get("text", str(item1))
        text2 = item2 if isinstance(item2, str) else item2.get("text", str(item2))

        shingles1 = self.compute_shingles(text1)
        shingles2 = self.compute_shingles(text2)

        similarity = self.jaccard_similarity(shingles1, shingles2)

        return similarity >= self.similarity_threshold

    def dedupe(self, items: list[Any], check_near: bool = False) -> DedupResult:
        """Deduplicate items.

        Args:
            items: Items to deduplicate.
            check_near: Whether to check for near-duplicates.

        Returns:
            DedupResult with unique and duplicate items.
        """
        unique = []
        duplicates = []
        duplicate_pairs = []

        for item in items:
            item_hash = self.compute_hash(item)

            # Exact duplicate check
            if item_hash in self.seen_hashes:
                duplicates.append(item)
                duplicate_pairs.append((item, self.hash_to_item[item_hash]))
                continue

            # Near-duplicate check (more expensive)
            is_near_dup = False
            if check_near:
                for seen_item in unique:
                    if self.is_near_duplicate(item, seen_item):
                        duplicates.append(item)
                        duplicate_pairs.append((item, seen_item))
                        is_near_dup = True
                        break

            if not is_near_dup:
                unique.append(item)
                self.seen_hashes.add(item_hash)
                self.hash_to_item[item_hash] = item

        return DedupResult(
            unique=unique,
            duplicates=duplicates,
            duplicate_pairs=duplicate_pairs,
        )

    def clear(self):
        """Clear seen hashes."""
        self.seen_hashes.clear()
        self.hash_to_item.clear()


def dedupe_chunks(
    chunks: list[Any],
    check_near: bool = False,
    threshold: float = 0.9,
) -> list[Any]:
    """Convenience function to deduplicate chunks.

    Args:
        chunks: Chunks to deduplicate.
        check_near: Whether to check near-duplicates.
        threshold: Similarity threshold for near-duplicates.

    Returns:
        List of unique chunks.
    """
    filter = DedupFilter(similarity_threshold=threshold)
    result = filter.dedupe(chunks, check_near=check_near)
    return result.unique

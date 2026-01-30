"""Route papers into conceptual topics."""

from __future__ import annotations

from collections.abc import Iterable

from .normalizer import TermNormalizer


class TopicRouter:
    """Rule-based topic classifier."""

    def __init__(self, normalizer: TermNormalizer):
        self.normalizer = normalizer

    def _match_topics(self, text: str) -> set[str]:
        normalized_text = self.normalizer.normalize_text(text)
        matches: set[str] = set()
        for canonical, synonyms in self.normalizer.synonyms.items():
            if canonical and canonical in normalized_text:
                matches.add(canonical)
                continue
            for synonym in synonyms:
                if synonym and synonym in normalized_text:
                    matches.add(canonical)
                    break
        return matches

    def classify(self, text_blocks: Iterable[str], tags: Iterable[str]) -> list[str]:
        matched: set[str] = set()
        for tag in tags:
            normalized = self.normalizer.normalize_term(tag)
            if normalized:
                matched.add(normalized)
        for block in text_blocks:
            if block:
                matched.update(self._match_topics(block))
        return sorted(matched)

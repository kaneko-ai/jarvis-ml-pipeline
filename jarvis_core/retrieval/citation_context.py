"""Citation Context Retriever.

Per RP-120, retrieves citation context for evidence validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CitationContext:
    """Context around a citation."""

    citation_marker: str  # e.g., "[1]", "(Smith, 2020)"
    context_before: str
    context_after: str
    full_context: str
    position: int


@dataclass
class CitationWindow:
    """A window of text around citations."""

    text: str
    citations: list[str]
    start_char: int
    end_char: int


# Citation patterns
CITATION_PATTERNS = [
    r"\[(\d+)\]",  # [1], [2,3]
    r"\[(\d+[-–]\d+)\]",  # [1-3]
    r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,\s*\d{4}[a-z]?)\)",  # (Smith et al., 2020)
    r"\(([A-Z][a-z]+\s+and\s+[A-Z][a-z]+,\s*\d{4})\)",  # (Smith and Jones, 2020)
]


def find_citations(text: str) -> list[tuple[str, int, int]]:
    """Find all citations in text.

    Returns:
        List of (citation_text, start, end) tuples.
    """
    citations = []

    for pattern in CITATION_PATTERNS:
        for match in re.finditer(pattern, text):
            citations.append((match.group(0), match.start(), match.end()))

    # Sort by position
    citations.sort(key=lambda x: x[1])

    return citations


def extract_citation_context(
    text: str,
    window_chars: int = 200,
) -> list[CitationContext]:
    """Extract context around each citation.

    Args:
        text: Source text.
        window_chars: Characters before/after citation.

    Returns:
        List of CitationContext objects.
    """
    citations = find_citations(text)
    contexts = []

    for citation_text, start, end in citations:
        # Get context before
        context_start = max(0, start - window_chars)
        context_before = text[context_start:start].strip()

        # Get context after
        context_end = min(len(text), end + window_chars)
        context_after = text[end:context_end].strip()

        # Full context
        full_context = text[context_start:context_end].strip()

        contexts.append(
            CitationContext(
                citation_marker=citation_text,
                context_before=context_before,
                context_after=context_after,
                full_context=full_context,
                position=start,
            )
        )

    return contexts


def extract_citation_windows(
    text: str,
    window_sentences: int = 2,
) -> list[CitationWindow]:
    """Extract windows of sentences containing citations.

    Args:
        text: Source text.
        window_sentences: Sentences before/after.

    Returns:
        List of CitationWindow objects.
    """
    # Split into sentences (simple)
    sentences = re.split(r"(?<=[.!?])\s+", text)

    windows = []
    for i, sentence in enumerate(sentences):
        # Check if sentence has citations
        citations_in_sentence = find_citations(sentence)
        if not citations_in_sentence:
            continue

        # Get window
        start_idx = max(0, i - window_sentences)
        end_idx = min(len(sentences), i + window_sentences + 1)

        window_text = " ".join(sentences[start_idx:end_idx])
        citation_markers = [c[0] for c in citations_in_sentence]

        windows.append(
            CitationWindow(
                text=window_text,
                citations=citation_markers,
                start_char=0,  # Would need char tracking
                end_char=len(window_text),
            )
        )

    return windows


class CitationContextRetriever:
    """Retriever for citation context."""

    def __init__(self, window_chars: int = 200):
        self.window_chars = window_chars
        self._index: dict = {}

    def index_document(self, doc_id: str, text: str) -> int:
        """Index citation contexts from a document."""
        contexts = extract_citation_context(text, self.window_chars)
        self._index[doc_id] = contexts
        return len(contexts)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[str, CitationContext, float]]:
        """Search citation contexts.

        Simple BM25-like scoring on context text.

        Returns:
            List of (doc_id, context, score) tuples.
        """
        query_terms = set(query.lower().split())
        results = []

        for doc_id, contexts in self._index.items():
            for context in contexts:
                # Simple term matching score
                context_terms = set(context.full_context.lower().split())
                overlap = len(query_terms & context_terms)
                if overlap > 0:
                    score = overlap / len(query_terms)
                    results.append((doc_id, context, score))

        # Sort by score
        results.sort(key=lambda x: x[2], reverse=True)

        return results[:top_k]
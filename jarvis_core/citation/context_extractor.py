"""Citation Context Extractor.

Extracts citing sentences and their context from papers.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.2.1
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CitationContext:
    """Context around a citation."""

    citing_paper_id: str
    cited_paper_id: str
    citation_text: str  # The actual citing sentence
    context_before: str = ""  # Sentences before the citation
    context_after: str = ""  # Sentences after the citation
    section: str | None = None  # Section where citation appears
    position: int = 0  # Position in document (sentence index)

    # Additional metadata
    citation_marker: str | None = None  # e.g., "[1]", "(Smith et al., 2020)"
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_full_context(self) -> str:
        """Get full context including before and after."""
        parts = []
        if self.context_before:
            parts.append(self.context_before)
        parts.append(self.citation_text)
        if self.context_after:
            parts.append(self.context_after)
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "citing_paper_id": self.citing_paper_id,
            "cited_paper_id": self.cited_paper_id,
            "citation_text": self.citation_text,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "section": self.section,
            "position": self.position,
            "citation_marker": self.citation_marker,
            "metadata": self.metadata,
        }


# Common citation patterns
CITATION_PATTERNS = [
    # Numeric: [1], [1,2], [1-3]
    re.compile(r"\[(\d+(?:[-,]\s*\d+)*)\]"),
    # Author-year: (Smith et al., 2020), (Smith 2020)
    re.compile(r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4})\)"),
    # Superscript style: text^1, text^1,2
    re.compile(r"[\d\w]\^(\d+(?:,\s*\d+)*)"),
]


class CitationExtractor:
    """Extracts citation contexts from text.

    Identifies citations in text and extracts the surrounding context
    for stance classification.

    Example:
        >>> extractor = CitationExtractor()
        >>> contexts = extractor.extract(
        ...     text="Previous work [1] showed significant results. We extend this.",
        ...     paper_id="paper_A",
        ...     reference_map={"1": "cited_paper_B"}
        ... )
        >>> print(contexts[0].cited_paper_id)
        'cited_paper_B'
    """

    def __init__(
        self,
        context_window: int = 1,  # Number of sentences before/after
        patterns: list[re.Pattern] | None = None,
    ):
        """Initialize the extractor.

        Args:
            context_window: Number of sentences to include as context
            patterns: Custom citation patterns
        """
        self._context_window = context_window
        self._patterns = patterns or CITATION_PATTERNS
        self._sentence_pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

    def extract(
        self,
        text: str,
        paper_id: str,
        reference_map: dict[str, str] | None = None,
    ) -> list[CitationContext]:
        """Extract citation contexts from text.

        Args:
            text: Full text to extract from
            paper_id: ID of the citing paper
            reference_map: Map of citation markers to cited paper IDs

        Returns:
            List of CitationContext objects
        """
        if not text:
            return []

        reference_map = reference_map or {}

        # Split into sentences
        sentences = self._split_sentences(text)

        # Find citations in each sentence
        contexts = []

        for i, sentence in enumerate(sentences):
            # Find all citations in this sentence
            citations = self._find_citations(sentence)

            for marker, citation_text in citations:
                # Resolve cited paper ID
                cited_id = self._resolve_citation(marker, reference_map)

                # Get context
                context_before = self._get_context(sentences, i, -self._context_window)
                context_after = self._get_context(sentences, i, self._context_window)

                # Detect section
                section = self._detect_section(text, i, sentences)

                contexts.append(
                    CitationContext(
                        citing_paper_id=paper_id,
                        cited_paper_id=cited_id,
                        citation_text=sentence,
                        context_before=context_before,
                        context_after=context_after,
                        section=section,
                        position=i,
                        citation_marker=marker,
                    )
                )

        return contexts

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = self._sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _find_citations(self, sentence: str) -> list[tuple[str, str]]:
        """Find citations in a sentence.

        Returns list of (marker, full_match) tuples.
        """
        citations = []

        for pattern in self._patterns:
            for match in pattern.finditer(sentence):
                marker = match.group(1) if match.lastindex else match.group(0)
                citations.append((marker, match.group(0)))

        return citations

    def _resolve_citation(
        self,
        marker: str,
        reference_map: dict[str, str],
    ) -> str:
        """Resolve citation marker to paper ID."""
        # Try exact match first
        if marker in reference_map:
            return reference_map[marker]

        # Try numeric extraction
        numbers = re.findall(r"\d+", marker)
        for num in numbers:
            if num in reference_map:
                return reference_map[num]

        # Return marker as-is if not resolved
        return f"ref:{marker}"

    def _get_context(
        self,
        sentences: list[str],
        current_idx: int,
        window: int,
    ) -> str:
        """Get context sentences."""
        if window > 0:
            # After context
            start = current_idx + 1
            end = min(current_idx + 1 + window, len(sentences))
        else:
            # Before context
            start = max(0, current_idx + window)
            end = current_idx

        context_sentences = sentences[start:end]
        return " ".join(context_sentences)

    def _detect_section(
        self,
        text: str,
        position: int,
        sentences: list[str],
    ) -> str | None:
        """Detect the section where the citation appears."""
        # Look for section headers before this position
        section_patterns = [
            (r"\b(Introduction|Background)\b", "Introduction"),
            (r"\b(Methods?|Materials?\s+and\s+Methods?)\b", "Methods"),
            (r"\b(Results?)\b", "Results"),
            (r"\b(Discussion)\b", "Discussion"),
            (r"\b(Conclusion|Summary)\b", "Conclusion"),
            (r"\b(Related\s+Work|Literature\s+Review)\b", "Related Work"),
        ]

        # Get text before current position
        text_before = " ".join(sentences[:position])

        # Find the last matching section
        last_section = None
        last_pos = -1

        for pattern, section_name in section_patterns:
            matches = list(re.finditer(pattern, text_before, re.IGNORECASE))
            if matches:
                match = matches[-1]
                if match.start() > last_pos:
                    last_pos = match.start()
                    last_section = section_name

        return last_section


def extract_citation_contexts(
    text: str,
    paper_id: str,
    reference_map: dict[str, str] | None = None,
    context_window: int = 1,
) -> list[CitationContext]:
    """Extract citation contexts from text.

    Convenience function for quick extraction.

    Args:
        text: Full text to extract from
        paper_id: ID of the citing paper
        reference_map: Map of citation markers to cited paper IDs
        context_window: Number of sentences for context

    Returns:
        List of CitationContext objects
    """
    extractor = CitationExtractor(context_window=context_window)
    return extractor.extract(text, paper_id, reference_map)

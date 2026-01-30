"""Citation Audit Module (Phase 27).

Validates that generated summaries are supported by cited evidence.
"""

from __future__ import annotations

import logging
import re
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AuditResult:
    """Result of a citation audit."""

    is_valid: bool
    score: float  # 0.0 to 1.0 (coverage of citations)
    missing_citations: List[str]  # Sentences claiming facts without citations
    hallucinated_citations: List[str]  # Citations that don't exist in source
    details: str


class CitationAuditor:
    """Audits text to ensure claims are backed by citations."""

    def __init__(self):
        # Pattern for [1], [2], [1, 2] etc.
        self.citation_pattern = re.compile(r"\[([\d,\s]+)\]")

    def audit(self, text: str, valid_citation_ids: List[str]) -> AuditResult:
        """Audit the text for valid citations."""
        sentences = self._split_sentences(text)
        missing_citations = []
        hallucinated_citations = []
        cited_sentences_count = 0
        total_sentences = len(sentences)

        valid_ids_set = set(valid_citation_ids)

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            # Extract citations in this sentence
            found_citations = []
            for match in self.citation_pattern.finditer(sent):
                # Split "1, 2" -> ["1", "2"]
                ids = [cd.strip() for cd in match.group(1).split(",")]
                found_citations.extend(ids)

            # Check validity
            if not found_citations:
                # Heuristic: If sentence looks like a claim (long enough), flag it
                if len(sent.split()) > 5:
                    missing_citations.append(sent[:50] + "...")
            else:
                cited_sentences_count += 1
                for cid in found_citations:
                    if cid not in valid_ids_set:
                        hallucinated_citations.append(cid)

        # Allow some sentences (intro/outro) to be citation-free
        # But critical claims must have them.
        # For strict audit, we might want higher threshold.
        score = cited_sentences_count / max(total_sentences, 1)

        is_valid = (
            score >= 0.5  # At least 50% of sentences have citations (relaxed for now)
            and len(hallucinated_citations) == 0  # ABSOLUTELY NO fake citations allowed
        )

        details = (
            f"Score: {score:.2f} ({cited_sentences_count}/{total_sentences}). "
            f"Missing: {len(missing_citations)}. "
            f"Hallucinated: {len(hallucinated_citations)}."
        )

        return AuditResult(
            is_valid=is_valid,
            score=score,
            missing_citations=missing_citations,
            hallucinated_citations=hallucinated_citations,
            details=details,
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Simple sentence splitter."""
        # Replace citations temporarily to avoid split on "Eq. [1]."
        # Actually simplest approach is splitting by . followed by space/newline
        # This is a heuristic approximation.
        return re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", text)
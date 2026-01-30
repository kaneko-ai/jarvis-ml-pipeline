"""Claim-Hypothesis-Experiment Chain Builder.

Per RP38, this builds research chains from claims to experiments.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def _extract_keywords(text: str) -> list[str]:
    """Extract keywords from text."""
    # Simple keyword extraction
    words = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b|\b[A-Z]{2,}\b", text)
    return list(set(words))


def _find_related_papers(
    keywords: list[str],
    vectors: list[PaperVector],
) -> list[str]:
    """Find papers related to keywords."""
    related = []
    for v in vectors:
        for kw in keywords:
            kw_lower = kw.lower()
            for c in v.concept.concepts:
                if kw_lower in c.lower():
                    related.append(v.paper_id)
                    break
    return list(set(related))[:5]


def _suggest_methods(
    keywords: list[str],
    vectors: list[PaperVector],
) -> list[str]:
    """Suggest experimental methods based on related papers."""
    all_methods = {}
    for v in vectors:
        for kw in keywords:
            kw_lower = kw.lower()
            for c in v.concept.concepts:
                if kw_lower in c.lower():
                    for method in v.method.methods:
                        all_methods[method] = all_methods.get(method, 0) + 1
                    break

    # Return top methods
    sorted_methods = sorted(all_methods.items(), key=lambda x: x[1], reverse=True)
    return [m[0] for m in sorted_methods[:3]]


def build_research_chain(
    claims: list[str],
    vectors: list[PaperVector],
) -> list[dict]:
    """Build claim-hypothesis-experiment chains.

    Args:
        claims: List of claim statements.
        vectors: PaperVectors for context.

    Returns:
        List of research chain dicts.
    """
    if not claims:
        return []

    results = []

    for claim in claims:
        keywords = _extract_keywords(claim)

        if not keywords:
            keywords = claim.split()[:3]

        related = _find_related_papers(keywords, vectors)
        methods = _suggest_methods(keywords, vectors)

        # Generate hypothesis
        if len(keywords) >= 2:
            kw1, kw2 = keywords[0], keywords[1]
            hypothesis = f"If {kw1} regulates {kw2}, then downstream signaling will change"
        elif keywords:
            hypothesis = f"{keywords[0]} may play a critical role in the observed phenomenon"
        else:
            hypothesis = "Further investigation is needed"

        # Generate experiment suggestion
        if methods:
            experiment = f"Use {methods[0]} to validate the hypothesis"
        else:
            experiment = "Western blot / qPCR to confirm expression changes"

        results.append(
            {
                "claim": claim,
                "hypothesis": hypothesis,
                "experiment": experiment,
                "supporting_papers": related,
                "suggested_methods": methods,
            }
        )

    return results
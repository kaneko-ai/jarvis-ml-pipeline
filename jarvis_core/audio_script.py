"""Podcast script generator for audio output.

This module provides:
- export_podcast_script(): Generate NotebookLM-optimized audio script

Per RP25, this creates a script structured for verbal presentation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .reference import Reference
    from .result import EvidenceQAResult


def export_podcast_script(
    result: EvidenceQAResult,
    references: list[Reference] | None = None,
    duration_target: str = "5-7 min",
) -> str:
    """Generate a podcast-style script from research results.

    The script is structured for audio presentation:
    1. Hook (30 sec) - Grab attention
    2. Summary (1 min) - Main answer
    3. Evidence walk-through - Claims with sources
    4. Key terms explained
    5. Conclusion + Next steps

    Args:
        result: The EvidenceQAResult.
        references: Optional list of references.
        duration_target: Target duration for pacing.

    Returns:
        Script text optimized for audio.
    """
    lines = [
        "=" * 60,
        "PODCAST SCRIPT",
        f"Target Duration: {duration_target}",
        "=" * 60,
        "",
        "---",
        "",
        "## SECTION 1: HOOK (30 seconds)",
        "",
        "[Grab attention with the key question]",
        "",
        f'Today we\'re exploring: "{result.query}"',
        "",
        "[Brief context on why this matters]",
        "",
        "---",
        "",
        "## SECTION 2: THE ANSWER (1 minute)",
        "",
        "[Deliver the main finding clearly]",
        "",
        result.answer,
        "",
        "---",
        "",
        "## SECTION 3: EVIDENCE WALKTHROUGH (2-3 minutes)",
        "",
        "[Go through each key finding with its source]",
        "",
    ]

    # Add claims with evidence
    if result.claims is not None:
        for i, claim in enumerate(result.claims.claims, 1):
            if not claim.valid:
                continue

            lines.append(f"### Finding {i}")
            lines.append("")
            lines.append(f'"{claim.text}"')
            lines.append("")

            # Add source attribution
            if claim.citations and references:
                for ref in references:
                    if any(cid in claim.citations for cid in ref.chunk_ids):
                        lines.append(f"[Source: {ref.get_display_locator()}]")
                        break
            lines.append("")
    else:
        lines.append("[No structured claims available - use answer text]")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## SECTION 4: KEY TERM EXPLANATIONS (30 seconds)",
            "",
            "[Define any technical terms for the listener]",
            "",
        ]
    )

    # Extract potential technical terms (simplified)
    lines.append("Key terms mentioned:")
    terms_found = []
    answer_lower = result.answer.lower()
    common_terms = ["cd73", "adenosine", "immunotherapy", "enzyme", "receptor", "pathway"]
    for term in common_terms:
        if term in answer_lower:
            terms_found.append(term)

    if terms_found:
        for term in terms_found[:3]:
            lines.append(f"- {term.upper()}: [Brief explanation]")
    else:
        lines.append("- [No complex terms detected]")

    lines.extend(
        [
            "",
            "---",
            "",
            "## SECTION 5: CONCLUSION & NEXT STEPS (30 seconds)",
            "",
            "[Wrap up and point to further reading]",
            "",
            "Key takeaway: [Summarize in one sentence]",
            "",
            "For more information, check out:",
        ]
    )

    # Add references
    if references:
        for ref in references[:3]:
            lines.append(f"- {ref.get_display_locator()}")
    else:
        lines.append("- [Sources listed in show notes]")

    lines.extend(
        [
            "",
            "---",
            "",
            "## SHOW NOTES",
            "",
            f"Query: {result.query}",
            f"Status: {result.status}",
            f"Sources: {len(references) if references else 0}",
            "",
            "=" * 60,
            "END OF SCRIPT",
            "=" * 60,
        ]
    )

    return "\n".join(lines)

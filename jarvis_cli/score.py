"""jarvis score - Calculate paper quality scores (B-3).

Uses PaperScorer to combine evidence level, citations, recency,
and other signals into an overall quality score (0-1) and grade (A-F).
"""

from __future__ import annotations

import json
from pathlib import Path


def run_score(args) -> int:
    """Score papers from a JSON file."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"  Error: File not found: {input_path}")
        return 1

    with open(input_path, encoding="utf-8") as f:
        papers = json.load(f)

    if not papers:
        print("  Error: No papers in file.")
        return 1

    print(f"  Scoring {len(papers)} papers...")
    print()

    papers = score_papers(papers)

    # Display results
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")[:60]
        score = p.get("quality_score", 0)
        grade = p.get("quality_grade", "?")
        evidence = p.get("evidence_level", "?")
        print(f"  [{i}] {title}")
        print(f"      Score: {score:.3f} ({grade}) | Evidence: {evidence}")

    print()

    # Save output
    output_path = args.output if hasattr(args, "output") and args.output else None
    if output_path is None:
        output_path = str(input_path).replace(".json", "_scored.json")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(papers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Scored results saved to: {output_path}")
    return 0


def score_papers(papers: list[dict]) -> list[dict]:
    """Add quality_score and quality_grade to each paper.

    Uses PaperScorer from jarvis_core.paper_scoring.
    Falls back to a simple calculation if the module is unavailable.
    """
    try:
        from jarvis_core.paper_scoring import PaperScorer
        scorer = PaperScorer()
    except ImportError:
        print("  Warning: PaperScorer not available. Using simple scoring.")
        scorer = None

    from datetime import datetime
    current_year = datetime.now().year

    for p in papers:
        title = p.get("title", "Untitled")
        evidence_str = p.get("evidence_level", "5")
        citation_count = p.get("citation_count", 0) or 0

        # Parse evidence level to integer (1-5)
        evidence_int = _parse_evidence_level(evidence_str)

        # Parse year
        year = p.get("year", current_year)
        if isinstance(year, str):
            try:
                year = int(year[:4]) if year else current_year
            except (ValueError, TypeError):
                year = current_year

        if scorer:
            paper_id = p.get("doi") or p.get("pmid") or title[:30]
            result = scorer.score(
                paper_id=paper_id,
                evidence_level=evidence_int,
                total_citations=citation_count,
                publication_year=year,
            )
            p["quality_score"] = round(result.overall_score, 3)
            p["quality_grade"] = result.grade
            p["quality_confidence"] = round(result.confidence, 3)
        else:
            # Simple fallback scoring
            score = _simple_score(evidence_int, citation_count, year, current_year)
            p["quality_score"] = round(score, 3)
            p["quality_grade"] = _grade_from_score(score)
            p["quality_confidence"] = 0.3

    return papers


def _parse_evidence_level(level_str: str) -> int:
    """Convert evidence level string to integer 1-5."""
    if not level_str or level_str == "unknown":
        return 5
    # Handle "1a", "1b", "2b", etc. -> take the leading digit
    for ch in str(level_str):
        if ch.isdigit():
            val = int(ch)
            if 1 <= val <= 5:
                return val
    return 5


def _simple_score(evidence: int, citations: int, year: int, current_year: int) -> float:
    """Simple fallback scoring without PaperScorer."""
    import math
    evidence_score = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}.get(evidence, 0.2)
    citation_score = min(1.0, math.log10(citations + 1) / 3) if citations > 0 else 0.3
    age = current_year - year
    recency_score = 1.0 if age <= 2 else (0.8 if age <= 5 else (0.6 if age <= 10 else 0.4))
    return evidence_score * 0.4 + citation_score * 0.3 + recency_score * 0.3


def _grade_from_score(score: float) -> str:
    """Convert score to letter grade."""
    if score >= 0.9:
        return "A"
    elif score >= 0.8:
        return "B"
    elif score >= 0.7:
        return "C"
    elif score >= 0.6:
        return "D"
    return "F"

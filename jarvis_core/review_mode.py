"""Multi-Query Review Mode for batch research.

This module provides:
- run_review_mode(): Process multiple queries with shared evidence

Per RP24, this enables "review/background investigation" workflows
where multiple questions are answered from the same source material.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Literal

from .result import EvidenceQAResult


@dataclass
class ReviewResult:
    """Result from multi-query review mode.

    Attributes:
        queries: List of queries processed.
        results: List of EvidenceQAResult for each query.
        inputs: Shared inputs (sources).
        start_time: When processing started.
        end_time: When processing ended.
    """

    queries: List[str]
    results: List[EvidenceQAResult]
    inputs: List[str]
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    def get_result_for_query(self, query: str) -> EvidenceQAResult | None:
        """Get result for a specific query."""
        for q, r in zip(self.queries, self.results):
            if q == query:
                return r
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "queries": self.queries,
            "results": [r.to_dict() for r in self.results],
            "inputs": self.inputs,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


def run_review_mode(
    queries: List[str],
    inputs: List[str],
    category: str = "generic",
) -> ReviewResult:
    """Run multi-query review mode.

    This processes multiple queries against the same sources,
    reusing the ingested evidence.

    Args:
        queries: List of questions to answer.
        inputs: List of source files/URLs (shared).
        category: Task category for routing.

    Returns:
        ReviewResult with all answers.
    """
    from .evidence_qa import run_evidence_qa_result, get_evidence_store_for_bundle

    start_time = datetime.now()
    results = []

    # Note: In MVP, we call run_evidence_qa_result for each query.
    # This re-ingests sources each time. A future optimization would
    # be to ingest once and reuse the EvidenceStore.

    for query in queries:
        result = run_evidence_qa_result(
            query=query,
            inputs=inputs,
            category=category,
        )
        results.append(result)

    end_time = datetime.now()

    return ReviewResult(
        queries=queries,
        results=results,
        inputs=inputs,
        start_time=start_time,
        end_time=end_time,
    )


def export_review_bundle(
    review: ReviewResult,
    out_dir: str,
) -> str:
    """Export review results as a bundle.

    Creates:
    - review/query_01_bundle.json
    - review/query_02_bundle.json
    - ...
    - review_index.md

    Args:
        review: The ReviewResult to export.
        out_dir: Output directory.

    Returns:
        Path to the output directory.
    """
    import json

    from .bundle import export_evidence_bundle
    from .evidence_qa import get_evidence_store_for_bundle

    out_path = Path(out_dir)
    review_dir = out_path / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    # Export each query's bundle
    for i, (query, result) in enumerate(zip(review.queries, review.results), 1):
        query_dir = review_dir / f"query_{i:02d}"
        query_dir.mkdir(exist_ok=True)

        # Export bundle.json only (simplified)
        bundle_data = {
            "query": query,
            "answer": result.answer,
            "status": result.status,
            "citations": [c.model_dump() if hasattr(c, "model_dump") else c.__dict__ for c in result.citations],
        }
        bundle_path = query_dir / "bundle.json"
        with open(bundle_path, "w", encoding="utf-8") as f:
            json.dump(bundle_data, f, indent=2, ensure_ascii=False, default=str)

    # Generate review index
    index_content = _generate_review_index(review)
    index_path = out_path / "review_index.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    return str(out_path)


def _generate_review_index(review: ReviewResult) -> str:
    """Generate the review index markdown."""
    lines = [
        "# Research Review",
        "",
        f"**Started:** {review.start_time.strftime('%Y-%m-%d %H:%M')}",
        f"**Completed:** {review.end_time.strftime('%Y-%m-%d %H:%M') if review.end_time else 'In Progress'}",
        "",
        f"**Sources:** {len(review.inputs)}",
        f"**Queries:** {len(review.queries)}",
        "",
        "---",
        "",
        "## Summary",
        "",
    ]

    for i, (query, result) in enumerate(zip(review.queries, review.results), 1):
        lines.append(f"### Query {i}: {query}")
        lines.append("")
        lines.append(f"**Status:** {result.status}")
        lines.append("")
        lines.append(f"**Answer:** {result.answer[:200]}..." if len(result.answer) > 200 else f"**Answer:** {result.answer}")
        lines.append("")
        lines.append(f"- Citations: {len(result.citations)}")
        lines.append(f"- [Details](review/query_{i:02d}/bundle.json)")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Cross-reference summary
    lines.append("## Cross-Reference Summary")
    lines.append("")

    # Collect all unique sources
    all_sources = set()
    for result in review.results:
        for citation in result.citations:
            all_sources.add(citation.source)

    lines.append(f"**Unique Sources Cited:** {len(all_sources)}")
    for source in all_sources:
        lines.append(f"- {source}")

    return "\n".join(lines)

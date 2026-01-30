"""Method Evolution Map.

Per RP44, this tracks method evolution over time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def track_method_evolution(
    vectors: list[PaperVector],
) -> list[dict]:
    """Track method evolution by year.

    Args:
        vectors: PaperVectors to analyze.

    Returns:
        List of yearly method evolution dicts.
    """
    if not vectors:
        return []

    # Group by year
    by_year = {}
    for v in vectors:
        year = v.metadata.year
        if year is None:
            continue

        if year not in by_year:
            by_year[year] = {}

        for method, score in v.method.methods.items():
            by_year[year][method] = by_year[year].get(method, 0) + score

    if not by_year:
        return []

    years = sorted(by_year.keys())

    results = []
    seen_methods = set()

    for year in years:
        methods = by_year[year]
        emerging = []
        dominant = []

        for m in methods:
            if m not in seen_methods:
                emerging.append(m)
            seen_methods.add(m)

        # Find dominant method this year
        if methods:
            top_method = max(methods.items(), key=lambda x: x[1])
            dominant.append(top_method[0])

        results.append(
            {
                "year": year,
                "emerging_methods": emerging,
                "dominant_methods": dominant,
                "method_count": len(methods),
            }
        )

    return results


def get_method_summary(
    evolution: list[dict],
) -> str:
    """Summarize method evolution.

    Args:
        evolution: Result from track_method_evolution.

    Returns:
        Human-readable summary.
    """
    if not evolution:
        return "手法進化データなし"

    all_emerging = []
    for e in evolution:
        for m in e.get("emerging_methods", []):
            all_emerging.append((e["year"], m))

    if not all_emerging:
        return "新規手法の出現なし"

    summary_parts = []
    for year, method in all_emerging[-3:]:
        summary_parts.append(f"{year}年: {method}")

    return "主要な新手法: " + ", ".join(summary_parts)
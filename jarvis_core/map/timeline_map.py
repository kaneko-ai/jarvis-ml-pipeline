"""Timeline × Map Integration.

Per V4-M06, this integrates clusters with temporal evolution.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def build_timeline_map(
    vectors: list[PaperVector],
) -> dict:
    """Build timeline-integrated cluster map.

    Args:
        vectors: Papers to analyze.

    Returns:
        Timeline map with yearly clusters.
    """
    if not vectors:
        return {"years": [], "clusters_by_year": {}}

    # Group by year
    by_year = defaultdict(list)
    for v in vectors:
        year = v.metadata.year or 0
        by_year[year].append(v)

    years = sorted(by_year.keys())

    # Build clusters for each year
    clusters_by_year = {}
    for year in years:
        papers = by_year[year]

        # Cluster by concept
        concept_groups = defaultdict(list)
        for p in papers:
            top_concept = (
                max(p.concept.concepts.items(), key=lambda x: x[1])[0]
                if p.concept.concepts
                else "other"
            )
            concept_groups[top_concept].append(p.paper_id)

        clusters_by_year[year] = {
            "year": year,
            "paper_count": len(papers),
            "clusters": [
                {"concept": c, "papers": ids[:5], "size": len(ids)}
                for c, ids in sorted(concept_groups.items(), key=lambda x: -len(x[1]))[:5]
            ],
            "top_concept": (
                max(concept_groups.items(), key=lambda x: len(x[1]))[0] if concept_groups else None
            ),
        }

    # Detect transitions
    transitions = []
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        c1 = clusters_by_year[y1].get("top_concept")
        c2 = clusters_by_year[y2].get("top_concept")

        if c1 != c2:
            transitions.append(
                {
                    "from_year": y1,
                    "to_year": y2,
                    "from_concept": c1,
                    "to_concept": c2,
                    "type": "paradigm_shift",
                }
            )

    return {
        "years": years,
        "clusters_by_year": clusters_by_year,
        "transitions": transitions,
        "total_papers": len(vectors),
    }


def summarize_timeline(timeline_map: dict) -> str:
    """Generate timeline summary."""
    lines = ["# 時系列クラスタマップ", ""]

    for year in timeline_map["years"]:
        info = timeline_map["clusters_by_year"][year]
        lines.append(f"## {year}年 ({info['paper_count']}論文)")
        lines.append(f"- 主要トピック: {info['top_concept']}")

        for c in info["clusters"][:3]:
            lines.append(f"  - {c['concept']}: {c['size']}論文")
        lines.append("")

    if timeline_map["transitions"]:
        lines.append("## パラダイムシフト")
        for t in timeline_map["transitions"]:
            lines.append(
                f"- {t['from_year']}→{t['to_year']}: {t['from_concept']} → {t['to_concept']}"
            )

    return "\n".join(lines)

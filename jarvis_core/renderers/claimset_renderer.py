"""ClaimSet Renderer.

Per RP-23, provides citation-ready output formatting.
"""

from __future__ import annotations

import json

from ..artifacts import ClaimSet, ClaimType


def render_claimset_json(claimset: ClaimSet, indent: int = 2) -> str:
    """Render ClaimSet as JSON."""
    return json.dumps(claimset.to_dict(), indent=indent, ensure_ascii=False)


def render_claimset_markdown(
    claimset: ClaimSet,
    evidence_map: dict | None = None,
) -> str:
    """Render ClaimSet as citation-ready Markdown.

    Args:
        claimset: The ClaimSet to render.
        evidence_map: Optional map of chunk_id -> evidence details.

    Returns:
        Markdown string.
    """
    lines = ["# Claims with Evidence", ""]

    for claim in claimset.claims:
        # Claim type badge
        type_badge = "📊 FACT" if claim.claim_type == ClaimType.FACT else "💭 INFERENCE"
        conf = f"({claim.confidence:.0%})" if claim.confidence < 1.0 else ""

        lines.append(f"## {type_badge} {conf}")
        lines.append("")
        lines.append(f"> {claim.text}")
        lines.append("")

        # Citations
        if claim.citations:
            lines.append("**Evidence:**")
            for cid in claim.citations:
                if evidence_map and cid in evidence_map:
                    ev = evidence_map[cid]
                    locator = ev.get("locator", cid)
                    quote = ev.get("quote", "")[:100]
                    lines.append(f'- `{locator}`: "{quote}..."')
                else:
                    lines.append(f"- `{cid}`")
            lines.append("")
        else:
            lines.append("⚠️ **No citations provided**")
            lines.append("")

    # Gaps section
    if claimset.gaps:
        lines.append("---")
        lines.append("## ⚠️ Unsupported Areas")
        lines.append("")
        for gap in claimset.gaps:
            lines.append(f"- {gap}")
        lines.append("")

    # Coverage summary
    lines.append("---")
    lines.append(f"**Citation Coverage:** {claimset.citation_coverage:.0%}")
    lines.append(f"**Total Claims:** {len(claimset.claims)}")

    return "\n".join(lines)

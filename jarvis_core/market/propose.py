"""Market proposal generation."""

from __future__ import annotations

import json
from pathlib import Path


def load_input_assets(*, run_dir: Path, market_data_dir: Path | None) -> dict:
    assets: dict = {"papers": [], "market_data": []}
    collector_path = run_dir / "collector" / "papers.json"
    if collector_path.exists():
        try:
            assets["papers"] = json.loads(collector_path.read_text(encoding="utf-8"))
        except Exception:
            assets["papers"] = []
    if market_data_dir and market_data_dir.exists():
        for path in market_data_dir.glob("*.json"):
            try:
                assets["market_data"].append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
    return assets


def generate_proposals(assets: dict) -> list[dict]:
    papers = assets.get("papers") or []
    market_data = assets.get("market_data") or []
    base_size = len(papers)
    return [
        {
            "idea_id": "idea-1",
            "name": "OA Evidence Tracker",
            "problem": "Research teams lose track of OA findings and evidence freshness.",
            "solution": "Run-scoped harvesting + evidence dashboards for therapeutic niches.",
            "why_now": f"Based on {base_size} collected papers and market signals.",
            "risk": "Data freshness and source reliability.",
            "differentiation": "Audit-first bundle contract with traceable citations.",
            "sources_used": base_size + len(market_data),
        }
    ]


def proposals_deck_md(proposals: list[dict]) -> str:
    lines = ["# Product Ideas Deck (10-slide skeleton)", ""]
    if not proposals:
        return "# Product Ideas Deck\n\n- No proposals generated.\n"
    proposal = proposals[0]
    slides = [
        ("Slide 1", "Title", proposal["name"]),
        ("Slide 2", "Problem", proposal["problem"]),
        ("Slide 3", "Current Alternatives", "Manual review, ad-hoc search, spreadsheet tracking."),
        ("Slide 4", "Solution", proposal["solution"]),
        ("Slide 5", "Target Users", "Biotech strategy, translational research, BD teams."),
        ("Slide 6", "Market Signals", proposal["why_now"]),
        ("Slide 7", "Competitive Landscape", proposal["differentiation"]),
        ("Slide 8", "Business Model", "Subscription + enterprise data workflows."),
        ("Slide 9", "Risks", proposal["risk"]),
        ("Slide 10", "Next Steps", "PoC -> KPI validation -> launch decision."),
    ]
    for no, title, body in slides:
        lines.extend([f"## {no}: {title}", body, ""])
    return "\n".join(lines)

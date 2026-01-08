"""Research run logging and diff management.

This module provides:
- save_run(): Save a run for later comparison
- diff_runs(): Compare two runs

Per RP26, this enables tracking research evolution.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..result import EvidenceQAResult


def save_run(
    result: EvidenceQAResult,
    out_dir: str,
) -> str:
    """Save a run for later comparison.

    Creates a timestamped directory with run data.

    Args:
        result: The EvidenceQAResult to save.
        out_dir: Base output directory.

    Returns:
        Path to the saved run directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(out_dir) / "runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save run data
    run_data = {
        "timestamp": timestamp,
        "query": result.query,
        "answer": result.answer,
        "status": result.status,
        "citations": [
            {"chunk_id": c.chunk_id, "source": c.source, "locator": c.locator}
            for c in result.citations
        ],
        "claims": [],
    }

    if result.claims is not None:
        for claim in result.claims.claims:
            run_data["claims"].append(
                {
                    "id": claim.id,
                    "text": claim.text,
                    "valid": claim.valid,
                    "citations": claim.citations,
                }
            )

    run_path = run_dir / "run.json"
    with open(run_path, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2, ensure_ascii=False)

    return str(run_dir)


def load_run(run_dir: str) -> dict:
    """Load a saved run."""
    run_path = Path(run_dir) / "run.json"
    with open(run_path, encoding="utf-8") as f:
        return json.load(f)


def diff_runs(run_a_dir: str, run_b_dir: str) -> str:
    """Compare two runs and generate a diff report.

    Args:
        run_a_dir: Path to first run.
        run_b_dir: Path to second run.

    Returns:
        Markdown diff report.
    """
    run_a = load_run(run_a_dir)
    run_b = load_run(run_b_dir)

    lines = [
        "# Run Comparison",
        "",
        f"**Run A:** {run_a.get('timestamp', 'Unknown')}",
        f"**Run B:** {run_b.get('timestamp', 'Unknown')}",
        "",
        "---",
        "",
    ]

    # Compare answer
    lines.append("## Answer Comparison")
    lines.append("")
    if run_a.get("answer") == run_b.get("answer"):
        lines.append("✓ Answers are identical")
    else:
        lines.append("### Run A:")
        lines.append(f"> {run_a.get('answer', '')[:200]}...")
        lines.append("")
        lines.append("### Run B:")
        lines.append(f"> {run_b.get('answer', '')[:200]}...")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Compare claims
    lines.append("## Claims Comparison")
    lines.append("")

    claims_a = {c["id"]: c for c in run_a.get("claims", [])}
    claims_b = {c["id"]: c for c in run_b.get("claims", [])}

    ids_a = set(claims_a.keys())
    ids_b = set(claims_b.keys())

    added = ids_b - ids_a
    removed = ids_a - ids_b
    common = ids_a & ids_b

    if added:
        lines.append(f"### Added Claims ({len(added)})")
        for cid in added:
            claim = claims_b[cid]
            lines.append(f"+ {claim['text'][:60]}...")
        lines.append("")

    if removed:
        lines.append(f"### Removed Claims ({len(removed)})")
        for cid in removed:
            claim = claims_a[cid]
            lines.append(f"- {claim['text'][:60]}...")
        lines.append("")

    modified = 0
    for cid in common:
        if claims_a[cid]["text"] != claims_b[cid]["text"]:
            modified += 1

    lines.append("### Summary")
    lines.append(f"- Added: {len(added)}")
    lines.append(f"- Removed: {len(removed)}")
    lines.append(f"- Modified: {modified}")
    lines.append(f"- Unchanged: {len(common) - modified}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Compare citations
    lines.append("## Citations Comparison")
    lines.append("")

    citations_a = set(c["chunk_id"] for c in run_a.get("citations", []))
    citations_b = set(c["chunk_id"] for c in run_b.get("citations", []))

    lines.append(f"- Run A citations: {len(citations_a)}")
    lines.append(f"- Run B citations: {len(citations_b)}")
    lines.append(f"- New in B: {len(citations_b - citations_a)}")
    lines.append(f"- Removed in B: {len(citations_a - citations_b)}")

    return "\n".join(lines)

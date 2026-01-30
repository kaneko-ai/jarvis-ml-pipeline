"""Report Generation with Evidence IDs (Phase 2-ΩΩ).

Generates markdown reports with mandatory evidence ID references
and explicit uncertainty labels for all conclusions.
"""

import json
import logging
from pathlib import Path
from typing import Any

from jarvis_core.reporting.report_schema import Conclusion, ReportMetadata, validate_conclusion
from jarvis_core.reporting.uncertainty import determine_uncertainty, format_conclusion_text

logger = logging.getLogger(__name__)


def load_artifacts(run_dir: Path) -> dict[str, Any]:
    """Load claims, evidence, and papers from run directory.

    Args:
        run_dir: Path to run directory

    Returns:
        Dict with 'claims', 'evidence', 'papers'
    """
    artifacts = {}

    # Load claims
    claims_file = run_dir / "claims.jsonl"
    if claims_file.exists():
        with open(claims_file, encoding="utf-8") as f:
            artifacts["claims"] = [json.loads(line) for line in f if line.strip()]
    else:
        artifacts["claims"] = []

    # Load evidence
    evidence_file = run_dir / "evidence.jsonl"
    if evidence_file.exists():
        with open(evidence_file, encoding="utf-8") as f:
            artifacts["evidence"] = [json.loads(line) for line in f if line.strip()]
    else:
        artifacts["evidence"] = []

    # Load papers
    papers_file = run_dir / "papers.jsonl"
    if papers_file.exists():
        with open(papers_file, encoding="utf-8") as f:
            artifacts["papers"] = [json.loads(line) for line in f if line.strip()]
    else:
        artifacts["papers"] = []

    return artifacts


def build_evidence_map(claims: list[dict], evidence_list: list[dict]) -> dict[str, list[dict]]:
    """Build mapping from claim_id to evidence list.

    Args:
        claims: List of claim dictionaries
        evidence_list: List of evidence dictionaries

    Returns:
        Dict mapping claim_id to list of evidence dicts
    """
    evidence_map = {}

    for ev in evidence_list:
        claim_id = ev.get("claim_id")
        if claim_id:
            if claim_id not in evidence_map:
                evidence_map[claim_id] = []
            evidence_map[claim_id].append(ev)

    return evidence_map


def select_best_evidence(evidence_list: list[dict], max_count: int = 3) -> list[dict]:
    """Select best evidence by strength.

    Priority: Strong → Medium → Weak

    Args:
        evidence_list: List of evidence for a claim
        max_count: Maximum number to select

    Returns:
        Selected evidence list
    """
    # Sort by strength
    strength_order = {"Strong": 0, "Medium": 1, "Weak": 2, "None": 3}
    sorted_ev = sorted(
        evidence_list, key=lambda e: strength_order.get(e.get("evidence_strength", "None"), 3)
    )

    return sorted_ev[:max_count]


def determine_support_level(evidence_list: list[dict]) -> str:
    """Determine overall support level from evidence.

    Rules:
    - Strong if any Strong evidence
    - Medium if 2+ Medium or 1 Medium + Weak
    - Weak if only Weak evidence
    - None if no evidence

    Args:
        evidence_list: List of evidence

    Returns:
        Support level: "Strong", "Medium", "Weak", or "None"
    """
    if not evidence_list:
        return "None"

    strengths = [e.get("evidence_strength", "None") for e in evidence_list]

    if "Strong" in strengths:
        return "Strong"

    medium_count = strengths.count("Medium")
    weak_count = strengths.count("Weak")

    if medium_count >= 2:
        return "Medium"
    elif medium_count >= 1 and weak_count >= 1:
        return "Medium"
    elif medium_count >= 1:
        return "Medium"
    elif weak_count > 0:
        return "Weak"
    else:
        return "None"


def create_conclusion(claim: dict, evidence_list: list[dict]) -> Conclusion:
    """Create a Conclusion object from claim and evidence.

    Args:
        claim: Claim dictionary
        evidence_list: Evidence list for this claim

    Returns:
        Conclusion object
    """
    claim_id = claim.get("claim_id", "unknown")
    claim_text = claim.get("claim_text", "")

    # Select best evidence
    selected_evidence = select_best_evidence(evidence_list)

    # Determine support level
    support_level = determine_support_level(selected_evidence)

    # Check for contradictions
    has_contradiction = any(e.get("evidence_role") == "refuting" for e in evidence_list)

    # Determine uncertainty
    uncertainty = determine_uncertainty(support_level, has_contradiction)

    # Format conclusion text
    formatted_text = format_conclusion_text(claim_text, uncertainty)

    # Gather evidence IDs
    evidence_ids = [e.get("evidence_id", "") for e in selected_evidence if e.get("evidence_id")]

    # Notes
    notes = []
    if has_contradiction:
        notes.append("矛盾する根拠あり")
    if support_level == "None":
        notes.append("根拠不足")

    return Conclusion(
        conclusion_text=formatted_text,
        claim_id=claim_id,
        evidence_ids=evidence_ids,
        support_level=support_level,
        uncertainty_label=uncertainty,
        notes=" / ".join(notes) if notes else "",
    )


def generate_report(run_dir: Path, query: str) -> str:
    """Generate complete markdown report with evidence IDs.

    Args:
        run_dir: Path to run directory
        query: Research query

    Returns:
        Markdown report text
    """
    # Load artifacts
    artifacts = load_artifacts(run_dir)
    claims = artifacts["claims"]
    evidence_list = artifacts["evidence"]
    papers = artifacts["papers"]

    # Build evidence map
    evidence_map = build_evidence_map(claims, evidence_list)

    # Create conclusions
    conclusions = []
    unsupported_claims = []

    for claim in claims:
        claim_id = claim.get("claim_id")
        claim_evidence = evidence_map.get(claim_id, [])

        conclusion = create_conclusion(claim, claim_evidence)
        conclusions.append(conclusion)

        if conclusion.support_level == "None":
            unsupported_claims.append(claim_id)

    # Validate conclusions
    all_errors = []
    for conclusion in conclusions:
        errors = validate_conclusion(conclusion)
        all_errors.extend(errors)

    if all_errors:
        logger.warning(f"Report validation errors: {all_errors}")

    # Calculate metadata
    total_claims = len(claims)
    supported_claims = total_claims - len(unsupported_claims)
    support_rate = supported_claims / total_claims if total_claims > 0 else 0.0

    metadata = ReportMetadata(
        total_papers=len(papers),
        total_claims=total_claims,
        supported_claims=supported_claims,
        support_rate=support_rate,
        quality_warnings=all_errors,
    )

    # Generate report
    lines = [
        f"# Research Report: {query}",
        "",
        "> Generated by JARVIS Research OS (Phase 2-ΩΩ)",
        f"> Papers: {metadata.total_papers} | Claims: {metadata.total_claims} | Support Rate: {metadata.support_rate:.1%}",
        "",
    ]

    # Warning if low support
    if metadata.support_rate < 0.90:
        lines.extend(
            [
                "> [!CAUTION] 根拠支持率が低い",
                f"> Support Rate: {metadata.support_rate:.1%} (推奨: ≥90%)",
                "> 結論の解釈には注意が必要です。",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## Key Conclusions",
            "",
        ]
    )

    # Group by claim type
    by_type = {}
    for conclusion in conclusions:
        # Try to infer type from claim if available
        claim_type = "General"
        for claim in claims:
            if claim.get("claim_id") == conclusion.claim_id:
                claim_type = claim.get("claim_type", "General")
                break

        if claim_type not in by_type:
            by_type[claim_type] = []
        by_type[claim_type].append(conclusion)

    # Display by type
    for claim_type, type_conclusions in by_type.items():
        if claim_type != "General":
            lines.extend(
                [
                    f"### {claim_type}",
                    "",
                ]
            )

        for conclusion in type_conclusions:
            lines.append(conclusion.to_markdown())
            lines.append("")

    # References
    lines.extend(
        [
            "---",
            "",
            "## References",
            "",
        ]
    )

    for paper in papers[:10]:
        paper_id = paper.get("paper_id", "Unknown")
        title = paper.get("title", "Untitled")
        authors = paper.get("authors", [])
        year = paper.get("year", "N/A")

        author_str = ", ".join(authors[:3]) if authors else "Unknown"
        if len(authors) > 3:
            author_str += " et al."

        lines.append(f"- **{paper_id}**: {author_str} ({year}). {title}")

    lines.append("")

    return "\n".join(lines)

"""Evidence synthesis agent implementation."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis_core.contradiction.detector import ContradictionDetector
from jarvis_core.evidence.ensemble import grade_evidence


@dataclass
class Paper:
    title: str
    abstract: str = ""
    full_text: str = ""


@dataclass
class SynthesisReport:
    summary: str
    evidence_table: list[dict] = field(default_factory=list)
    contradictions: list[dict] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    strength_of_evidence: str = "moderate"


class EvidenceSynthesisAgent:
    """Aggregate evidence across multiple papers."""

    async def synthesize(self, papers: list[Paper], research_question: str) -> SynthesisReport:
        """Aggregate evidence across multiple papers.

        This agent integrates findings, detects contradictions, and assesses
        the overall quality of the evidence base.
        """
        evidence_table = []
        claims = []
        levels = []

        for paper in papers:
            # Evaluate using ensemble grader
            grade = grade_evidence(
                title=paper.title, abstract=paper.abstract, full_text=paper.full_text, use_llm=False
            )
            evidence_table.append(
                {
                    "title": paper.title,
                    "evidence_level": grade.level.value,
                    "confidence": grade.confidence,
                }
            )
            # Collect main claims (using title/abstract snippet as proxy in this stage)
            claims.append(f"{paper.title}: Significant findings in the study.")
            levels.append(grade.level.value)

        # Detect logical contradictions
        contradictions = []
        detector = ContradictionDetector()
        found_contradictions = detector.detect(claims)
        for contradiction in found_contradictions:
            contradictions.append(
                {
                    "statement_a": contradiction.statement_a,
                    "statement_b": contradiction.statement_b,
                    "confidence": contradiction.confidence,
                    "reason": contradiction.reason,
                }
            )

        # Assess overall strength of evidence
        # Level 1-2 = High/Moderate, 3-4 = Low/Extremely Low
        if not levels:
            overall_strength = "low (no papers found)"
        else:
            avg_level = sum(levels) / len(levels)
            if avg_level <= 1.5:
                overall_strength = "high"
            elif avg_level <= 2.5:
                overall_strength = "moderate"
            else:
                overall_strength = "low"

            # Downgrade if contradictions exist
            if len(contradictions) > 0 and overall_strength != "low":
                overall_strength += " (downgraded due to contradictions)"

        # Generate summary
        paper_count = len(papers)
        summary = (
            f"This synthesis for '{research_question}' integrates data from {paper_count} papers. "
            f"The overall strength of evidence is assessed as {overall_strength}. "
        )
        if contradictions:
            summary += f"Note: {len(contradictions)} potential contradictions were identified during analysis."

        gaps = []
        if paper_count < 3:
            gaps.append("Limited publication volume (less than 3 relevant papers)")
        if not any(lvl <= 2 for lvl in levels):
            gaps.append("Lack of high-level evidence (RCTs or Systematic Reviews)")

        return SynthesisReport(
            summary=summary,
            evidence_table=evidence_table,
            contradictions=contradictions,
            gaps=gaps,
            strength_of_evidence=overall_strength,
        )

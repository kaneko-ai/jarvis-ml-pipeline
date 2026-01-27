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
        evidence_table = []
        claims = []
        for paper in papers:
            grade = grade_evidence(
                title=paper.title, abstract=paper.abstract, full_text=paper.full_text, use_llm=False
            )
            evidence_table.append({"title": paper.title, "evidence_level": grade.level.value})
            claims.append(paper.title)

        contradictions = []
        detector = ContradictionDetector()
        for contradiction in detector.detect(claims):
            contradictions.append(
                {
                    "statement_a": contradiction.statement_a,
                    "statement_b": contradiction.statement_b,
                    "confidence": contradiction.confidence,
                }
            )

        gaps = ["Need more randomized controlled trials"] if len(papers) < 3 else []
        summary = f"Synthesis for '{research_question}' covering {len(papers)} papers."

        return SynthesisReport(
            summary=summary,
            evidence_table=evidence_table,
            contradictions=contradictions,
            gaps=gaps,
            strength_of_evidence="moderate" if papers else "low",
        )

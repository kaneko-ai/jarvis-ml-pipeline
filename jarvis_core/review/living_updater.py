"""Living review updater."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from jarvis_core.advanced.features import SystematicReviewAgent
from jarvis_core.evidence.ensemble import grade_evidence


@dataclass
class NewPaper:
    paper_id: str
    title: str
    abstract: str
    published_at: str | None = None


@dataclass
class UpdateReport:
    review_id: str
    updated_at: str
    new_papers: list[NewPaper] = field(default_factory=list)
    evidence_grades: list[dict] = field(default_factory=list)
    prisma_flow: dict | None = None


class LivingReviewUpdater:
    """Checks for new papers and updates a living review."""

    def __init__(self):
        self._last_checked: dict[str, str] = {}

    def check_for_updates(self, review_id: str) -> list[NewPaper]:
        """Return new papers since last check (placeholder implementation)."""
        _ = self._last_checked.get(review_id)
        self._last_checked[review_id] = datetime.utcnow().isoformat()
        return []

    async def update_review(self, review_id: str, new_papers: list[NewPaper]) -> UpdateReport:
        """Update review with new papers and return report."""
        review = SystematicReviewAgent()
        evidence_grades = []
        for paper in new_papers:
            review.add_paper(paper.paper_id, {"title": paper.title}, stage="identification")
            grade = grade_evidence(title=paper.title, abstract=paper.abstract, use_llm=False)
            evidence_grades.append(
                {"paper_id": paper.paper_id, "evidence_level": grade.level.value}
            )

        prisma_flow = review.get_prisma_flow()
        return UpdateReport(
            review_id=review_id,
            updated_at=datetime.utcnow().isoformat(),
            new_papers=new_papers,
            evidence_grades=evidence_grades,
            prisma_flow=prisma_flow,
        )
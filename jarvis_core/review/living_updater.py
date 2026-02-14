"""Living review updater."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

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

    async def check_for_updates(
        self, review_id: str, available_papers: list[NewPaper]
    ) -> list[NewPaper]:
        """Return new papers since last check.

        Typically this would query PubMed/OpenAlex with a date range,
        but for this implementation we simulate by filtering provided papers.
        """
        last_check_str = self._last_checked.get(review_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self._last_checked[review_id] = now.isoformat()

        if not last_check_str:
            return available_papers  # First check, everything is "new"

        last_check = datetime.fromisoformat(last_check_str)
        new_only = []
        for paper in available_papers:
            if paper.published_at:
                pub_date = datetime.fromisoformat(paper.published_at)
                if pub_date > last_check:
                    new_only.append(paper)
            else:
                # If no date, treat as new for safety in this simulation
                new_only.append(paper)

        return new_only

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
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            new_papers=new_papers,
            evidence_grades=evidence_grades,
            prisma_flow=prisma_flow,
        )

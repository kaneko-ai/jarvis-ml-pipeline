"""Conflict of interest detection."""

from __future__ import annotations

from dataclasses import dataclass
import re

from jarvis_core.extraction.funding import FundingSource


@dataclass
class Author:
    name: str
    affiliation: str | None = None
    declared_conflicts: str | None = None


@dataclass
class PotentialConflict:
    type: str
    description: str
    severity: str


PHARMA_KEYWORDS = ["pharma", "therapeutics", "biotech", "drug", "inc.", "ltd"]


def detect_conflicts(authors: list[Author], funding: list[FundingSource]) -> list[PotentialConflict]:
    """Detect potential conflicts of interest."""
    conflicts: list[PotentialConflict] = []

    for author in authors:
        affiliation = (author.affiliation or "").lower()
        if any(keyword in affiliation for keyword in PHARMA_KEYWORDS):
            conflicts.append(
                PotentialConflict(
                    type="author_affiliation",
                    description=f"{author.name} affiliated with industry: {author.affiliation}",
                    severity="high",
                )
            )
        if author.declared_conflicts:
            conflicts.append(
                PotentialConflict(
                    type="author_declaration",
                    description=author.declared_conflicts,
                    severity="medium",
                )
            )

    for source in funding:
        if source.funder_type == "industry":
            conflicts.append(
                PotentialConflict(
                    type="industry_funding",
                    description=f"Industry funding from {source.funder_name}",
                    severity="medium",
                )
            )

    return conflicts

"""Funding disclosure extraction."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class FundingSource:
    funder_name: str
    grant_id: str | None
    funder_type: str


FUNDING_PATTERNS = [
    (r"NIH|National Institutes of Health", "government"),
    (r"NSF|National Science Foundation", "government"),
    (r"WHO|World Health Organization", "nonprofit"),
    (r"Wellcome Trust", "nonprofit"),
    (r"Gates Foundation", "nonprofit"),
    (r"Pfizer|Moderna|AstraZeneca|Novartis", "industry"),
]

GRANT_PATTERN = re.compile(r"(grant|award)\s*#?\s*([A-Za-z0-9\-]+)", re.IGNORECASE)


def extract_funding(text: str) -> list[FundingSource]:
    """Extract funding sources from text."""
    sources: list[FundingSource] = []
    for pattern, funder_type in FUNDING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            grant_match = GRANT_PATTERN.search(text)
            grant_id = grant_match.group(2) if grant_match else None
            sources.append(
                FundingSource(
                    funder_name=pattern.split("|")[0].strip(),
                    grant_id=grant_id,
                    funder_type=funder_type,
                )
            )
    return sources
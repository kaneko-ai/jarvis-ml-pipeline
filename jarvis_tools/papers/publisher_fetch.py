"""Publisher Fetch.

Per RP-103, fetches papers from publisher URLs via DOI resolution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from .fetch_policy import FetchPolicy, DEFAULT_FETCH_POLICY


@dataclass
class FetchCandidate:
    """A candidate URL for fetching."""

    url: str
    source: str  # doi, publisher, pmc, local
    domain: str
    priority: int = 0
    is_oa: bool = False
    notes: str = ""


@dataclass
class FetchDecision:
    """Decision on whether to fetch a candidate."""

    allowed: bool
    reason: str
    candidate: FetchCandidate
    policy_version: str = "1.0"


@dataclass
class FetchLegalMeta:
    """Legal metadata for audit trail (RP-104)."""

    source: str
    domain: str
    policy_version: str
    allowed: bool
    reason: str
    timestamp: str = ""


def resolve_doi_to_candidates(doi: str) -> List[FetchCandidate]:
    """Resolve DOI to candidate URLs.

    Note: This is a minimal implementation using doi.org redirect.
    Does NOT make network calls - returns expected URL patterns.
    """
    if not doi:
        return []

    # Clean DOI
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    elif doi.startswith("http://doi.org/"):
        doi = doi.replace("http://doi.org/", "")
    elif doi.startswith("doi:"):
        doi = doi.replace("doi:", "")

    candidates = []

    # Primary: doi.org redirect URL
    doi_url = f"https://doi.org/{doi}"
    candidates.append(FetchCandidate(
        url=doi_url,
        source="doi",
        domain="doi.org",
        priority=1,
        notes="DOI resolver redirect",
    ))

    # Check for known OA patterns
    if "pmc" in doi.lower() or "nih" in doi.lower():
        candidates.append(FetchCandidate(
            url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{doi}/pdf/",
            source="pmc",
            domain="ncbi.nlm.nih.gov",
            priority=0,
            is_oa=True,
            notes="PMC OA",
        ))

    return candidates


def resolve_pmid_to_candidates(pmid: str) -> List[FetchCandidate]:
    """Resolve PMID to candidate URLs."""
    if not pmid:
        return []

    pmid = pmid.strip()

    candidates = [
        # PubMed abstract page
        FetchCandidate(
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            source="pubmed",
            domain="ncbi.nlm.nih.gov",
            priority=2,
            notes="PubMed abstract page",
        ),
    ]

    return candidates


def check_fetch_decision(
    candidate: FetchCandidate,
    policy: Optional[FetchPolicy] = None,
) -> FetchDecision:
    """Check if a candidate can be fetched under policy."""
    if policy is None:
        policy = DEFAULT_FETCH_POLICY

    domain = candidate.domain.lower()

    # OA is always allowed
    if candidate.is_oa:
        return FetchDecision(
            allowed=True,
            reason="Open Access content",
            candidate=candidate,
        )

    # Check allowed adapters
    allowed_domains = {
        "ncbi.nlm.nih.gov": "pmc_oa",
        "doi.org": "doi_resolver",
    }

    if domain in allowed_domains:
        adapter = allowed_domains[domain]
        if adapter in policy.get_allowed_adapters() or adapter == "doi_resolver":
            return FetchDecision(
                allowed=True,
                reason=f"Domain {domain} allowed by policy",
                candidate=candidate,
            )

    # Publisher fetch requires explicit policy
    if candidate.source == "publisher":
        if policy.can_fetch_from_publisher(candidate.is_oa):
            return FetchDecision(
                allowed=True,
                reason="Publisher fetch allowed by policy",
                candidate=candidate,
            )
        else:
            return FetchDecision(
                allowed=False,
                reason=f"Publisher PDF from {domain} denied by policy",
                candidate=candidate,
            )

    # Default: deny with reason
    return FetchDecision(
        allowed=False,
        reason=f"Domain {domain} not in allowlist",
        candidate=candidate,
    )


def get_fetch_candidates(
    doi: Optional[str] = None,
    pmid: Optional[str] = None,
    policy: Optional[FetchPolicy] = None,
) -> List[FetchDecision]:
    """Get all fetch candidates with policy decisions.

    Returns candidates sorted by priority (lowest first = highest priority).
    """
    if policy is None:
        policy = DEFAULT_FETCH_POLICY

    candidates = []

    if doi:
        candidates.extend(resolve_doi_to_candidates(doi))
    if pmid:
        candidates.extend(resolve_pmid_to_candidates(pmid))

    # Check each against policy
    decisions = [check_fetch_decision(c, policy) for c in candidates]

    # Sort by priority
    decisions.sort(key=lambda d: d.candidate.priority)

    return decisions

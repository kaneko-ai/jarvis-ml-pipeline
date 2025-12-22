"""Fetch Policy.

Per RP-103/106, defines unified fetch policy rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class FetchSource(Enum):
    """Fetch source types."""

    LOCAL = "local"
    PMC_OA = "pmc_oa"
    UNPAYWALL = "unpaywall"
    PUBLISHER = "publisher"
    HTML_FALLBACK = "html_fallback"


@dataclass
class FetchPolicy:
    """Unified fetch policy.

    Per RP-106, source_order is the single source of truth.
    """

    # Source priority order (RP-106: single source of truth)
    source_order: List[FetchSource] = field(default_factory=lambda: [
        FetchSource.LOCAL,
        FetchSource.PMC_OA,
        FetchSource.UNPAYWALL,
        FetchSource.PUBLISHER,
        FetchSource.HTML_FALLBACK,
    ])

    # Allowed adapters
    allowed_adapters: List[str] = field(default_factory=lambda: [
        "local",
        "pmc_oa",
        "unpaywall_pdf",
    ])

    # Publisher PDF policy
    publisher_pdf_enabled: bool = False
    publisher_pdf_oa_only: bool = True

    # HTML fallback
    html_fallback_enabled: bool = True

    # Domain allowlist
    domain_allowlist: List[str] = field(default_factory=lambda: [
        "ncbi.nlm.nih.gov",
        "pmc.ncbi.nlm.nih.gov",
        "pubmed.ncbi.nlm.nih.gov",
    ])

    # Domain denylist
    domain_denylist: List[str] = field(default_factory=list)

    # Policy version for audit
    version: str = "1.0"

    def get_allowed_adapters(self) -> List[str]:
        """Get allowed adapters."""
        return self.allowed_adapters

    def can_fetch_from_publisher(self, is_oa: bool) -> bool:
        """Check if publisher fetch is allowed."""
        if not self.publisher_pdf_enabled:
            return False
        if self.publisher_pdf_oa_only and not is_oa:
            return False
        return True

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is allowed."""
        domain = domain.lower()

        # Check denylist first
        if any(d in domain for d in self.domain_denylist):
            return False

        # Check allowlist if populated
        if self.domain_allowlist:
            return any(d in domain for d in self.domain_allowlist)

        return True

    def get_order(self) -> List[FetchSource]:
        """Get source order (single source of truth per RP-106)."""
        return self.source_order


# Default policy
DEFAULT_FETCH_POLICY = FetchPolicy()


# Error for policy violations
class PolicyViolationError(Exception):
    """Raised when fetch violates policy."""

    def __init__(self, reason: str, domain: str = "", source: str = ""):
        self.reason = reason
        self.domain = domain
        self.source = source
        super().__init__(f"Policy violation: {reason}")


def check_policy(
    domain: str,
    source: FetchSource,
    is_oa: bool = False,
    policy: Optional[FetchPolicy] = None,
) -> tuple[bool, str]:
    """Check if fetch is allowed under policy.

    Returns:
        (allowed, reason)
    """
    if policy is None:
        policy = DEFAULT_FETCH_POLICY

    # Check domain
    if not policy.is_domain_allowed(domain):
        return False, f"Domain {domain} not in allowlist"

    # Check source type
    if source == FetchSource.PUBLISHER:
        if not policy.can_fetch_from_publisher(is_oa):
            return False, "Publisher PDF not allowed by policy"

    if source == FetchSource.HTML_FALLBACK:
        if not policy.html_fallback_enabled:
            return False, "HTML fallback disabled by policy"

    return True, "Allowed by policy"

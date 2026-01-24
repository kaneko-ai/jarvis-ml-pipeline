"""License Compliance Module (Phase 30).

Enforces Open Access compatibility for retrieval operations.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class LicenseType(Enum):
    CC_BY = "cc-by"
    CC0 = "cc0"
    PUBLIC_DOMAIN = "public-domain"
    CC_BY_SA = "cc-by-sa"
    CC_BY_NC = "cc-by-nc"
    CC_BY_ND = "cc-by-nd"
    UNKNOWN = "unknown"
    COPYRIGHTED = "copyrighted"

class LicenseFilter:
    """Filters content based on license compatibility."""

    # Default allowed licenses for commercial/research use
    # Note: NC (Non-Commercial) licenses might be restricted depending on use case.
    DEFAULT_ALLOWLIST = {
        LicenseType.CC_BY,
        LicenseType.CC0,
        LicenseType.PUBLIC_DOMAIN,
        LicenseType.CC_BY_SA,
    }

    def __init__(self, allowlist: Optional[set[LicenseType]] = None):
        self.allowlist = allowlist or self.DEFAULT_ALLOWLIST

    def is_allowed(self, license_str: str) -> bool:
        """Check if a license string is in the allowlist."""
        license_type = self._parse_license(license_str)
        return license_type in self.allowlist

    def filter_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter a list of search results."""
        allowed = []
        for res in results:
            lic = res.get("license", "unknown")
            if self.is_allowed(lic):
                allowed.append(res)
            else:
                logger.debug(f"Filtered out result due to license: {lic}")
        return allowed

    def _parse_license(self, license_str: str) -> LicenseType:
        """Normalize license string to enum."""
        if not license_str:
            return LicenseType.UNKNOWN
            
        s = license_str.lower().strip()
        
        if "cc0" in s or "public domain" in s:
            return LicenseType.CC0
        if "cc-by-nc" in s or "cc by-nc" in s:
            return LicenseType.CC_BY_NC
        if "cc-by-nd" in s or "cc by-nd" in s:
            return LicenseType.CC_BY_ND
        if "cc-by-sa" in s or "cc by-sa" in s:
            return LicenseType.CC_BY_SA
        if "cc-by" in s or "cc by" in s: # Check this last as it's a substring of others
            return LicenseType.CC_BY
        
        return LicenseType.UNKNOWN

"""Open access resolver with evidence tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass
class OAEvidence:
    """Evidence supporting OA status."""

    source: str
    pmcid: str = ""
    license: str = ""
    url_best_oa: str = ""
    checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "pmcid": self.pmcid,
            "license": self.license,
            "url_best_oa": self.url_best_oa,
            "checked_at": self.checked_at,
        }


class OAResolver:
    """Resolve OA status using PMC and Unpaywall evidence."""

    def __init__(self, unpaywall_email: str | None = None, timeout: int = 15) -> None:
        self.unpaywall_email = unpaywall_email
        self.timeout = timeout

    def resolve(self, paper: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        pmcid = (paper.get("pmcid") or "").strip()
        doi = (paper.get("doi") or "").strip()

        if pmcid:
            evidence = OAEvidence(
                source="pmc",
                pmcid=pmcid,
                url_best_oa=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
                checked_at=now,
            )
            return {
                "oa_status": "gold",
                "oa_evidence": evidence.to_dict(),
            }

        if doi:
            unpaywall = self._fetch_unpaywall(doi)
            if unpaywall:
                status = unpaywall.get("oa_status") or (
                    "gold" if unpaywall.get("is_oa") else "closed"
                )
                best_location = unpaywall.get("best_oa_location") or {}
                evidence = OAEvidence(
                    source="unpaywall",
                    pmcid="",
                    license=best_location.get("license") or "",
                    url_best_oa=best_location.get("url") or best_location.get("url_for_pdf") or "",
                    checked_at=now,
                )
                return {
                    "oa_status": status,
                    "oa_evidence": evidence.to_dict(),
                }

        evidence = OAEvidence(source="unknown", checked_at=now)
        return {
            "oa_status": "unknown",
            "oa_evidence": evidence.to_dict(),
        }

    def _fetch_unpaywall(self, doi: str) -> dict[str, Any] | None:
        if not self.unpaywall_email:
            return None
        try:
            url = f"https://api.unpaywall.org/v2/{quote(doi)}?email={quote(self.unpaywall_email)}"
            req = Request(url, headers={"User-Agent": "Jarvis-ML-Pipeline/1.0"})
            with urlopen(req, timeout=self.timeout) as response:  # nosec B310
                payload = response.read().decode("utf-8")
            return json.loads(payload)
        except (URLError, ValueError):
            return None

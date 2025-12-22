"""Fetch Adapters.

Per RP-10, provides adapters for paper retrieval with safe defaults.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
import os


class BaseFetchAdapter(ABC):
    """Base class for paper fetch adapters."""

    @abstractmethod
    def fetch(self, paper_id: str, **kwargs) -> Optional[str]:
        """Fetch paper and return local path."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name."""
        pass


class PmcOaAdapter(BaseFetchAdapter):
    """PMC Open Access adapter."""

    @property
    def name(self) -> str:
        return "pmc_oa"

    def fetch(self, paper_id: str, output_dir: str = ".", **kwargs) -> Optional[str]:
        """Fetch from PMC OA."""
        from .pmc_oa import download_oa_pdf

        pmcid = kwargs.get("pmcid") or paper_id
        output_path = Path(output_dir) / f"pmc_{pmcid}.pdf"

        if download_oa_pdf(pmcid, str(output_path)):
            return str(output_path)
        return None


class LocalDirectoryAdapter(BaseFetchAdapter):
    """Local directory adapter for user-provided PDFs."""

    def __init__(self, local_dir: str = "~/papers"):
        self.local_dir = Path(local_dir).expanduser()

    @property
    def name(self) -> str:
        return "local_dir"

    def fetch(self, paper_id: str, **kwargs) -> Optional[str]:
        """Find paper in local directory."""
        if not self.local_dir.exists():
            return None

        # Search by various patterns
        patterns = [
            f"*{paper_id}*.pdf",
            f"*{paper_id.replace('-', '')}*.pdf",
        ]

        doi = kwargs.get("doi")
        if doi:
            # doi: 10.1234/abc -> abc.pdf
            doi_suffix = doi.split("/")[-1] if "/" in doi else doi
            patterns.append(f"*{doi_suffix}*.pdf")

        for pattern in patterns:
            matches = list(self.local_dir.glob(pattern))
            if matches:
                return str(matches[0])

        return None


class UnpaywallAdapter(BaseFetchAdapter):
    """Unpaywall OA check adapter (no API key required for basic check)."""

    @property
    def name(self) -> str:
        return "unpaywall"

    def fetch(self, paper_id: str, output_dir: str = ".", **kwargs) -> Optional[str]:
        """Check Unpaywall for OA version."""
        import urllib.request
        import json

        doi = kwargs.get("doi")
        if not doi:
            return None

        # Use a generic email for Unpaywall API
        email = os.environ.get("UNPAYWALL_EMAIL", "user@example.com")
        url = f"https://api.unpaywall.org/v2/{doi}?email={email}"

        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())

            if data.get("is_oa"):
                best_oa = data.get("best_oa_location", {})
                pdf_url = best_oa.get("url_for_pdf")

                if pdf_url:
                    output_path = Path(output_dir) / f"unpaywall_{paper_id}.pdf"
                    urllib.request.urlretrieve(pdf_url, str(output_path))
                    return str(output_path)

        except Exception:
            pass

        return None


class FetchAdapterManager:
    """Manages fetch adapters with priority order."""

    def __init__(self, adapters: List[str] = None, local_dir: str = "~/papers"):
        self.adapter_map = {
            "pmc_oa": PmcOaAdapter(),
            "local_dir": LocalDirectoryAdapter(local_dir),
            "unpaywall": UnpaywallAdapter(),
        }

        # Default: safe adapters only
        self.priority = adapters or ["pmc_oa", "unpaywall", "local_dir"]

    def fetch(self, paper_id: str, output_dir: str = ".", **kwargs) -> Optional[str]:
        """Try adapters in priority order."""
        for adapter_name in self.priority:
            adapter = self.adapter_map.get(adapter_name)
            if adapter:
                result = adapter.fetch(paper_id, output_dir=output_dir, **kwargs)
                if result:
                    return result
        return None

    def get_failure_reason(self, paper_id: str) -> str:
        """Get reason for fetch failure."""
        return f"no_oa_available: Tried {', '.join(self.priority)}"

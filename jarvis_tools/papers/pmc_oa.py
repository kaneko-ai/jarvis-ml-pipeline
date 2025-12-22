"""PMC Open Access PDF functions.

Per RP-04, extracted from run_pipeline.py.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional


def get_oa_pdf_url(pmcid: str) -> Optional[str]:
    """Get Open Access PDF URL for a PMCID.

    Args:
        pmcid: PMC ID (without "PMC" prefix).

    Returns:
        FTP URL for PDF, or None if not available.
    """
    base = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
    params = {"id": f"PMC{pmcid}"}
    url = f"{base}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()

        root = ET.fromstring(data)

        # Check for error
        error = root.find(".//error")
        if error is not None:
            return None

        # Find PDF link
        for record in root.findall(".//record"):
            for link in record.findall("link"):
                if link.attrib.get("format") == "pdf":
                    href = link.attrib.get("href", "")
                    if href:
                        return href

        return None

    except Exception as e:
        print(f"[get_oa_pdf_url] Error for PMC{pmcid}: {e}")
        return None


def download_oa_pdf(pmcid: str, output_path: str) -> bool:
    """Download Open Access PDF.

    Args:
        pmcid: PMC ID.
        output_path: Where to save the PDF.

    Returns:
        True if successful.
    """
    pdf_url = get_oa_pdf_url(pmcid)
    if not pdf_url:
        return False

    try:
        urllib.request.urlretrieve(pdf_url, output_path)
        return True
    except Exception as e:
        print(f"[download_oa_pdf] Error: {e}")
        return False

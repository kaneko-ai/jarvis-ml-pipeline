"""Data sources for R&D radar."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import requests  # type: ignore[import-untyped]
from defusedxml import ElementTree as DefusedET
from defusedxml.common import DefusedXmlException

from jarvis_core.sources.arxiv_client import ArxivClient


def collect_findings(
    *,
    source: str,
    query: str,
    since_days: int,
    rss_url: str | None = None,
    manual_urls_path: str | None = None,
) -> tuple[list[dict], list[dict]]:
    warnings: list[dict] = []
    findings: list[dict] = []
    if source in {"arxiv", "all"}:
        findings.extend(_from_arxiv(query=query))
    if source in {"rss", "all"} and rss_url:
        rss_findings, rss_warnings = _from_rss(rss_url)
        findings.extend(rss_findings)
        warnings.extend(rss_warnings)
    if manual_urls_path:
        findings.extend(_from_manual_urls(manual_urls_path))
    if not findings:
        warnings.append(
            {"code": "RADAR_EMPTY", "msg": "No radar findings collected.", "severity": "warning"}
        )
    return findings, warnings


def _from_arxiv(*, query: str) -> list[dict]:
    client = ArxivClient()
    papers = client.search(query=query, max_results=20, sort_by="submittedDate")
    findings = []
    for paper in papers:
        findings.append(
            {
                "source": "arxiv",
                "id": f"arxiv:{paper.arxiv_id}",
                "title": paper.title,
                "summary": paper.abstract,
                "url": paper.abs_url or "",
                "published": paper.published.isoformat() if paper.published else None,
            }
        )
    return findings


def _from_rss(rss_url: str) -> tuple[list[dict], list[dict]]:
    warnings: list[dict] = []
    try:
        response = requests.get(rss_url, timeout=15)
        response.raise_for_status()
        root = DefusedET.fromstring(response.text)
    except (requests.RequestException, ET.ParseError, DefusedXmlException) as exc:
        return [], [{"code": "RSS_FETCH_FAILED", "msg": str(exc), "severity": "warning"}]

    items = root.findall(".//item")
    findings: list[dict] = []
    for item in items[:20]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        findings.append(
            {"source": "rss", "id": link or title, "title": title, "summary": desc, "url": link}
        )
    return findings, warnings


def _from_manual_urls(path: str) -> list[dict]:
    manual_path = Path(path)
    if not manual_path.exists():
        return []
    findings: list[dict] = []
    for line in manual_path.read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        findings.append({"source": "manual", "id": url, "title": url, "summary": "", "url": url})
    return findings

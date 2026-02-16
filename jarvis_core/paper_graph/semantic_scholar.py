"""Semantic Scholar access helpers for paper graph features."""

from __future__ import annotations

from dataclasses import dataclass

from jarvis_core.sources.semantic_scholar_client import SemanticScholarClient


@dataclass
class FetchResult:
    paper: dict | None
    references: list[dict]
    warnings: list[dict]


def fetch_root_and_references(
    *,
    s2_id: str,
    max_refs: int,
    offline: bool,
    timeout_sec: float = 20.0,
) -> FetchResult:
    if offline:
        return FetchResult(
            paper=None,
            references=[],
            warnings=[
                {
                    "code": "OFFLINE_MODE",
                    "msg": "Network access disabled by offline mode.",
                    "severity": "warning",
                }
            ],
        )

    client = SemanticScholarClient()
    warnings: list[dict] = []
    paper = _safe_get_paper(client, s2_id, timeout_sec=timeout_sec)
    if not paper:
        warnings.append(
            {
                "code": "PAPER_ID_RESOLVE_FAILED",
                "msg": f"Could not resolve paper id via Semantic Scholar: {s2_id}",
                "severity": "warning",
            }
        )
        return FetchResult(paper=None, references=[], warnings=warnings)

    references = _safe_get_references(
        client,
        paper.get("paperId", s2_id),
        limit=max_refs,
        timeout_sec=timeout_sec,
    )
    if not references:
        warnings.append(
            {
                "code": "REFERENCE_FETCH_EMPTY",
                "msg": "No references fetched from Semantic Scholar.",
                "severity": "warning",
            }
        )
    return FetchResult(paper=paper, references=references, warnings=warnings)


def fetch_references(
    *,
    paper_id: str,
    max_refs: int,
    offline: bool,
    timeout_sec: float = 20.0,
) -> tuple[list[dict], list[dict]]:
    if offline:
        return [], [
            {
                "code": "OFFLINE_MODE",
                "msg": "Reference fetch skipped due to offline mode.",
                "severity": "warning",
            }
        ]
    client = SemanticScholarClient()
    refs = _safe_get_references(client, paper_id, limit=max_refs, timeout_sec=timeout_sec)
    if refs:
        return refs, []
    return refs, [
        {
            "code": "REFERENCE_FETCH_EMPTY",
            "msg": f"No references fetched for paper: {paper_id}",
            "severity": "warning",
        }
    ]


def _safe_get_paper(
    client: SemanticScholarClient, paper_id: str, timeout_sec: float
) -> dict | None:
    try:
        paper = client.get_paper(paper_id)
    except Exception:
        return None
    if not paper:
        return None
    if hasattr(paper, "to_dict"):
        return paper.to_dict()
    if isinstance(paper, dict):
        return paper
    return None


def _safe_get_references(
    client: SemanticScholarClient, paper_id: str, *, limit: int, timeout_sec: float
) -> list[dict]:
    try:
        refs = client.get_references(paper_id, limit=limit)
    except Exception:
        return []
    result: list[dict] = []
    for ref in refs or []:
        if hasattr(ref, "to_dict"):
            result.append(ref.to_dict())
        elif isinstance(ref, dict):
            result.append(ref)
    return result

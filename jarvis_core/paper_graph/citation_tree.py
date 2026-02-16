"""Citation tree builder (depth-limited BFS)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

from .ids import paper_key_from_dict


@dataclass
class CitationTreeResult:
    nodes: list[dict]
    edges: list[dict]
    warnings: list[dict]


def build_tree(
    *,
    root: dict,
    depth: int,
    max_per_level: int,
    fetch_refs: Callable[[str, int], tuple[list[dict], list[dict]]],
) -> CitationTreeResult:
    nodes_by_id: dict[str, dict] = {}
    edges: list[dict] = []
    warnings: list[dict] = []

    root_key = paper_key_from_dict(root)
    nodes_by_id[root_key] = _to_node(root, level=0)
    q: deque[tuple[str, dict, int]] = deque([(root_key, root, 0)])

    while q:
        from_key, current, level = q.popleft()
        if level >= depth:
            continue
        current_id = str(current.get("paperId") or "")
        refs, fetch_warnings = fetch_refs(current_id, max_per_level)
        warnings.extend(fetch_warnings)
        for ref in refs[:max_per_level]:
            key = paper_key_from_dict(ref)
            if key not in nodes_by_id:
                nodes_by_id[key] = _to_node(ref, level=level + 1)
                q.append((key, ref, level + 1))
            edges.append({"from_node_id": from_key, "to_node_id": key, "type": "cites"})

    return CitationTreeResult(nodes=list(nodes_by_id.values()), edges=edges, warnings=warnings)


def _to_node(paper: dict, *, level: int) -> dict:
    external_ids = paper.get("externalIds") or {}
    ids = {
        "doi": external_ids.get("DOI") if isinstance(external_ids, dict) else None,
        "pmid": external_ids.get("PubMed") if isinstance(external_ids, dict) else None,
        "arxiv": external_ids.get("ArXiv") if isinstance(external_ids, dict) else None,
    }
    return {
        "node_id": paper_key_from_dict(paper),
        "title": paper.get("title", ""),
        "year": paper.get("year"),
        "venue": paper.get("venue", ""),
        "ids": ids,
        "level": level,
        "inbound_cites": paper.get("citationCount", 0),
    }

"""Research-oriented API endpoints."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from jarvis_core.scoring.paper_score import score_paper


router = APIRouter()


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _claims_by_paper(claims: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for claim in claims:
        grouped.setdefault(claim.get("paper_id", ""), []).append(claim)
    return grouped


def _top_claims(claims: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    def avg_score(claim: Dict[str, Any]) -> float:
        evidence = claim.get("evidence") or []
        if not evidence:
            return 0.0
        return sum(item.get("score", 0.0) for item in evidence) / max(len(evidence), 1)

    return sorted(claims, key=avg_score, reverse=True)[:limit]


@router.get("/api/research/rank")
async def rank_papers(
    run_id: str = Query(...),
    q: str = Query(""),
    top_k: int = Query(50, ge=1, le=200),
    mode: str = Query("hybrid"),
):
    run_dir = Path("data/research") / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="run not found")

    papers = _load_jsonl(run_dir / "canonical_papers.jsonl")
    claims = _load_jsonl(run_dir / "claims.jsonl")
    claims_grouped = _claims_by_paper(claims)

    ranked: List[Dict[str, Any]] = []
    for paper in papers:
        paper_id = paper.get("canonical_paper_id") or paper.get("paper_id") or ""
        paper_claims = claims_grouped.get(paper_id, [])
        score_result = score_paper(paper, paper_claims, query=q)
        ranked.append(
            {
                **paper,
                "score": score_result.score,
                "tier": score_result.tier,
                "score_breakdown": score_result.breakdown,
                "audit_flags": paper.get("audit_flags", []),
                "top_claims": _top_claims(paper_claims),
                "mode": mode,
            }
        )

    ranked.sort(key=lambda item: item.get("score", 0), reverse=True)
    return {"run_id": run_id, "count": len(ranked), "results": ranked[:top_k]}


@router.get("/api/research/paper/{paper_id}")
async def get_paper(paper_id: str, run_id: str = Query(...)):
    run_dir = Path("data/research") / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="run not found")

    papers = _load_jsonl(run_dir / "canonical_papers.jsonl")
    claims = _load_jsonl(run_dir / "claims.jsonl")
    paper = next(
        (p for p in papers if p.get("canonical_paper_id") == paper_id or p.get("paper_id") == paper_id),
        None,
    )
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")

    paper_claims = [c for c in claims if c.get("paper_id") == paper_id]
    return {"paper": paper, "claims": paper_claims}


@router.get("/api/research/export")
async def export_research(run_id: str = Query(...), format: str = Query("jsonl")):
    run_dir = Path("data/research") / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="run not found")

    papers = _load_jsonl(run_dir / "canonical_papers.jsonl")
    claims = _load_jsonl(run_dir / "claims.jsonl")
    claims_grouped = _claims_by_paper(claims)

    rows = []
    for paper in papers:
        paper_id = paper.get("canonical_paper_id") or paper.get("paper_id") or ""
        rows.append({**paper, "claims": claims_grouped.get(paper_id, [])})

    if format == "jsonl":
        payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
        return PlainTextResponse(payload, media_type="application/jsonl")
    if format == "csv":
        output = io.StringIO()
        fieldnames = [
            "canonical_paper_id",
            "title",
            "year",
            "journal",
            "oa_status",
            "audit_score",
            "audit_flags",
            "claim_count",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "canonical_paper_id": row.get("canonical_paper_id") or row.get("paper_id"),
                    "title": row.get("title"),
                    "year": row.get("year"),
                    "journal": row.get("journal"),
                    "oa_status": row.get("oa_status"),
                    "audit_score": row.get("audit_score"),
                    "audit_flags": ";".join(row.get("audit_flags") or []),
                    "claim_count": len(row.get("claims") or []),
                }
            )
        return PlainTextResponse(output.getvalue(), media_type="text/csv")

    raise HTTPException(status_code=400, detail="unsupported format")

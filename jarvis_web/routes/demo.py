"""Public demo API endpoints for landing page integration.

These endpoints are intentionally lightweight and do not require auth so that
the static landing page can execute end-to-end demos against a deployed API.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jarvis_core.citation import classify_citation_stance, extract_citation_contexts
from jarvis_core.contradiction import detect_contradiction
from jarvis_core.evidence import EVIDENCE_LEVEL_DESCRIPTIONS_EN, grade_evidence

router = APIRouter(prefix="/api/demo", tags=["demo"])

_PVALUE_PATTERN = re.compile(r"p\s*[<>=]\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
_AUTHOR_YEAR_PATTERN = re.compile(r"([A-Z][a-z]+(?:\s+et\s+al\.)?),?\s*(\d{4})")


def _envelope_ok(data: Any) -> dict[str, Any]:
    return {"status": "ok", "data": data, "errors": []}


def _quality_rating(level: str) -> str:
    if level in {"1a", "1b", "1c"}:
        return "High"
    if level in {"2a", "2b", "2c"}:
        return "Moderate"
    return "Low"


def _format_stance(stance: str) -> str:
    mapping = {
        "support": "Support",
        "contrast": "Contrast",
        "mention": "Mention",
        "extend": "Extend",
        "compare": "Compare",
        "unknown": "Unknown",
    }
    return mapping.get(stance.lower(), "Unknown")


def _extract_author_year(marker: str | None) -> tuple[str, str]:
    if not marker:
        return "Unknown", ""
    match = _AUTHOR_YEAR_PATTERN.search(marker)
    if match:
        return match.group(1), match.group(2)
    return marker, ""


def _statistical_conflict(claim_a: str, claim_b: str) -> tuple[bool, float, str]:
    match_a = _PVALUE_PATTERN.search(claim_a)
    match_b = _PVALUE_PATTERN.search(claim_b)
    if not match_a or not match_b:
        return False, 0.0, ""

    p_a = float(match_a.group(1))
    p_b = float(match_b.group(1))
    conflict = (p_a < 0.05 <= p_b) or (p_b < 0.05 <= p_a)
    if not conflict:
        return False, 0.0, ""

    return (
        True,
        92.0,
        "One claim is statistically significant while the other is not.",
    )


class EvidenceGradeRequest(BaseModel):
    title: str = Field(default="", max_length=400)
    abstract: str = Field(default="", max_length=10000)
    full_text: str = Field(default="", max_length=20000)


class CitationAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    paper_id: str = Field(default="landing-demo", max_length=120)


class ContradictionDetectRequest(BaseModel):
    claim_a: str = Field(min_length=1, max_length=4000)
    claim_b: str = Field(min_length=1, max_length=4000)


@router.get("/health")
async def demo_health() -> dict[str, Any]:
    """Health endpoint for landing page API connectivity checks."""
    return _envelope_ok({"service": "demo-api", "ready": True})


@router.post("/evidence/grade")
async def demo_grade_evidence(request: EvidenceGradeRequest) -> dict[str, Any]:
    """Grade evidence level with deterministic rule-first behavior."""
    title = request.title.strip()
    abstract = request.abstract.strip()
    full_text = request.full_text.strip()
    if not title and not abstract and not full_text:
        raise HTTPException(status_code=400, detail="title, abstract, or full_text is required")

    grade = grade_evidence(
        title=title,
        abstract=abstract,
        full_text=full_text,
        use_llm=False,
    )
    level = grade.level.value
    confidence_pct = round(max(0.0, min(1.0, float(grade.confidence))) * 100, 1)

    data = {
        "level": level,
        "description": EVIDENCE_LEVEL_DESCRIPTIONS_EN.get(level, "Unknown evidence level"),
        "confidence": confidence_pct,
        "quality_rating": _quality_rating(level),
        "classifier_source": grade.classifier_source,
        "source": "api",
    }
    return _envelope_ok(data)


@router.post("/citation/analyze")
async def demo_analyze_citation(request: CitationAnalyzeRequest) -> dict[str, Any]:
    """Extract citation contexts and classify stance."""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    contexts = extract_citation_contexts(
        text=text,
        paper_id=request.paper_id,
        reference_map=None,
        context_window=1,
    )

    citations = []
    for idx, context in enumerate(contexts, 1):
        stance_result = classify_citation_stance(context.get_full_context())
        author, year = _extract_author_year(context.citation_marker)
        citations.append(
            {
                "id": f"citation-{idx}",
                "author": author,
                "year": year,
                "stance": _format_stance(stance_result.stance.value),
                "context": context.get_full_context().strip() or context.citation_text.strip(),
                "confidence": round(max(0.0, min(1.0, float(stance_result.confidence))) * 100, 1),
                "evidence": stance_result.evidence,
            }
        )

    summary = {
        "total": len(citations),
        "support": sum(1 for item in citations if item["stance"] == "Support"),
        "contrast": sum(1 for item in citations if item["stance"] == "Contrast"),
        "mention": sum(1 for item in citations if item["stance"] == "Mention"),
    }
    return _envelope_ok({"citations": citations, "summary": summary, "source": "api"})


@router.post("/contradiction/detect")
async def demo_detect_contradiction(request: ContradictionDetectRequest) -> dict[str, Any]:
    """Detect contradiction between two claims."""
    claim_a = request.claim_a.strip()
    claim_b = request.claim_b.strip()
    if not claim_a or not claim_b:
        raise HTTPException(status_code=400, detail="Both claim_a and claim_b are required")

    contradictions = detect_contradiction([claim_a, claim_b])

    is_contradictory = False
    confidence = 15.0
    contradiction_type = "None"
    explanation = "No significant contradictions detected between the claims."

    if contradictions:
        top = max(contradictions, key=lambda item: item.confidence)
        is_contradictory = True
        confidence = round(max(0.0, min(1.0, float(top.confidence))) * 100, 1)
        contradiction_type = "Semantic"
        explanation = top.reason

    has_stats_conflict, stats_confidence, stats_explanation = _statistical_conflict(
        claim_a, claim_b
    )
    if has_stats_conflict and stats_confidence >= confidence:
        is_contradictory = True
        confidence = stats_confidence
        contradiction_type = "Statistical"
        explanation = stats_explanation

    data = {
        "isContradictory": is_contradictory,
        "confidence": confidence,
        "contradictionType": contradiction_type,
        "explanation": explanation,
        "claimA": claim_a,
        "claimB": claim_b,
        "source": "api",
    }
    return _envelope_ok(data)

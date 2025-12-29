"""Paper quality scoring and tiering."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class ScoreResult:
    score: float
    tier: str
    breakdown: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "tier": self.tier,
            "breakdown": self.breakdown,
        }


def score_paper(
    paper: Dict[str, Any],
    claims: List[Dict[str, Any]],
    query: str = "",
    domain: str = "",
) -> ScoreResult:
    transparency = _score_transparency(paper, claims)
    reliability = _score_reliability(paper)
    relevance = _score_relevance(paper, query, domain)
    evidence = _score_evidence_strength(claims)

    total = transparency + reliability + relevance + evidence
    tier = _tier(total)
    return ScoreResult(
        score=round(total, 2),
        tier=tier,
        breakdown={
            "transparency": transparency,
            "reliability": reliability,
            "relevance": relevance,
            "evidence": evidence,
        },
    )


def _score_transparency(paper: Dict[str, Any], claims: List[Dict[str, Any]]) -> float:
    score = 0.0
    oa_status = paper.get("oa_status")
    if oa_status and oa_status != "closed":
        score += 10.0
    if any(claim.get("claim_type") == "method" for claim in claims):
        score += 10.0
    if any(claim.get("claim_type") == "result" for claim in claims):
        score += 10.0
    return min(score, 30.0)


def _score_reliability(paper: Dict[str, Any]) -> float:
    score = 0.0
    if paper.get("journal"):
        score += 10.0
    year = int(paper.get("year") or 0)
    current_year = datetime.utcnow().year
    if year > 0:
        score += 5.0
        if current_year - year <= 5:
            score += 10.0
    return min(score, 25.0)


def _score_relevance(paper: Dict[str, Any], query: str, domain: str) -> float:
    score = 0.0
    haystack = " ".join([paper.get("title") or "", paper.get("abstract") or ""]).lower()
    if query:
        q = query.lower()
        if q in haystack:
            score += 15.0
        else:
            score += 5.0
    if domain:
        d = domain.lower()
        if d in haystack:
            score += 10.0
    return min(score, 25.0)


def _score_evidence_strength(claims: List[Dict[str, Any]]) -> float:
    if not claims:
        return 0.0
    avg = 0.0
    weak_count = 0
    for claim in claims:
        evidence = claim.get("evidence") or []
        if not evidence:
            weak_count += 1
            continue
        avg += sum(item.get("score", 0.0) for item in evidence) / max(len(evidence), 1)
        if any(item.get("score", 0.0) < 0.4 for item in evidence):
            weak_count += 1
    avg_score = avg / len(claims)
    score = avg_score * 20.0
    if weak_count:
        score -= min(10.0, weak_count * 2.0)
    return max(0.0, min(score, 20.0))


def _tier(score: float) -> str:
    if score >= 90:
        return "S"
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    return "C"

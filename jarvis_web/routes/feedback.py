"""Feedback Intelligence API routes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from jarvis_web.auth import verify_token
from jarvis_core.feedback.collector import FeedbackCollector
from jarvis_core.feedback.feature_extractor import FeedbackFeatureExtractor
from jarvis_core.feedback.history_store import FeedbackHistoryStore
from jarvis_core.feedback.risk_model import FeedbackRiskModel
from jarvis_core.feedback.suggestion_engine import SuggestionEngine


router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackHistoryRequest(BaseModel):
    text: str
    source: str = "email"
    reviewer: str = "unknown"
    document_type: str = "draft"
    date: Optional[str] = None


class FeedbackAnalyzeRequest(BaseModel):
    text: str
    document_type: str = "draft"
    section: str = "unknown"


def _analyze_text(text: str, document_type: str, section: str) -> dict:
    extractor = FeedbackFeatureExtractor()
    history = FeedbackHistoryStore().list_entries(limit=200)
    risk_model = FeedbackRiskModel()
    suggestion_engine = SuggestionEngine(history)

    items = []
    for record in extractor.extract(text, section=section):
        risk = risk_model.score(record.features, history, section=record.section)
        top_categories = [c["category"] for c in risk["top_categories"]]
        suggestions = suggestion_engine.suggest(record.text, top_categories)
        items.append({
            "location": record.location,
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "top_categories": risk["top_categories"],
            "reasons": risk["reasons"],
            "suggestions": suggestions,
        })

    summary = {
        "high": sum(1 for i in items if i["risk_level"] == "high"),
        "medium": sum(1 for i in items if i["risk_level"] == "medium"),
        "low": sum(1 for i in items if i["risk_level"] == "low"),
        "top_categories": _top_categories(items),
    }
    ready_high_limit = risk_model.ready_threshold()
    summary["ready_to_submit"] = summary["high"] <= 0
    summary["ready_with_risk"] = 0 < summary["high"] <= ready_high_limit

    return {
        "document_type": document_type,
        "summary": summary,
        "items": items,
    }


def _top_categories(items: List[dict]) -> List[str]:
    tally = {}
    for item in items:
        for category in item["top_categories"]:
            key = category["category"]
            tally[key] = tally.get(key, 0) + category["prob"]
    return [k for k, _ in sorted(tally.items(), key=lambda kv: kv[1], reverse=True)[:3]]


@router.post("/history")
async def add_feedback_history(request: FeedbackHistoryRequest, _: bool = Depends(verify_token)):
    collector = FeedbackCollector()
    entries = collector.parse_text(
        request.text,
        source=request.source,
        reviewer=request.reviewer,
        document_type=request.document_type,
        date=request.date,
    )
    collector.save_entries(entries)
    return {"added": len(entries)}


@router.get("/history")
async def list_feedback_history(limit: int = 50, _: bool = Depends(verify_token)):
    store = FeedbackHistoryStore()
    entries = store.list_entries(limit=limit)
    return {"entries": [e.to_dict() for e in entries]}


@router.post("/analyze")
async def analyze_feedback(request: FeedbackAnalyzeRequest, _: bool = Depends(verify_token)):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    return _analyze_text(request.text, request.document_type, request.section)


@router.get("/latest")
async def latest_feedback(_: bool = Depends(verify_token)):
    runs_dir = Path("logs/runs")
    if not runs_dir.exists():
        return {"summary": None, "items": []}
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
    for run_dir in run_dirs:
        feedback_path = run_dir / "feedback_risk.json"
        if feedback_path.exists():
            with open(feedback_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return {"summary": None, "items": []}

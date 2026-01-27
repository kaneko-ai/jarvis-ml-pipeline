"""Feedback API (Phase 36).

Endpoints for submitting user feedback.
"""

from __future__ import annotations

import logging
from typing import Dict, Any
from pathlib import Path

# Assuming fastapi is used based on project context
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from jarvis_core.feedback.store import FeedbackStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


# Simple dependency injection
def get_store():
    # TODO: Configure path via settings
    return FeedbackStore(Path("data/feedback"))


class FeedbackRequest(BaseModel):
    query_id: str
    doc_id: str
    rating: int
    metadata: Dict[str, Any] = {}


@router.post("/")
async def submit_feedback(req: FeedbackRequest, store: FeedbackStore = Depends(get_store)):
    """Submit relevance feedback."""
    try:
        store.log_feedback(
            query_id=req.query_id, doc_id=req.doc_id, rating=req.rating, metadata=req.metadata
        )
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Feedback API error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

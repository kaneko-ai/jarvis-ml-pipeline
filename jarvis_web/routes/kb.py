"""KB API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import os

from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter(prefix="/api/kb", tags=["kb"])

KB_ROOT = Path("data/kb")


def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify authorization token (local copy to avoid circular import)."""
    expected = os.environ.get("JARVIS_WEB_TOKEN", "")
    if not expected:
        return True
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


def _load_index() -> dict:
    path = KB_ROOT / "index.json"
    if not path.exists():
        return {"papers": {}, "topics": {}, "runs": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"papers": {}, "topics": {}, "runs": {}}


def _read_note(path: Path) -> str:
    if not path.exists():
        raise HTTPException(status_code=404, detail="Note not found")
    return path.read_text(encoding="utf-8")


def _safe_topic_name(topic: str) -> str:
    return topic.replace("/", "_")


@router.get("/status")
async def kb_status(_: bool = Depends(verify_token)):
    """Return KB status summary."""
    index = _load_index()
    papers = index.get("papers", {})
    topics = index.get("topics", {})
    runs = index.get("runs", {})
    last_updated: Optional[str] = None
    for entry in list(papers.values()) + list(topics.values()) + list(runs.values()):
        updated_at = entry.get("updated_at")
        if updated_at and (last_updated is None or updated_at > last_updated):
            last_updated = updated_at
    return {
        "papers": len(papers),
        "topics": len(topics),
        "runs": len(runs),
        "last_updated": last_updated,
        "topic_list": sorted(topics.keys()),
    }


@router.get("/topic/{topic}")
async def get_topic(topic: str, _: bool = Depends(verify_token)):
    """Fetch topic note contents."""
    safe_topic = _safe_topic_name(topic)
    path = KB_ROOT / "notes" / "topics" / f"{safe_topic}.md"
    content = _read_note(path)
    return {"topic": topic, "content": content}


@router.get("/paper/{pmid}")
async def get_paper(pmid: str, _: bool = Depends(verify_token)):
    """Fetch paper note contents."""
    path = KB_ROOT / "notes" / "papers" / f"PMID_{pmid}.md"
    content = _read_note(path)
    return {"pmid": pmid, "content": content}

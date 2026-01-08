"""Saved query endpoints."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse


router = APIRouter()


def _store_path() -> Path:
    path = Path("data/index/v2/saved_queries.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    return path


def _load_queries() -> List[Dict[str, Any]]:
    path = _store_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_queries(queries: List[Dict[str, Any]]) -> None:
    path = _store_path()
    path.write_text(json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/api/queries")
async def list_queries():
    return JSONResponse({"items": _load_queries()}, status_code=200)


@router.post("/api/queries")
async def create_query(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name")
    query_payload = payload.get("payload")
    if not name or not query_payload:
        raise HTTPException(status_code=400, detail="name and payload are required")
    queries = _load_queries()
    entry = {"id": str(uuid.uuid4()), "name": name, "payload": query_payload}
    queries.append(entry)
    _save_queries(queries)
    return JSONResponse(entry, status_code=201)


@router.delete("/api/queries/{query_id}")
async def delete_query(query_id: str):
    queries = _load_queries()
    updated = [item for item in queries if item.get("id") != query_id]
    if len(updated) == len(queries):
        raise HTTPException(status_code=404, detail="query not found")
    _save_queries(updated)
    return JSONResponse({"status": "deleted"}, status_code=200)

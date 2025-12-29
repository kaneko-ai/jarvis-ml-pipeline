"""Search v2 API endpoints."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse, PlainTextResponse

from jarvis_core.retrieval.export import export_csv, export_json, export_markdown
from jarvis_core.retrieval.hybrid_search import HybridSearchEngine


router = APIRouter()


@router.post("/api/search/v2")
async def search_v2(payload: Dict[str, Any] = Body(...)):
    query = payload.get("query", "")
    mode = payload.get("mode", "hybrid")
    top_k = int(payload.get("top_k", 20))
    filters = payload.get("filters", {}) or {}
    engine = HybridSearchEngine()
    if not engine.chunk_map:
        return JSONResponse(
            {"took_ms": 0, "total_candidates": 0, "results": [], "error": "index_missing"}, status_code=200
        )
    try:
        result = engine.search(query=query, filters=filters, top_k=top_k, mode=mode)
    except Exception as exc:
        return JSONResponse(
            {"took_ms": 0, "total_candidates": 0, "results": [], "error": str(exc)}, status_code=200
        )
    return JSONResponse(result.to_dict(), status_code=200)


@router.post("/api/search/v2/export")
async def export_search_v2(payload: Dict[str, Any] = Body(...)):
    query = payload.get("query", "")
    mode = payload.get("mode", "hybrid")
    top_k = int(payload.get("top_k", 20))
    filters = payload.get("filters", {}) or {}
    export_format = payload.get("format", "json")
    engine = HybridSearchEngine()
    if not engine.chunk_map:
        return JSONResponse(
            {"took_ms": 0, "total_candidates": 0, "results": [], "error": "index_missing"}, status_code=200
        )
    try:
        result = engine.search(query=query, filters=filters, top_k=top_k, mode=mode)
    except Exception as exc:
        return JSONResponse(
            {"took_ms": 0, "total_candidates": 0, "results": [], "error": str(exc)}, status_code=200
        )
    if export_format == "json":
        payload_text = export_json(result.results)
        return PlainTextResponse(payload_text, media_type="application/json")
    if export_format == "md":
        payload_text = export_markdown(result.results)
        return PlainTextResponse(payload_text, media_type="text/markdown")
    if export_format == "csv":
        payload_text = export_csv(result.results)
        return PlainTextResponse(payload_text, media_type="text/csv")
    return JSONResponse({"detail": "export format not implemented"}, status_code=501)

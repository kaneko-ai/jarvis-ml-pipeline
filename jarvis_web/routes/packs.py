"""Weekly pack API routes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse

from jarvis_core.kb.weekly_pack import generate_weekly_pack

router = APIRouter(prefix="/api/packs", tags=["packs"])

PACKS_ROOT = Path("data/packs")


def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    expected = os.environ.get("JARVIS_WEB_TOKEN", "")
    if not expected:
        return True
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


def _list_weekly_packs() -> list[dict]:
    weekly_root = PACKS_ROOT / "weekly"
    if not weekly_root.exists():
        return []
    packs = []
    for path in sorted(weekly_root.iterdir()):
        if not path.is_dir():
            continue
        metadata_path = path / "metadata.json"
        metadata = {}
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metadata = {}
        packs.append(
            {
                "id": path.name,
                "type": "weekly",
                "path": str(path),
                "metadata": metadata,
            }
        )
    return packs


def _resolve_pack_path(pack_id: str) -> Path:
    safe_id = pack_id.replace("..", "").strip("/")
    pack_path = PACKS_ROOT / "weekly" / safe_id / "weekly_pack.zip"
    return pack_path


@router.get("")
async def list_packs(_: bool = Depends(verify_token)):
    return {"packs": _list_weekly_packs()}


@router.get("/{pack_id}/download")
async def download_pack(pack_id: str, _: bool = Depends(verify_token)):
    pack_path = _resolve_pack_path(pack_id)
    if not pack_path.exists():
        raise HTTPException(status_code=404, detail="Pack not found")
    return FileResponse(pack_path, filename=pack_path.name)


@router.post("/generate")
async def generate_pack(_: bool = Depends(verify_token)):
    try:
        pack_path = generate_weekly_pack()
    except Exception as exc:  # pragma: no cover - guard
        raise HTTPException(status_code=503, detail=f"Pack generation failed: {exc}")
    return {"status": "generated", "path": str(pack_path)}

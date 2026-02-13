"""Stage cache utilities for ops_extract resume behavior."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import OPS_EXTRACT_SCHEMA_VERSION

STAGE_CACHE_VERSION = "ops_extract_stage_cache_v1"


def _now_iso() -> str:
    fixed = os.getenv("JARVIS_OPS_EXTRACT_FIXED_TIME")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).isoformat()


def _sha256_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_input_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_stage_cache(path: Path) -> dict[str, Any]:
    base = {
        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
        "version": STAGE_CACHE_VERSION,
        "stages": {},
    }
    if not path.exists():
        return base
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict):
            return base
        if not isinstance(payload.get("stages"), dict):
            payload["stages"] = {}
        if not payload.get("schema_version"):
            payload["schema_version"] = OPS_EXTRACT_SCHEMA_VERSION
        if not payload.get("version"):
            payload["version"] = STAGE_CACHE_VERSION
        return payload
    except Exception:
        return base


def save_stage_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def stage_outputs_from_paths(paths: list[Path], run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        try:
            rel = path.relative_to(run_dir).as_posix()
        except Exception:
            rel = str(path)
        rows.append({"path": rel, "sha256": _sha256_path(path)})
    return rows


def cache_outputs_match(run_dir: Path, outputs: list[dict[str, Any]]) -> bool:
    for item in outputs:
        rel = str(item.get("path", "")).strip()
        if not rel:
            return False
        path = run_dir / rel
        expected = item.get("sha256")
        if expected is None:
            if not path.exists():
                return False
            continue
        actual = _sha256_path(path)
        if actual != expected:
            return False
    return True


def update_stage_cache_entry(
    cache_payload: dict[str, Any],
    *,
    stage_id: str,
    input_hash: str,
    outputs: list[dict[str, Any]],
    status: str,
) -> None:
    stages = cache_payload.setdefault("stages", {})
    stages[stage_id] = {
        "input_hash": input_hash,
        "outputs": outputs,
        "status": status,
        "updated_at": _now_iso(),
    }

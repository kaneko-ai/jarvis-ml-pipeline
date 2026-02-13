"""Manifest writer for ops_extract mode."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .contracts import OPS_EXTRACT_SCHEMA_VERSION, OPS_EXTRACT_VERSION


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_input_entries(paths: Iterable[Path], source: str = "local") -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for p in paths:
        if not p.exists():
            entries.append(
                {
                    "path": str(p),
                    "size": None,
                    "sha256": None,
                    "source": source,
                    "exists": False,
                }
            )
            continue
        entries.append(
            {
                "path": str(p),
                "size": p.stat().st_size,
                "sha256": _sha256(p),
                "source": source,
                "exists": True,
            }
        )
    return entries


def collect_output_entries(
    run_dir: Path,
    *,
    exclude_relpaths: set[str] | None = None,
) -> list[dict[str, Any]]:
    exclude_relpaths = exclude_relpaths or set()
    entries: list[dict[str, Any]] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(run_dir).as_posix()
        if rel in exclude_relpaths:
            continue
        entries.append(
            {
                "path": rel,
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return entries


def create_manifest_payload(
    *,
    run_id: str,
    project: str,
    created_at: str,
    finished_at: str,
    status: str,
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    extract: dict[str, Any],
    ops: dict[str, Any],
    committed: bool = True,
    committed_local: bool = True,
    committed_drive: bool = False,
    schema_version: str = OPS_EXTRACT_SCHEMA_VERSION,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "run_id": run_id,
        "project": project,
        "created_at": created_at,
        "finished_at": finished_at,
        "status": status,
        "inputs": inputs,
        "outputs": outputs,
        "extract": extract,
        "ops": ops,
        "committed": committed,
        "committed_local": committed_local,
        "committed_drive": committed_drive,
        "version": OPS_EXTRACT_VERSION,
    }


def write_manifest(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

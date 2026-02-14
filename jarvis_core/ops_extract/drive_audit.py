"""Post-sync Drive audit utilities for ops_extract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import OPS_EXTRACT_SCHEMA_VERSION
from .drive_client import DriveResumableClient


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _md5(path: Path) -> str:
    import hashlib

    digest = hashlib.md5(usedforsecurity=False)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_folder(item: dict[str, Any]) -> bool:
    mime_type = str(item.get("mimeType", "")).strip().lower()
    return mime_type == "application/vnd.google-apps.folder" or bool(item.get("folder"))


def _collect_remote_entries(
    client: DriveResumableClient,
    root_folder_id: str,
) -> dict[str, dict[str, Any]]:
    remote_files: dict[str, dict[str, Any]] = {}
    stack: list[tuple[str, str]] = [(root_folder_id, "")]
    visited: set[str] = set()
    while stack:
        parent_id, prefix = stack.pop()
        if parent_id in visited:
            continue
        visited.add(parent_id)
        children = client.list_children(
            parent_id=parent_id,
            q=None,
            fields="files(id,name,mimeType,size,md5Checksum,modifiedTime)",
        )
        for child in children:
            if not isinstance(child, dict):
                continue
            name = str(child.get("name", "")).strip()
            if not name:
                continue
            rel = f"{prefix}/{name}" if prefix else name
            if _is_folder(child):
                child_id = str(child.get("id", "")).strip()
                if child_id:
                    stack.append((child_id, rel))
                continue
            remote_files[rel] = child
    return remote_files


def audit_manifest_vs_drive(
    run_dir: Path,
    client: DriveResumableClient,
    folder_id: str,
) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest_not_found:{manifest_path}")
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest_payload, dict):
        raise RuntimeError("manifest_payload_invalid")

    outputs = manifest_payload.get("outputs", [])
    if not isinstance(outputs, list):
        outputs = []
    remote_entries = _collect_remote_entries(client, folder_id)

    missing: list[str] = []
    mismatch_size: list[str] = []
    mismatch_md5: list[str] = []
    remote_no_md5: list[str] = []
    metadata_fetch_errors: list[str] = []
    checked_paths: list[str] = []

    for row in outputs:
        if not isinstance(row, dict):
            continue
        rel = str(row.get("path", "")).strip()
        if not rel:
            continue
        checked_paths.append(rel)
        remote = remote_entries.get(rel)
        if remote is None:
            missing.append(rel)
            continue
        remote_meta = dict(remote)
        remote_id = str(remote_meta.get("id", "")).strip()
        if remote_id:
            try:
                fetched = client.get_file_metadata(
                    remote_id,
                    fields="id,size,md5Checksum,modifiedTime,name",
                )
                if isinstance(fetched, dict) and fetched:
                    remote_meta.update(fetched)
            except Exception as exc:
                metadata_fetch_errors.append(f"{rel}:{exc}")

        expected_size = row.get("size")
        try:
            if expected_size is not None and int(remote_meta.get("size", -1)) != int(expected_size):
                mismatch_size.append(rel)
        except Exception:
            mismatch_size.append(rel)

        remote_md5 = str(remote_meta.get("md5Checksum", "")).strip().lower()
        local_path = run_dir / rel
        expected_md5 = (
            _md5(local_path).lower() if local_path.exists() and local_path.is_file() else ""
        )
        if remote_md5:
            if expected_md5 and remote_md5 != expected_md5:
                mismatch_md5.append(rel)
        else:
            remote_no_md5.append(rel)

    report = {
        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "folder_id": folder_id,
        "checked_count": len(checked_paths),
        "missing": sorted(set(missing)),
        "mismatch_size": sorted(set(mismatch_size)),
        "mismatch_md5": sorted(set(mismatch_md5)),
        "remote_no_md5": sorted(set(remote_no_md5)),
        "metadata_fetch_errors": sorted(set(metadata_fetch_errors)),
        "ok": not (missing or mismatch_size or mismatch_md5),
    }
    out_path = run_dir / "drive_audit.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report

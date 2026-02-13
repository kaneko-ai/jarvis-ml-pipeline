"""Post-run Drive sync (Tier0/Tier1, resumable state)."""

from __future__ import annotations

import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis_core.integrations.additional import GoogleDriveConfig, GoogleDriveExporter

SYNC_STATE_VERSION = "ops_extract_sync_v1"


def _sha256_bytes(raw: bytes) -> str:
    import hashlib

    return hashlib.sha256(raw).hexdigest()


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_sync_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _read_sync_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


def _target_files_from_manifest(run_dir: Path) -> list[Path]:
    tier_candidates = [
        "input.json",
        "run_config.json",
        "papers.jsonl",
        "claims.jsonl",
        "evidence.jsonl",
        "scores.json",
        "result.json",
        "eval_summary.json",
        "warnings.jsonl",
        "report.md",
        "run_metadata.json",
        "metrics.json",
        "warnings.json",
        "failure_analysis.json",
        "ingestion/text.md",
        "ingestion/text_source.json",
        "ocr/ocr_meta.json",
        "events.jsonl",
        "cost_report.json",
        "manifest.json",
    ]
    files = [run_dir / rel for rel in tier_candidates if (run_dir / rel).exists()]
    files.sort(key=lambda p: (p.name == "manifest.json", p.relative_to(run_dir).as_posix()))
    return files


def _build_manifest_override(path: Path, committed: bool) -> bytes:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise RuntimeError("manifest_payload_invalid")
    payload["committed"] = bool(committed)
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _upload_raw_json_payload(
    *,
    rel_path: str,
    raw: bytes,
    dry_run: bool,
    exporter: GoogleDriveExporter | None,
) -> dict[str, Any]:
    expected_sha = _sha256_bytes(raw)
    meta = {
        "path": rel_path,
        "size": len(raw),
        "sha256": expected_sha,
        "uploaded_at": _now(),
    }
    if dry_run:
        meta["file_id"] = f"dryrun_{rel_path.replace('/', '_')}"
        return meta

    if exporter is None:
        raise RuntimeError("Drive exporter unavailable")

    payload = {
        "path": rel_path,
        "encoding": "base64",
        "content_base64": base64.b64encode(raw).decode("ascii"),
    }
    file_id = exporter.export_json(filename=rel_path.replace("/", "__"), data=payload)
    if not file_id:
        raise RuntimeError(f"Drive upload failed: {rel_path}")
    meta["file_id"] = file_id
    return meta


def _upload_single_file(
    *,
    path: Path,
    run_dir: Path,
    dry_run: bool,
    exporter: GoogleDriveExporter | None,
) -> dict[str, Any]:
    rel = path.relative_to(run_dir).as_posix()
    raw = path.read_bytes()
    return _upload_raw_json_payload(
        rel_path=rel,
        raw=raw,
        dry_run=dry_run,
        exporter=exporter,
    )


def _upload_with_retry(
    *,
    path: Path,
    run_dir: Path,
    dry_run: bool,
    exporter: GoogleDriveExporter | None,
    verify_sha256: bool,
    max_retries: int,
    retry_backoff_sec: float,
) -> dict[str, Any]:
    expected_sha = _sha256(path)
    for attempt in range(max(0, max_retries) + 1):
        try:
            result = _upload_single_file(
                path=path,
                run_dir=run_dir,
                dry_run=dry_run,
                exporter=exporter,
            )
            if verify_sha256 and str(result.get("sha256")) != expected_sha:
                raise RuntimeError(f"sha256_mismatch:{path.name}")
            return result
        except Exception:
            if attempt >= max_retries:
                raise
            time.sleep(float(retry_backoff_sec) * (2**attempt))
    raise RuntimeError("upload_retry_unreachable")


def _normalize_uploaded_entries(entries: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for item in entries or []:
        path = str(item.get("path", "")).strip()
        if not path:
            continue
        normalized[path] = item
    return normalized


def _build_target_meta(files: list[Path], run_dir: Path) -> dict[str, dict[str, Any]]:
    payload: dict[str, dict[str, Any]] = {}
    for path in files:
        rel = path.relative_to(run_dir).as_posix()
        payload[rel] = {
            "path": rel,
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        }
    return payload


def sync_run_to_drive(
    *,
    run_dir: Path,
    enabled: bool,
    dry_run: bool,
    upload_workers: int,
    access_token: str | None = None,
    folder_id: str | None = None,
    retries: int = 0,
    max_retries: int = 3,
    retry_backoff_sec: float = 2.0,
    verify_sha256: bool = True,
) -> dict[str, Any]:
    sync_state_path = run_dir / "sync_state.json"

    if not enabled:
        payload = {
            "version": SYNC_STATE_VERSION,
            "state": "not_started",
            "uploaded_files": [],
            "pending_files": [],
            "failed_files": [],
            "retries": retries,
            "resume_count": 0,
            "last_error": "",
            "dry_run": dry_run,
            "manifest_committed_drive": False,
            "last_attempt_at": _now(),
        }
        _write_sync_state(sync_state_path, payload)
        return payload

    previous = _read_sync_state(sync_state_path)
    previous_uploaded = _normalize_uploaded_entries(previous.get("uploaded_files"))
    previous_failed = {
        str(item.get("path", "")).strip()
        for item in (previous.get("failed_files") or [])
        if str(item.get("path", "")).strip()
    }
    resume_count = 1 if previous_uploaded or previous.get("pending_files") or previous_failed else 0

    all_files = _target_files_from_manifest(run_dir)
    target_meta = _build_target_meta(all_files, run_dir)

    uploaded_map: dict[str, dict[str, Any]] = {}
    for rel, expected in target_meta.items():
        prev = previous_uploaded.get(rel)
        if not prev:
            continue
        if int(prev.get("size", -1)) == int(expected["size"]) and str(prev.get("sha256")) == str(
            expected["sha256"]
        ):
            uploaded_map[rel] = prev

    pending = [rel for rel in target_meta if rel not in uploaded_map]
    if previous_failed:
        narrowed = [rel for rel in pending if rel in previous_failed]
        if narrowed:
            pending = narrowed

    state = {
        "version": SYNC_STATE_VERSION,
        "state": "pending",
        "uploaded_files": list(uploaded_map.values()),
        "pending_files": [{"path": rel} for rel in pending],
        "failed_files": [],
        "retries": int(previous.get("retries", retries)),
        "resume_count": resume_count,
        "last_error": "",
        "dry_run": dry_run,
        "manifest_committed_drive": False,
        "last_attempt_at": _now(),
    }
    if not pending and bool(previous.get("manifest_committed_drive", False)):
        state["state"] = "committed"
        state["manifest_committed_drive"] = True
        state["pending_files"] = []
        state["committed_at"] = previous.get("committed_at") or _now()
        _write_sync_state(sync_state_path, state)
        return state

    _write_sync_state(sync_state_path, state)

    try:
        exporter = None
        if not dry_run:
            if not access_token:
                raise RuntimeError("Drive access token missing")
            exporter = GoogleDriveExporter(
                GoogleDriveConfig(access_token=access_token, folder_id=folder_id)
            )

        manifest_rel = "manifest.json"
        pending_non_manifest = [rel for rel in pending if rel != manifest_rel]

        state["state"] = "uploading"
        state["last_attempt_at"] = _now()
        _write_sync_state(sync_state_path, state)

        def do_upload(rel: str) -> dict[str, Any]:
            try:
                return _upload_with_retry(
                    path=run_dir / rel,
                    run_dir=run_dir,
                    dry_run=dry_run,
                    exporter=exporter,
                    verify_sha256=verify_sha256,
                    max_retries=max_retries,
                    retry_backoff_sec=retry_backoff_sec,
                )
            except Exception as exc:
                raise RuntimeError(f"{rel}:{exc}") from exc

        if pending_non_manifest:
            with ThreadPoolExecutor(max_workers=max(1, int(upload_workers))) as pool:
                future_map = {pool.submit(do_upload, rel): rel for rel in pending_non_manifest}
                for future in as_completed(future_map):
                    rel = future_map[future]
                    result = future.result()
                    uploaded_map[rel] = result

        state["state"] = "verifying"
        state["uploaded_files"] = sorted(uploaded_map.values(), key=lambda x: x.get("path", ""))
        state["pending_files"] = [{"path": rel} for rel in target_meta if rel not in uploaded_map]
        _write_sync_state(sync_state_path, state)

        required_non_manifest = [rel for rel in target_meta if rel != manifest_rel]
        missing_non_manifest = [rel for rel in required_non_manifest if rel not in uploaded_map]
        if missing_non_manifest:
            raise RuntimeError(f"verification_failed:missing_non_manifest={missing_non_manifest}")

        manifest_path = run_dir / manifest_rel
        if manifest_path.exists():
            manifest_raw_draft = _build_manifest_override(manifest_path, committed=False)
            manifest_meta_draft = _upload_raw_json_payload(
                rel_path=manifest_rel,
                raw=manifest_raw_draft,
                dry_run=dry_run,
                exporter=exporter,
            )
            if verify_sha256 and manifest_meta_draft.get("sha256") != _sha256_bytes(
                manifest_raw_draft
            ):
                raise RuntimeError("verification_failed:manifest_draft_sha256_mismatch")

            manifest_raw_final = _build_manifest_override(manifest_path, committed=True)
            manifest_meta_final = _upload_raw_json_payload(
                rel_path=manifest_rel,
                raw=manifest_raw_final,
                dry_run=dry_run,
                exporter=exporter,
            )
            if verify_sha256 and manifest_meta_final.get("sha256") != _sha256_bytes(
                manifest_raw_final
            ):
                raise RuntimeError("verification_failed:manifest_final_sha256_mismatch")
            uploaded_map[manifest_rel] = manifest_meta_final

        state["state"] = "committed"
        state["uploaded_files"] = sorted(uploaded_map.values(), key=lambda x: x.get("path", ""))
        state["pending_files"] = []
        state["failed_files"] = []
        state["manifest_committed_drive"] = True
        state["committed_at"] = _now()
        state["last_attempt_at"] = _now()
        _write_sync_state(sync_state_path, state)
        return state
    except Exception as exc:
        failed_rel = ""
        message = str(exc)
        if ":" in message and not message.startswith("verification_failed"):
            failed_rel = message.split(":", 1)[0].strip()

        remaining = [rel for rel in pending if rel not in uploaded_map]
        state["state"] = "failed"
        state["last_error"] = message
        state["retries"] = int(previous.get("retries", retries)) + 1
        state["uploaded_files"] = sorted(uploaded_map.values(), key=lambda x: x.get("path", ""))
        state["pending_files"] = [{"path": rel} for rel in remaining]
        state["failed_files"] = (
            [{"path": failed_rel, "error": message}]
            if failed_rel
            else [{"path": rel, "error": message} for rel in remaining[:1]]
        )
        state["manifest_committed_drive"] = False
        state["last_attempt_at"] = _now()
        _write_sync_state(sync_state_path, state)
        return state

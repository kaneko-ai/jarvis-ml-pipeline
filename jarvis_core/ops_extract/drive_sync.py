"""Post-run Drive sync (Tier0/Tier1, resumable state)."""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .contracts import OPS_EXTRACT_SCHEMA_VERSION, OPS_EXTRACT_SYNC_STATE_VERSION
from .drive_client import DriveResumableClient, DriveUploadError
from .security import redact_sensitive_text

SYNC_STATE_VERSION = OPS_EXTRACT_SYNC_STATE_VERSION


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


def _md5_bytes(raw: bytes) -> str:
    import hashlib

    return hashlib.md5(raw, usedforsecurity=False).hexdigest()


def _md5(path: Path) -> str:
    import hashlib

    h = hashlib.md5(usedforsecurity=False)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _now() -> str:
    fixed = os.getenv("JARVIS_OPS_EXTRACT_FIXED_TIME")
    if fixed:
        return fixed
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


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _fallback_target_files(run_dir: Path) -> list[Path]:
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
        "network_diagnosis.json",
        "trace.jsonl",
        "stage_cache.json",
        "ingestion/text.md",
        "ingestion/pdf_diagnosis.json",
        "ingestion/text_source.json",
        "ocr/ocr_meta.json",
        "events.jsonl",
        "cost_report.json",
        "manifest.json",
    ]
    files = [run_dir / rel for rel in tier_candidates if (run_dir / rel).exists()]
    files.sort(key=lambda p: (p.name == "manifest.json", p.relative_to(run_dir).as_posix()))
    return files


def _target_files_from_manifest(run_dir: Path) -> tuple[list[Path], bool]:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return _fallback_target_files(run_dir), True

    try:
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return _fallback_target_files(run_dir), True
    if not isinstance(manifest_payload, dict):
        return _fallback_target_files(run_dir), True

    files: list[Path] = []
    seen: set[str] = set()
    outputs = manifest_payload.get("outputs", [])
    if not isinstance(outputs, list) or len(outputs) == 0:
        return _fallback_target_files(run_dir), True

    for output in outputs:
        if not isinstance(output, dict):
            continue
        rel = str(output.get("path", "")).strip()
        if not rel or rel in seen:
            continue
        path = run_dir / rel
        if path.exists():
            files.append(path)
            seen.add(rel)

    if not files:
        return _fallback_target_files(run_dir), True

    files.append(manifest_path)
    files.sort(key=lambda p: (p.name == "manifest.json", p.relative_to(run_dir).as_posix()))
    return files, False


def _build_manifest_override(path: Path, committed: bool) -> bytes:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise RuntimeError("manifest_payload_invalid")
    payload["committed"] = bool(committed)
    payload["committed_local"] = bool(payload.get("committed_local", True))
    payload["committed_drive"] = bool(committed)
    payload["schema_version"] = str(payload.get("schema_version", OPS_EXTRACT_SCHEMA_VERSION))
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _upload_raw_json_payload(
    *,
    rel_path: str,
    raw: bytes,
    dry_run: bool,
    client: DriveResumableClient | None,
    folder_id: str | None,
    chunk_bytes: int,
    resume_token: str | None,
    session_uri: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    expected_sha = _sha256_bytes(raw)
    expected_md5 = _md5_bytes(raw)
    meta = {
        "path": rel_path,
        "size": len(raw),
        "sha256": expected_sha,
        "md5": expected_md5,
        "uploaded_at": _now(),
        "verified": True,
        "attempts": 1,
        "verification_warning": "",
    }
    if dry_run:
        meta["file_id"] = f"dryrun_{rel_path.replace('/', '_')}"
        meta["session_uri"] = ""
        return meta

    if client is None:
        raise RuntimeError("Drive client unavailable")

    upload_meta = client.upload_bytes(
        filename=filename or Path(rel_path).name,
        raw=raw,
        folder_id=folder_id,
        chunk_bytes=chunk_bytes,
        resume_token=resume_token,
        session_uri=session_uri,
    )
    meta["file_id"] = str(upload_meta.get("file_id", ""))
    meta["session_uri"] = str(upload_meta.get("session_uri", ""))
    meta["attempts"] = int(upload_meta.get("attempts", 1))
    return meta


def _verify_remote_integrity(
    *,
    client: DriveResumableClient,
    file_id: str,
    expected_size: int,
    expected_md5: str,
) -> str:
    try:
        metadata = client.get_file_metadata(
            file_id,
            fields="id,name,size,md5Checksum,modifiedTime,version",
        )
    except Exception:
        return "REMOTE_METADATA_UNAVAILABLE"
    remote_size_raw = metadata.get("size")
    if remote_size_raw is None:
        raise RuntimeError("verification_failed:remote_size_missing")
    remote_size = int(remote_size_raw)
    if remote_size != int(expected_size):
        raise RuntimeError(
            f"verification_failed:remote_size_mismatch:{remote_size}!={int(expected_size)}"
        )
    remote_md5 = str(metadata.get("md5Checksum", "")).strip().lower()
    if remote_md5:
        if remote_md5 != str(expected_md5).strip().lower():
            raise RuntimeError("verification_failed:remote_md5_mismatch")
        return ""
    return "REMOTE_CHECKSUM_UNAVAILABLE"


def _upload_single_file(
    *,
    path: Path,
    run_dir: Path,
    dry_run: bool,
    client: DriveResumableClient | None,
    folder_id: str | None,
    chunk_bytes: int,
    resume_token: str | None,
    session_uri: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    rel = path.relative_to(run_dir).as_posix()
    raw = path.read_bytes()
    return _upload_raw_json_payload(
        rel_path=rel,
        raw=raw,
        dry_run=dry_run,
        client=client,
        folder_id=folder_id,
        chunk_bytes=chunk_bytes,
        resume_token=resume_token,
        session_uri=session_uri,
        filename=filename or path.name,
    )


def _upload_with_retry(
    *,
    path: Path,
    run_dir: Path,
    dry_run: bool,
    client: DriveResumableClient | None,
    folder_id: str | None,
    chunk_bytes: int,
    resume_token: str | None,
    session_uri: str | None,
    verify_sha256: bool,
    max_retries: int,
    retry_backoff_sec: float,
    filename: str | None = None,
) -> dict[str, Any]:
    expected_sha = _sha256(path)
    expected_md5 = _md5(path)
    latest_session_uri = session_uri
    for attempt in range(max(0, max_retries) + 1):
        try:
            result = _upload_single_file(
                path=path,
                run_dir=run_dir,
                dry_run=dry_run,
                client=client,
                folder_id=folder_id,
                chunk_bytes=chunk_bytes,
                resume_token=resume_token,
                session_uri=latest_session_uri,
                filename=filename or path.name,
            )
            if verify_sha256 and str(result.get("sha256")) != expected_sha:
                raise RuntimeError(f"sha256_mismatch:{path.name}")
            verify_warning = ""
            if verify_sha256 and not dry_run and client is not None:
                verify_warning = _verify_remote_integrity(
                    client=client,
                    file_id=str(result.get("file_id", "")),
                    expected_size=path.stat().st_size,
                    expected_md5=expected_md5,
                )
            result["verification_warning"] = verify_warning
            result["verified"] = True
            result["attempts"] = max(int(result.get("attempts", 1)), attempt + 1)
            return result
        except Exception as exc:
            if isinstance(exc, DriveUploadError):
                message = str(exc).lower()
                if "missing_session_uri" in message:
                    latest_session_uri = None
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


def _normalize_uploaded_entry(item: dict[str, Any]) -> dict[str, Any]:
    row = dict(item)
    row["file_id"] = str(row.get("file_id", ""))
    row["session_uri"] = str(row.get("session_uri", ""))
    row["md5"] = str(row.get("md5", ""))
    row["verification_warning"] = str(row.get("verification_warning", ""))
    row["verified"] = bool(row.get("verified", False))
    row["attempts"] = int(row.get("attempts", 1))
    return row


def _build_target_meta(files: list[Path], run_dir: Path) -> dict[str, dict[str, Any]]:
    payload: dict[str, dict[str, Any]] = {}
    for path in files:
        rel = path.relative_to(run_dir).as_posix()
        payload[rel] = {
            "path": rel,
            "size": path.stat().st_size,
            "sha256": _sha256(path),
            "md5": _md5(path),
        }
    return payload


def _derive_drive_layout(run_dir: Path) -> tuple[str, str, str]:
    project = "default"
    run_id = run_dir.name
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    metadata_path = run_dir / "run_metadata.json"
    if metadata_path.exists():
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            project = str(payload.get("project", project) or project)
            run_id = str(payload.get("run_id", run_id) or run_id)
            finished_at = str(payload.get("finished_at", "")).strip()
            if len(finished_at) >= 7 and finished_at[4] == "-":
                month = finished_at[:7]
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return project, month, run_id
    return project, month, run_id


def _resolve_folder_ids_for_relpath(
    *,
    client: DriveResumableClient | None,
    dry_run: bool,
    root_folder_id: str | None,
    rel_path: str,
    folder_cache: dict[str, str | None],
) -> tuple[str | None, str]:
    filename = Path(rel_path).name
    parent_rel = Path(rel_path).parent.as_posix()
    if parent_rel in {"", "."}:
        return root_folder_id, filename
    if dry_run or client is None:
        return root_folder_id, filename
    parent_folder_id = root_folder_id
    key_acc = ""
    for part in parent_rel.split("/"):
        key_acc = f"{key_acc}/{part}" if key_acc else part
        cached = folder_cache.get(key_acc)
        if cached is not None or key_acc in folder_cache:
            parent_folder_id = cached
            continue
        try:
            folder_id = client.ensure_folder(name=part, parent_id=parent_folder_id)
        except Exception:
            return root_folder_id, filename
        folder_cache[key_acc] = folder_id
        parent_folder_id = folder_id
    return parent_folder_id, filename


def _has_public_permission(permissions: list[dict[str, Any]]) -> bool:
    for item in permissions:
        perm_type = str(item.get("type", "")).lower()
        role = str(item.get("role", "")).lower()
        if perm_type in {"anyone", "domain"} and role in {
            "reader",
            "writer",
            "commenter",
            "organizer",
        }:
            return True
    return False


def sync_run_to_drive(
    *,
    run_dir: Path,
    enabled: bool,
    dry_run: bool,
    upload_workers: int,
    access_token: str | None = None,
    folder_id: str | None = None,
    api_base_url: str | None = None,
    upload_base_url: str | None = None,
    chunk_bytes: int = 8 * 1024 * 1024,
    resume_token: str | None = None,
    retries: int = 0,
    max_retries: int = 3,
    retry_backoff_sec: float = 2.0,
    verify_sha256: bool = True,
    sync_lock_ttl_sec: int = 900,
    check_public_permissions: bool = True,
) -> dict[str, Any]:
    sync_state_path = run_dir / "sync_state.json"
    sync_lock_path = run_dir / ".sync_lock.json"

    if not enabled:
        payload = {
            "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
            "version": SYNC_STATE_VERSION,
            "state": "not_started",
            "uploaded_files": [],
            "pending_files": [],
            "failed_files": [],
            "warnings": [],
            "retries": retries,
            "resume_count": 0,
            "last_error": "",
            "dry_run": dry_run,
            "manifest_committed_drive": False,
            "remote_root_folder_id": "",
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

    all_files, manifest_fallback = _target_files_from_manifest(run_dir)
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
        failed_first = [rel for rel in pending if rel in previous_failed]
        non_failed = [rel for rel in pending if rel not in previous_failed]
        pending = failed_first + non_failed

    state = {
        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
        "version": SYNC_STATE_VERSION,
        "state": "pending",
        "uploaded_files": [_normalize_uploaded_entry(v) for v in uploaded_map.values()],
        "pending_files": [{"path": rel} for rel in pending],
        "failed_files": [],
        "warnings": list(previous.get("warnings", [])),
        "retries": int(previous.get("retries", retries)),
        "resume_count": resume_count,
        "last_error": "",
        "dry_run": dry_run,
        "manifest_committed_drive": False,
        "remote_root_folder_id": str(previous.get("remote_root_folder_id", "") or ""),
        "last_attempt_at": _now(),
    }
    if manifest_fallback:
        state["warnings"].append("MANIFEST_MISSING_FALLBACK")
    if not pending and bool(previous.get("manifest_committed_drive", False)):
        missing_uploaded_files = [rel for rel in target_meta if rel not in uploaded_map]
        if missing_uploaded_files:
            raise RuntimeError(
                f"verification_failed:missing_uploaded_files={missing_uploaded_files}"
            )

        state["state"] = "committed"
        state["manifest_committed_drive"] = True
        state["pending_files"] = []
        state["committed_at"] = previous.get("committed_at") or _now()
        state["remote_root_folder_id"] = str(previous.get("remote_root_folder_id", "") or "")
        _write_sync_state(sync_state_path, state)
        return state

    _write_sync_state(sync_state_path, state)

    lock_created = False
    now = datetime.now(timezone.utc)
    if not dry_run:
        existing_lock: dict[str, Any] = {}
        if sync_lock_path.exists():
            try:
                with open(sync_lock_path, encoding="utf-8") as f:
                    existing_lock = json.load(f)
            except Exception:
                existing_lock = {}
            created_at = _parse_iso(str(existing_lock.get("created_at", "")))
            ttl_sec = int(existing_lock.get("ttl_sec", sync_lock_ttl_sec) or sync_lock_ttl_sec)
            if created_at and now < created_at + timedelta(seconds=max(1, ttl_sec)):
                state["state"] = "deferred"
                state["last_error"] = "sync_lock_conflict"
                state["pending_files"] = [{"path": rel} for rel in pending]
                state["remote_root_folder_id"] = str(state.get("remote_root_folder_id", "") or "")
                state["last_attempt_at"] = _now()
                _write_sync_state(sync_state_path, state)
                return state
        with open(sync_lock_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "created_at": now.isoformat(),
                    "pid": os.getpid(),
                    "ttl_sec": max(1, int(sync_lock_ttl_sec)),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        lock_created = True

    try:
        client = None
        if not dry_run:
            if not access_token:
                raise RuntimeError("Drive access token missing")
            client = DriveResumableClient(
                access_token=access_token,
                api_base_url=api_base_url,
                upload_base_url=upload_base_url,
            )

        root_upload_folder_id = folder_id
        folder_cache: dict[str, str | None] = {"": root_upload_folder_id}
        if client is not None and not dry_run:
            project_name, run_month, run_name = _derive_drive_layout(run_dir)
            try:
                for part in ("Javis", "runs", project_name, run_month, run_name):
                    root_upload_folder_id = client.ensure_folder(
                        name=part,
                        parent_id=root_upload_folder_id,
                    )
                folder_cache[""] = root_upload_folder_id
            except Exception as exc:
                state["warnings"].append(
                    f"FOLDER_LAYOUT_FALLBACK:{redact_sensitive_text(str(exc))}"
                )
                root_upload_folder_id = folder_id
                folder_cache[""] = root_upload_folder_id
        state["remote_root_folder_id"] = str(root_upload_folder_id or "")

        if (
            client is not None
            and not dry_run
            and check_public_permissions
            and root_upload_folder_id
        ):
            try:
                permissions = client.list_permissions(str(root_upload_folder_id))
                if _has_public_permission(permissions):
                    raise RuntimeError("permissions_public_link_detected")
            except RuntimeError as exc:
                if "permissions_public_link_detected" in str(exc):
                    raise
                state["warnings"].append(
                    f"PERMISSIONS_CHECK_SKIPPED:{redact_sensitive_text(str(exc))}"
                )
            except Exception as exc:
                state["warnings"].append(
                    f"PERMISSIONS_CHECK_SKIPPED:{redact_sensitive_text(str(exc))}"
                )

        manifest_rel = "manifest.json"
        pending_non_manifest = [rel for rel in pending if rel != manifest_rel]

        state["state"] = "uploading"
        state["last_attempt_at"] = _now()
        _write_sync_state(sync_state_path, state)

        def do_upload(rel: str) -> dict[str, Any]:
            try:
                target_folder_id, target_filename = _resolve_folder_ids_for_relpath(
                    client=client,
                    dry_run=dry_run,
                    root_folder_id=root_upload_folder_id,
                    rel_path=rel,
                    folder_cache=folder_cache,
                )
                return _upload_with_retry(
                    path=run_dir / rel,
                    run_dir=run_dir,
                    dry_run=dry_run,
                    client=client,
                    folder_id=target_folder_id,
                    chunk_bytes=chunk_bytes,
                    resume_token=resume_token,
                    session_uri=str(previous_uploaded.get(rel, {}).get("session_uri", "")).strip()
                    or None,
                    verify_sha256=verify_sha256,
                    max_retries=max_retries,
                    retry_backoff_sec=retry_backoff_sec,
                    filename=target_filename,
                )
            except Exception as exc:
                raise RuntimeError(f"{rel}:{exc}") from exc

        if pending_non_manifest:
            with ThreadPoolExecutor(max_workers=max(1, int(upload_workers))) as pool:
                future_map = {pool.submit(do_upload, rel): rel for rel in pending_non_manifest}
                for future in as_completed(future_map):
                    rel = future_map[future]
                    result = future.result()
                    warning_code = str(result.get("verification_warning", "")).strip()
                    if warning_code:
                        state["warnings"].append(f"{rel}:{warning_code}")
                    uploaded_map[rel] = result

        state["state"] = "verifying"
        state["uploaded_files"] = sorted(
            [_normalize_uploaded_entry(v) for v in uploaded_map.values()],
            key=lambda x: x.get("path", ""),
        )
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
                client=client,
                folder_id=root_upload_folder_id,
                chunk_bytes=chunk_bytes,
                resume_token=resume_token,
                session_uri=str(
                    previous_uploaded.get(manifest_rel, {}).get("session_uri", "")
                ).strip()
                or None,
                filename="manifest.json",
            )
            if verify_sha256 and manifest_meta_draft.get("sha256") != _sha256_bytes(
                manifest_raw_draft
            ):
                raise RuntimeError("verification_failed:manifest_draft_sha256_mismatch")
            if verify_sha256 and not dry_run and client is not None:
                manifest_warning = _verify_remote_integrity(
                    client=client,
                    file_id=str(manifest_meta_draft.get("file_id", "")),
                    expected_size=len(manifest_raw_draft),
                    expected_md5=_md5_bytes(manifest_raw_draft),
                )
                if manifest_warning:
                    state["warnings"].append(f"{manifest_rel}:{manifest_warning}")

            manifest_raw_final = _build_manifest_override(manifest_path, committed=True)
            manifest_meta_final = _upload_raw_json_payload(
                rel_path=manifest_rel,
                raw=manifest_raw_final,
                dry_run=dry_run,
                client=client,
                folder_id=root_upload_folder_id,
                chunk_bytes=chunk_bytes,
                resume_token=resume_token,
                session_uri=None,
                filename="manifest.json",
            )
            if verify_sha256 and manifest_meta_final.get("sha256") != _sha256_bytes(
                manifest_raw_final
            ):
                raise RuntimeError("verification_failed:manifest_final_sha256_mismatch")
            if verify_sha256 and not dry_run and client is not None:
                manifest_warning = _verify_remote_integrity(
                    client=client,
                    file_id=str(manifest_meta_final.get("file_id", "")),
                    expected_size=len(manifest_raw_final),
                    expected_md5=_md5_bytes(manifest_raw_final),
                )
                if manifest_warning:
                    state["warnings"].append(f"{manifest_rel}:{manifest_warning}")
            uploaded_map[manifest_rel] = manifest_meta_final

        state["state"] = "committed"
        state["uploaded_files"] = sorted(
            [_normalize_uploaded_entry(v) for v in uploaded_map.values()],
            key=lambda x: x.get("path", ""),
        )
        state["pending_files"] = []
        state["failed_files"] = []
        state["manifest_committed_drive"] = True
        state["remote_root_folder_id"] = str(root_upload_folder_id or "")
        state["committed_at"] = _now()
        state["last_attempt_at"] = _now()
        _write_sync_state(sync_state_path, state)
        return state
    except Exception as exc:
        failed_rel = ""
        message = redact_sensitive_text(str(exc))
        if ":" in message and not message.startswith("verification_failed"):
            failed_rel = message.split(":", 1)[0].strip()

        remaining = [rel for rel in pending if rel not in uploaded_map]
        state["state"] = "failed"
        state["last_error"] = message
        state["retries"] = int(previous.get("retries", retries)) + 1
        state["uploaded_files"] = sorted(
            [_normalize_uploaded_entry(v) for v in uploaded_map.values()],
            key=lambda x: x.get("path", ""),
        )
        state["pending_files"] = [{"path": rel} for rel in remaining]
        state["failed_files"] = (
            [{"path": failed_rel, "error": message}]
            if failed_rel
            else [{"path": rel, "error": message} for rel in remaining[:1]]
        )
        state["manifest_committed_drive"] = False
        state["remote_root_folder_id"] = str(state.get("remote_root_folder_id", "") or "")
        state["last_attempt_at"] = _now()
        _write_sync_state(sync_state_path, state)
        return state
    finally:
        if lock_created:
            try:
                sync_lock_path.unlink(missing_ok=True)
            except OSError as exc:
                state.setdefault("warnings", [])
                state["warnings"].append(f"SYNC_LOCK_CLEANUP_FAILED:{type(exc).__name__}")

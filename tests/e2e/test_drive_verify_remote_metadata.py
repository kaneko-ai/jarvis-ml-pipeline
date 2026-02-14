from __future__ import annotations

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from jarvis_core.ops_extract.drive_sync import sync_run_to_drive


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _setup_run_dir(run_dir: Path) -> None:
    _write(run_dir / "result.json", "{}")
    _write(run_dir / "scores.json", "{}")
    _write(run_dir / "metrics.json", "{}")
    _write(
        run_dir / "manifest.json",
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"demo","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","inputs":[],"outputs":[],"extract":{"method":"pdf_text","needs_ocr":false,"needs_ocr_reason":"not_needed","total_chars":0,"chars_per_page_mean":0.0,"empty_page_ratio":0.0},"ops":{"retries":0,"resume_count":0,"sync_state":"not_started"},"committed":true,"committed_local":true,"committed_drive":false,"version":"ops_extract_v1"}',
    )


class _VerifyHandler(BaseHTTPRequestHandler):
    sessions: dict[str, dict[str, Any]] = {}
    files: dict[str, dict[str, Any]] = {}
    metadata_without_md5 = False

    def log_message(self, _format: str, *_args):  # pragma: no cover
        return

    def do_POST(self):
        if self.path != "/upload/resumable/start":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        sid = f"s{len(self.sessions) + 1}"
        self.sessions[sid] = {
            "name": str(payload.get("name", "unknown")),
            "total": int(payload.get("size", 0)),
            "data": bytearray(),
        }
        port = self.server.server_address[1]
        body = json.dumps({"session_uri": f"http://127.0.0.1:{port}/session/{sid}"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        if not self.path.startswith("/session/"):
            self.send_response(404)
            self.end_headers()
            return
        sid = self.path.split("/")[-1]
        session = self.sessions[sid]
        length = int(self.headers.get("Content-Length", "0"))
        chunk = self.rfile.read(length)
        content_range = str(self.headers.get("Content-Range", "bytes 0-0/0"))
        _, values = content_range.split(" ", 1)
        start_end, total = values.split("/")
        start, end = [int(x) for x in start_end.split("-")]
        total = int(total)
        data = session["data"]
        if len(data) < start:
            data.extend(b"\x00" * (start - len(data)))
        if len(data) == start:
            data.extend(chunk)
        else:
            data[start : start + len(chunk)] = chunk
        if end + 1 < total:
            self.send_response(308)
            self.send_header("Range", f"bytes=0-{end}")
            self.end_headers()
            return
        file_id = f"id_{sid}"
        raw = bytes(data)
        self.files[file_id] = {
            "id": file_id,
            "name": session["name"],
            "size": len(raw),
            "md5Checksum": hashlib.md5(raw).hexdigest(),
            "modifiedTime": "2026-02-14T00:00:00+00:00",
            "version": "1",
        }
        body = json.dumps({"file_id": file_id}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.path.startswith("/api/files/"):
            self.send_response(404)
            self.end_headers()
            return
        file_id = self.path.split("/api/files/")[-1].split("?")[0]
        payload = dict(self.files.get(file_id, {}))
        if self.metadata_without_md5:
            payload.pop("md5Checksum", None)
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _run_sync(tmp_path: Path, metadata_without_md5: bool) -> dict[str, Any]:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _setup_run_dir(run_dir)
    _VerifyHandler.sessions = {}
    _VerifyHandler.files = {}
    _VerifyHandler.metadata_without_md5 = metadata_without_md5
    server = ThreadingHTTPServer(("127.0.0.1", 0), _VerifyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        return sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            access_token="token",
            folder_id="folder",
            api_base_url=f"http://127.0.0.1:{port}/api",
            upload_base_url=f"http://127.0.0.1:{port}/upload",
            chunk_bytes=8,
            max_retries=1,
            retry_backoff_sec=0.0,
            verify_sha256=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_drive_remote_verify_with_md5(tmp_path: Path):
    state = _run_sync(tmp_path, metadata_without_md5=False)
    assert state["state"] == "committed"
    assert state["manifest_committed_drive"] is True


def test_drive_remote_verify_without_md5_fallback(tmp_path: Path):
    state = _run_sync(tmp_path, metadata_without_md5=True)
    assert state["state"] == "committed"
    warnings = state.get("warnings", [])
    assert any("REMOTE_CHECKSUM_UNAVAILABLE" in str(item) for item in warnings)


def test_drive_committed_protocol(tmp_path: Path):
    state = _run_sync(tmp_path, metadata_without_md5=False)
    assert state["state"] == "committed"
    assert state["manifest_committed_drive"] is True
    assert state["pending_files"] == []


def test_drive_idempotent_resync(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _setup_run_dir(run_dir)
    _VerifyHandler.sessions = {}
    _VerifyHandler.files = {}
    _VerifyHandler.metadata_without_md5 = False
    server = ThreadingHTTPServer(("127.0.0.1", 0), _VerifyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        first = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            access_token="token",
            folder_id="folder",
            api_base_url=f"http://127.0.0.1:{port}/api",
            upload_base_url=f"http://127.0.0.1:{port}/upload",
            chunk_bytes=8,
            max_retries=1,
            retry_backoff_sec=0.0,
            verify_sha256=True,
        )
        second = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            access_token="token",
            folder_id="folder",
            api_base_url=f"http://127.0.0.1:{port}/api",
            upload_base_url=f"http://127.0.0.1:{port}/upload",
            chunk_bytes=8,
            max_retries=1,
            retry_backoff_sec=0.0,
            verify_sha256=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert first["state"] == "committed"
    assert second["state"] == "committed"
    assert second["manifest_committed_drive"] is True

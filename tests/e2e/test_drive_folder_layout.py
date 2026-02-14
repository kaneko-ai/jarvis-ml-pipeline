from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from jarvis_core.ops_extract.drive_sync import sync_run_to_drive


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class _FolderLayoutHandler(BaseHTTPRequestHandler):
    sessions: dict[str, dict[str, Any]] = {}
    files: dict[str, dict[str, Any]] = {}
    folders: dict[tuple[str, str], str] = {}
    uploads: list[dict[str, str]] = []

    def log_message(self, _format: str, *_args):  # pragma: no cover
        return

    def do_POST(self):
        if self.path == "/api/folders/ensure":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            key = (str(payload.get("parent_id", "")), str(payload.get("name", "")))
            if key not in self.folders:
                self.folders[key] = f"fd_{len(self.folders)+1}"
            folder_id = self.folders[key]
            body = json.dumps({"folder_id": folder_id}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/upload/resumable/start":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            sid = f"s{len(self.sessions) + 1}"
            self.sessions[sid] = {
                "name": str(payload.get("name", "unknown")),
                "total": int(payload.get("size", 0)),
                "folder_id": str(payload.get("folder_id", "")),
                "data": bytearray(),
            }
            port = self.server.server_address[1]
            body = json.dumps({"session_uri": f"http://127.0.0.1:{port}/session/{sid}"}).encode(
                "utf-8"
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        if not self.path.startswith("/session/"):
            self.send_response(404)
            self.end_headers()
            return
        sid = self.path.split("/")[-1]
        session = self.sessions[sid]
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        content_range = str(self.headers.get("Content-Range", "bytes 0-0/0"))
        _, values = content_range.split(" ", 1)
        start_end, total = values.split("/")
        _start, end = [int(x) for x in start_end.split("-")]
        total = int(total)
        if end + 1 < total:
            self.send_response(308)
            self.send_header("Range", f"bytes=0-{end}")
            self.end_headers()
            return
        file_id = f"id_{sid}"
        self.files[file_id] = {
            "id": file_id,
            "name": session["name"],
            "size": session["total"],
            "md5Checksum": "",
            "modifiedTime": "2026-02-14T00:00:00+00:00",
            "version": "1",
        }
        self.uploads.append({"name": session["name"], "folder_id": session["folder_id"]})
        body = json.dumps({"file_id": file_id}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/files/"):
            file_id = self.path.split("/api/files/")[-1].split("?")[0]
            body = json.dumps(self.files.get(file_id, {})).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/api/children"):
            body = json.dumps({"files": []}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


def test_drive_folder_layout_with_hierarchy(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _write(run_dir / "result.json", "{}")
    _write(run_dir / "metrics.json", "{}")
    _write(run_dir / "ingestion/text.md", "text")
    _write(
        run_dir / "run_metadata.json",
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"demo","mode":"ops_extract","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","config":{},"preflight":{"passed":true,"errors":[],"warnings":[],"checks":[]}}',
    )
    _write(
        run_dir / "manifest.json",
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"demo","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","inputs":[],"outputs":[],"extract":{"method":"pdf_text","needs_ocr":false,"needs_ocr_reason":"not_needed","total_chars":0,"chars_per_page_mean":0.0,"empty_page_ratio":0.0},"ops":{"retries":0,"resume_count":0,"sync_state":"not_started"},"committed":true,"committed_local":true,"committed_drive":false,"version":"ops_extract_v1"}',
    )

    _FolderLayoutHandler.sessions = {}
    _FolderLayoutHandler.files = {}
    _FolderLayoutHandler.folders = {}
    _FolderLayoutHandler.uploads = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FolderLayoutHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        state = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            access_token="token",
            folder_id="root",
            api_base_url=f"http://127.0.0.1:{port}/api",
            upload_base_url=f"http://127.0.0.1:{port}/upload",
            verify_sha256=False,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert state["state"] == "committed"
    assert ("root", "Javis") in _FolderLayoutHandler.folders
    assert any(item["name"] == "text.md" for item in _FolderLayoutHandler.uploads)
    assert not any("__" in item["name"] for item in _FolderLayoutHandler.uploads)

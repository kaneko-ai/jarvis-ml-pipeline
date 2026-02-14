from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from jarvis_core.ops_extract.drive_sync import sync_run_to_drive


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class _PermissionHandler(BaseHTTPRequestHandler):
    folders: dict[tuple[str, str], str] = {}

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
            # Should not reach here in this test when permission guard works.
            self.send_response(500)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/permissions"):
            body = json.dumps(
                {"permissions": [{"id": "p1", "type": "anyone", "role": "reader"}]}
            ).encode("utf-8")
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


def test_permissions_public_link_hard_fail(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _write(run_dir / "result.json", "{}")
    _write(run_dir / "metrics.json", "{}")
    _write(
        run_dir / "manifest.json",
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"demo","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","inputs":[],"outputs":[],"extract":{"method":"pdf_text","needs_ocr":false,"needs_ocr_reason":"not_needed","total_chars":0,"chars_per_page_mean":0.0,"empty_page_ratio":0.0},"ops":{"retries":0,"resume_count":0,"sync_state":"not_started"},"committed":true,"committed_local":true,"committed_drive":false,"version":"ops_extract_v1"}',
    )
    _PermissionHandler.folders = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _PermissionHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        state = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=1,
            access_token="token",
            folder_id="root",
            api_base_url=f"http://127.0.0.1:{port}/api",
            upload_base_url=f"http://127.0.0.1:{port}/upload",
            verify_sha256=False,
            check_public_permissions=True,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
    assert state["state"] == "failed"
    assert "permissions_public_link_detected" in state["last_error"]


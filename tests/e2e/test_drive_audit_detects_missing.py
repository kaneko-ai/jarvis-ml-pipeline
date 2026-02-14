from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from jarvis_core.ops_extract.drive_audit import audit_manifest_vs_drive
from jarvis_core.ops_extract.drive_client import DriveResumableClient


class _DriveAuditHandler(BaseHTTPRequestHandler):
    def log_message(self, _format: str, *_args):  # pragma: no cover
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/children":
            query = parse_qs(parsed.query)
            parent_id = str((query.get("parent_id", [""])[0]))
            files = []
            if parent_id == "root":
                files = [
                    {
                        "id": "f_a",
                        "name": "a.json",
                        "mimeType": "application/json",
                        "size": 2,
                        "md5Checksum": "",
                    }
                ]
            body = json.dumps({"files": files}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


def test_drive_audit_detects_missing(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "a.json").write_text("{}", encoding="utf-8")
    (run_dir / "b.json").write_text("{}", encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "outputs": [
                    {"path": "a.json", "size": 2, "sha256": "a" * 64},
                    {"path": "b.json", "size": 2, "sha256": "b" * 64},
                ],
            }
        ),
        encoding="utf-8",
    )

    server = ThreadingHTTPServer(("127.0.0.1", 0), _DriveAuditHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        client = DriveResumableClient(
            access_token="token",
            api_base_url=f"http://127.0.0.1:{port}/api",
            upload_base_url=f"http://127.0.0.1:{port}/upload",
        )
        report = audit_manifest_vs_drive(run_dir=run_dir, client=client, folder_id="root")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert report["ok"] is False
    assert "b.json" in report["missing"]
    assert (run_dir / "drive_audit.json").exists()

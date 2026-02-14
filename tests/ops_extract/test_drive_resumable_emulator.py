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


def _setup_run_dir(run_dir: Path) -> None:
    _write(run_dir / "result.json", '{"status":"ok"}')
    _write(run_dir / "scores.json", '{"score":1}')
    _write(run_dir / "metrics.json", "{}")
    _write(run_dir / "warnings.json", '{"schema_version":"ops_extract_contract_v2","warnings":[]}')
    _write(
        run_dir / "failure_analysis.json",
        '{"schema_version":"ops_extract_contract_v2","status":"success","category":"none","root_cause_guess":"","recommendation_steps":[],"preventive_checks":[],"generated_at":"2026-02-13T00:00:00+00:00"}',
    )
    _write(
        run_dir / "run_metadata.json",
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"p1","mode":"ops_extract","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","config":{},"preflight":{"passed":true,"errors":[],"warnings":[],"checks":[]}}',
    )
    _write(
        run_dir / "trace.jsonl",
        '{"schema_version":"ops_extract_contract_v2","stage_id":"preflight","start_ts":"2026-02-13T00:00:00+00:00","end_ts":"2026-02-13T00:00:00+00:00","duration":0.0,"inputs":[],"outputs":[],"retry_count":0,"error":null}\n',
    )
    _write(
        run_dir / "stage_cache.json",
        '{"schema_version":"ops_extract_contract_v2","version":"ops_extract_stage_cache_v1","stages":{}}',
    )
    _write(run_dir / "ingestion/text.md", "hello")
    _write(
        run_dir / "ingestion/text_source.json",
        '{"run_id":"r1","project":"p1","source":"pdf_text","entries":[]}',
    )
    _write(
        run_dir / "ingestion/pdf_diagnosis.json",
        '{"schema_version":"ops_extract_contract_v2","files":[],"summary":{"text-embedded":0,"image-only":0,"hybrid":0,"encrypted":0,"corrupted":0}}',
    )
    _write(
        run_dir / "manifest.json",
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"p1","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","inputs":[],"outputs":[],"extract":{"method":"pdf_text","needs_ocr":false,"needs_ocr_reason":"not_needed","total_chars":5,"chars_per_page_mean":5.0,"empty_page_ratio":0.0},"ops":{"retries":0,"resume_count":0,"sync_state":"not_started"},"committed":true,"committed_local":true,"committed_drive":false,"version":"ops_extract_v1"}',
    )


class _DriveEmulatorHandler(BaseHTTPRequestHandler):
    sessions: dict[str, dict[str, Any]] = {}
    fail_once_by_name: dict[str, bool] = {"scores.json": False}

    def log_message(self, format: str, *args):  # pragma: no cover
        return

    def do_POST(self):
        if self.path != "/upload/resumable/start":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        name = str(payload.get("name", "file"))
        session_id = f"s{len(self.sessions) + 1}"
        self.sessions[session_id] = {
            "name": name,
            "data": bytearray(),
            "total": int(payload.get("size", 0)),
        }
        port = self.server.server_address[1]
        session_uri = f"http://127.0.0.1:{port}/session/{session_id}"
        body = json.dumps({"session_uri": session_uri}).encode("utf-8")
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
        session_id = self.path.split("/")[-1]
        session = self.sessions.get(session_id)
        if not session:
            self.send_response(404)
            self.end_headers()
            return
        name = str(session.get("name", ""))
        if name in self.fail_once_by_name and not self.fail_once_by_name[name]:
            self.fail_once_by_name[name] = True
            self.send_response(500)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        chunk = self.rfile.read(length)
        content_range = str(self.headers.get("Content-Range", ""))
        # bytes start-end/total
        _, values = content_range.split(" ", 1)
        start_end, total = values.split("/")
        start, end = [int(x) for x in start_end.split("-")]
        session["total"] = int(total)
        data = session["data"]
        if len(data) < start:
            data.extend(b"\x00" * (start - len(data)))
        if len(data) == start:
            data.extend(chunk)
        else:
            data[start : start + len(chunk)] = chunk

        if end + 1 < session["total"]:
            self.send_response(308)
            self.send_header("Range", f"bytes=0-{end}")
            self.end_headers()
            return

        body = json.dumps({"file_id": f"id_{session_id}"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def test_drive_resumable_emulator_resume_and_commit(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _setup_run_dir(run_dir)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _DriveEmulatorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    upload_base_url = f"http://127.0.0.1:{port}/upload"
    api_base_url = f"http://127.0.0.1:{port}/api"

    try:
        first = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            access_token="token",
            folder_id="folder",
            api_base_url=api_base_url,
            upload_base_url=upload_base_url,
            chunk_bytes=5,
            max_retries=0,
            retry_backoff_sec=0.0,
        )
        assert first["state"] == "failed"

        second = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            access_token="token",
            folder_id="folder",
            api_base_url=api_base_url,
            upload_base_url=upload_base_url,
            chunk_bytes=5,
            max_retries=1,
            retry_backoff_sec=0.0,
        )
        assert second["state"] == "committed"
        assert second["manifest_committed_drive"] is True
        assert any(item.get("path") == "manifest.json" for item in second["uploaded_files"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

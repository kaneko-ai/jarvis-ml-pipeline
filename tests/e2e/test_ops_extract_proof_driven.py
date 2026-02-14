from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig, OpsExtractThresholds
from jarvis_core.ops_extract.drive_sync import sync_run_to_drive
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _good_extraction() -> ExtractionResult:
    text = "A" * 1600
    return ExtractionResult(
        text=text,
        pages=[(1, text)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def _low_extraction() -> ExtractionResult:
    return ExtractionResult(
        text="short",
        pages=[(1, "")],
        method="pypdf",
        warnings=[{"category": "parser", "message": "low text"}],
        success=True,
    )


@pytest.mark.e2e
def test_e2e_text_embedded_pdf_without_ocr(tmp_path: Path):
    run_dir = tmp_path / "run-text"
    pdf = tmp_path / "text.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(enabled=True, lessons_path=str(tmp_path / "lessons.md")),
    )
    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_good_extraction(),
    ):
        outcome = orchestrator.run(run_id="e2e-text", project="demo", input_paths=[pdf])

    assert outcome.status == "success"
    assert outcome.ocr_used is False
    assert (run_dir / "ingestion" / "text.md").exists()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["committed_local"] is True


@pytest.mark.e2e
def test_e2e_image_pdf_with_ocr_path(tmp_path: Path):
    run_dir = tmp_path / "run-ocr"
    pdf = tmp_path / "image.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(
            enabled=True,
            lessons_path=str(tmp_path / "lessons.md"),
            thresholds=OpsExtractThresholds(
                min_total_chars=800,
                min_chars_per_page=200,
                empty_page_ratio_threshold=0.6,
            ),
        ),
    )
    with (
        patch(
            "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
            return_value=_low_extraction(),
        ),
        patch("jarvis_core.ops_extract.orchestrator.check_yomitoku_available", return_value=True),
        patch(
            "jarvis_core.ops_extract.orchestrator.rasterize_pdf_to_images",
            return_value={"page_count": 1, "image_paths": [str(tmp_path / "p1.png")], "dpi": 300},
        ),
        patch(
            "jarvis_core.ops_extract.orchestrator.run_yomitoku_cli",
            return_value={
                "text": "OCR CONTENT",
                "text_path": str(tmp_path / "ocr.md"),
                "returncode": 0,
                "figure_count": 0,
                "engine_version": "mock",
            },
        ),
    ):
        outcome = orchestrator.run(run_id="e2e-ocr", project="demo", input_paths=[pdf])

    assert outcome.status == "success"
    assert outcome.ocr_used is True
    assert (run_dir / "ingestion" / "text.md").exists()
    assert (run_dir / "ocr" / "ocr_meta.json").exists()


class _EmuHandler(BaseHTTPRequestHandler):
    sessions: dict[str, dict] = {}
    fail_once = {"scores.json": False}

    def log_message(self, format: str, *args):  # pragma: no cover
        return

    def do_POST(self):
        if self.path != "/upload/resumable/start":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        session_id = f"s{len(self.sessions) + 1}"
        self.sessions[session_id] = {
            "name": str(payload.get("name", "unknown")),
            "total": int(payload.get("size", 0)),
            "received": bytearray(),
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
        sid = self.path.split("/")[-1]
        session = self.sessions[sid]
        name = session["name"]
        if name in self.fail_once and not self.fail_once[name]:
            self.fail_once[name] = True
            self.send_response(500)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        chunk = self.rfile.read(length)
        content_range = str(self.headers.get("Content-Range", "bytes 0-0/0"))
        _, values = content_range.split(" ", 1)
        start_end, total = values.split("/")
        start, end = [int(x) for x in start_end.split("-")]
        total = int(total)
        received = session["received"]
        if len(received) < start:
            received.extend(b"\x00" * (start - len(received)))
        if len(received) == start:
            received.extend(chunk)
        else:
            received[start : start + len(chunk)] = chunk

        if end + 1 < total:
            self.send_response(308)
            self.send_header("Range", f"bytes=0-{end}")
            self.end_headers()
            return

        body = json.dumps({"file_id": f"id_{sid}"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _prepare_sync_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "result.json").write_text("{}", encoding="utf-8")
    (run_dir / "scores.json").write_text("{}", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"p1","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","inputs":[],"outputs":[],"extract":{"method":"pdf_text","needs_ocr":false,"needs_ocr_reason":"not_needed","total_chars":0,"chars_per_page_mean":0.0,"empty_page_ratio":0.0},"ops":{"retries":0,"resume_count":0,"sync_state":"not_started"},"committed":true,"committed_local":true,"committed_drive":false,"version":"ops_extract_v1"}',
        encoding="utf-8",
    )


@pytest.mark.e2e
def test_e2e_drive_sync_failed_then_resume_commit(tmp_path: Path):
    run_dir = tmp_path / "run-sync"
    _prepare_sync_run(run_dir)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _EmuHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    upload_base = f"http://127.0.0.1:{port}/upload"
    api_base = f"http://127.0.0.1:{port}/api"
    try:
        first = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            access_token="token",
            folder_id="folder",
            api_base_url=api_base,
            upload_base_url=upload_base,
            chunk_bytes=4,
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
            api_base_url=api_base,
            upload_base_url=upload_base,
            chunk_bytes=4,
            max_retries=1,
            retry_backoff_sec=0.0,
        )
        assert second["state"] == "committed"
        assert second["manifest_committed_drive"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

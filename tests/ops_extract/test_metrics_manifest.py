import json
from pathlib import Path

from jarvis_core.ops_extract.manifest import (
    build_input_entries,
    collect_output_entries,
    create_manifest_payload,
    write_manifest,
)
from jarvis_core.ops_extract.metrics import build_metrics, build_text_quality_warnings


def test_build_text_quality_warnings_detects_issues():
    text = "ABC\x00DEF    GHI\x01"
    warnings = build_text_quality_warnings(text)
    codes = {w["code"] for w in warnings}
    assert "TEXT_NUL_CHAR" in codes
    assert "TEXT_CONTROL_CHAR" in codes
    assert "TEXT_MULTI_SPACE" in codes


def test_build_metrics_has_ops_and_extract_sections():
    metrics = build_metrics(
        run_duration_sec=1.25,
        text_source="pdf_text",
        total_chars=1200,
        chars_per_page_mean=600.0,
        empty_page_ratio=0.0,
        encoding_warnings_count=1,
        ocr_used=False,
        needs_ocr_reason="not_needed",
    )
    assert "ops" in metrics
    assert "extract" in metrics
    assert metrics["extract"]["total_chars"] == 1200
    assert metrics["ops"]["run_duration_sec"] == 1.25


def test_manifest_payload_and_write(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    sample = run_dir / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    inputs = build_input_entries([sample])
    outputs = collect_output_entries(run_dir, exclude_relpaths={"manifest.json"})
    payload = create_manifest_payload(
        run_id="run-1",
        project="project-a",
        created_at="2026-02-13T00:00:00+00:00",
        finished_at="2026-02-13T00:01:00+00:00",
        status="success",
        inputs=inputs,
        outputs=outputs,
        extract={
            "method": "pdf_text",
            "needs_ocr": False,
            "needs_ocr_reason": "not_needed",
            "total_chars": 100,
            "chars_per_page_mean": 100.0,
            "empty_page_ratio": 0.0,
        },
        ops={"retries": 0, "resume_count": 0, "sync_state": "not_started"},
        committed=True,
    )
    manifest_path = write_manifest(run_dir / "manifest.json", payload)
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert loaded["committed"] is True
    assert loaded["status"] == "success"
    assert loaded["version"] == "ops_extract_v1"

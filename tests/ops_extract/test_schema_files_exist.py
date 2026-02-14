from __future__ import annotations

from pathlib import Path


def test_ops_extract_schema_files_exist():
    schema_dir = Path("schemas/ops_extract")
    required = {
        "manifest.schema.json",
        "metrics.schema.json",
        "warnings.schema.json",
        "failure_analysis.schema.json",
        "run_metadata.schema.json",
        "sync_state.schema.json",
        "trace.schema.json",
        "stage_cache.schema.json",
        "network_diagnosis.schema.json",
        "crash_dump.schema.json",
        "pdf_diagnosis.schema.json",
        "text_source.schema.json",
        "ocr_meta.schema.json",
        "lessons_entry.schema.json",
    }
    existing = {p.name for p in schema_dir.glob("*.schema.json")}
    missing = sorted(required - existing)
    assert not missing, f"missing schema files: {missing}"

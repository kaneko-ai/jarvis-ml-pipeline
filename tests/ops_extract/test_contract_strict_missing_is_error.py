from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.schema_validate import validate_run_contracts_strict


def test_contract_strict_missing_is_error(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "status": "success",
                "outputs": [{"path": "ingestion/text.md", "size": 1, "sha256": "a" * 64}],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    errors = validate_run_contracts_strict(run_dir, include_ocr_meta=False)
    assert any(err.startswith("missing:") for err in errors)
    assert any(err == "missing:run_metadata.json" for err in errors)

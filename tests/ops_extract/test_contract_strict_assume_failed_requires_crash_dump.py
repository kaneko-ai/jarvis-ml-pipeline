from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.schema_validate import validate_run_contracts_strict


def test_contract_strict_assume_failed_requires_crash_dump(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "status": "failed",
                "outputs": [{"path": "result.json", "size": 1, "sha256": "a" * 64}],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    errors = validate_run_contracts_strict(
        run_dir,
        include_ocr_meta=False,
        assume_failed=True,
    )
    assert "missing:crash_dump.json" in errors

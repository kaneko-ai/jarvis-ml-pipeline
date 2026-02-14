from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.cli_v4.main import run_workflow


def test_survey_emits_progress(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    input_pdf = tmp_path / "paper.pdf"
    input_pdf.write_text("dummy", encoding="utf-8")

    result = run_workflow(
        workflow="literature_to_plan",
        inputs=[str(input_pdf)],
        query="cd73 literature",
        concepts=["CD73"],
        output_dir=str(output_dir),
    )
    assert result["status"] == "success"

    progress_path = output_dir / "progress.jsonl"
    assert progress_path.exists()
    stages = []
    for raw in progress_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        stages.append(str(json.loads(raw).get("stage", "")))
    assert "survey_discover" in stages
    assert "survey_download" in stages
    assert "survey_parse" in stages
    assert "survey_index" in stages

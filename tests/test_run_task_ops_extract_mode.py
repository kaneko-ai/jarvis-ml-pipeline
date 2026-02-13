from pathlib import Path

from jarvis_core.app import run_task
from jarvis_core.ingestion.robust_extractor import ExtractionResult


def test_run_task_ops_extract_mode_skips_llm(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "input.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    def fake_extract(_self, _path):
        return ExtractionResult(
            text="A" * 1200,
            pages=[(1, "A" * 1200)],
            method="pypdf",
            warnings=[],
            success=True,
        )

    def llm_should_not_be_called(*_args, **_kwargs):
        raise AssertionError("LLMClient should not be initialized in ops_extract mode")

    monkeypatch.setattr(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        fake_extract,
    )
    monkeypatch.setattr("jarvis_core.llm_utils.LLMClient.__init__", llm_should_not_be_called)

    result = run_task(
        {
            "goal": "run ops extract",
            "mode": "ops_extract",
            "project": "demo",
            "inputs": {"pdf_paths": [str(pdf_path)]},
        },
        {
            "extra": {
                "ops_extract": {
                    "enabled": True,
                    "lessons_path": str(tmp_path / "lessons.md"),
                }
            },
            "provider": "gemini",
            "model": "gemini-2.0-flash",
        },
    )

    run_dir = Path(result.log_dir)
    assert result.status == "success"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "failure_analysis.json").exists()
    assert (run_dir / "result.json").exists()
    assert (run_dir / "eval_summary.json").exists()
    assert (run_dir / "warnings.jsonl").exists()


def test_run_task_ops_extract_mode_failure_generates_contract(tmp_path: Path):
    result = run_task(
        {
            "goal": "run ops extract failure",
            "mode": "ops_extract",
            "project": "demo",
            "inputs": {"pdf_paths": ["missing-file.pdf"]},
        },
        {
            "extra": {
                "ops_extract": {
                    "enabled": True,
                    "lessons_path": str(tmp_path / "lessons.md"),
                }
            },
            "provider": "mock",
        },
    )

    run_dir = Path(result.log_dir)
    assert result.status == "failed"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "failure_analysis.json").exists()
    assert (run_dir / "result.json").exists()
    assert (run_dir / "eval_summary.json").exists()
    assert (run_dir / "warnings.jsonl").exists()

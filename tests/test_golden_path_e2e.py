"""End-to-End Golden Path Test using Mock LLM.

This test runs the integrated pipeline via run_task() in offline mode,
ensuring all major components are covered.
"""

from pathlib import Path
import pytest
from jarvis_core.app import run_task


@pytest.fixture
def mock_env(monkeypatch):
    """Set environment variables for offline mock execution."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("USE_MOCK_PUBMED", "1")
    # Ensure no real API keys are needed
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")


def test_run_task_golden_path_e2e(mock_env):
    """Test full task execution from entry point to artifact generation."""
    task_dict = {
        "goal": "Explain the role of CRISPR in cancer immunotherapy.",
        "category": "oncology",
        "inputs": {"query": "CRISPR cancer immunotherapy"},
    }

    # Run config
    run_config = {"model": "mock-model", "seed": 42}

    # Execute
    result = run_task(task_dict, run_config)

    assert result.status == "success"
    assert result.gate_passed is True
    assert result.run_id is not None
    assert "Mock response" in result.answer

    # 2. Verify Artifact Consistency (10-file contract per MASTER_SPEC)
    run_dir = Path(result.log_dir)
    assert run_dir.exists()

    required_files = [
        "run_config.json",
        "result.json",
        "eval_summary.json",
        "events.jsonl",
        "papers.jsonl",
        "claims.jsonl",
        "evidence.jsonl",
        "scores.json",
        "report.md",
        "warnings.jsonl",
    ]

    for filename in required_files:
        path = run_dir / filename
        assert path.exists(), f"Missing required artifact: {filename}"
        if filename.endswith(".json"):
            import json

            content = json.loads(path.read_text(encoding="utf-8"))
            assert content is not None
        elif filename.endswith(".jsonl"):
            lines = path.read_text(encoding="utf-8").splitlines()
            assert len(lines) >= 0  # events.jsonl must have entries
            if filename == "events.jsonl":
                assert len(lines) > 0

    # 3. Clean up (optional, but good for local tests)
    # shutil.rmtree(run_dir)


def test_run_task_error_handling(mock_env):
    """Test application behavior on invalid input."""
    # Intentional error: empty goal
    task_dict = {"goal": ""}

    result = run_task(task_dict)

    # Per MASTER_SPEC: failed status if goal missing or logic fails
    assert result.status == "failed"
    assert Path(result.log_dir).exists()
    assert (Path(result.log_dir) / "result.json").exists()


def test_run_task_retry_flow(mock_env):
    """Test that temporary LLM errors trigger automatic retries."""
    task_dict = {"goal": "Trigger a retry flow. keywords: trigger_retry", "category": "generic"}

    # Execute
    result = run_task(task_dict)

    # Should eventually succeed after retry
    assert result.status == "success"
    assert "Successful retry response" in result.answer


def test_run_task_budget_error(mock_env):
    """Test that critical provider errors (e.g. budget) lead to controlled failure."""
    task_dict = {"goal": "Test budget limit. keywords: trigger_budget_limit", "category": "generic"}

    # Execute
    result = run_task(task_dict)

    # Should fail with budget error info
    assert result.status == "failed"
    assert any("Budget exhausted" in w for w in result.warnings)


def test_run_task_empty_llm_response(mock_env):
    """Test that empty LLM responses are handled (likely causing quality gate failure)."""
    task_dict = {"goal": "Test empty response. keywords: trigger_empty", "category": "generic"}

    # Execute
    result = run_task(task_dict)

    # LLM returns empty -> Agent might return empty or fail -> Quality gate fails
    assert result.status == "failed"
    # Result answer should be empty if agent couldn't handle it
    assert result.answer == ""

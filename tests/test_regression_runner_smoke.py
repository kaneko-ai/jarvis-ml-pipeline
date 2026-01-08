"""Tests for regression runner (smoke).

Per RP-203.
"""

import pytest

pytestmark = pytest.mark.core


class TestRegressionRunnerSmoke:
    """Smoke tests for regression runner."""

    def test_load_gold_set(self, tmp_path):
        """Gold set should load correctly."""
        from scripts.run_regression import load_gold_set

        # Create test gold set
        gold_file = tmp_path / "test_gold.jsonl"
        gold_file.write_text(
            '{"id": "1", "query": "test query"}\n' '{"id": "2", "query": "another query"}\n'
        )

        cases = load_gold_set(str(gold_file))
        assert len(cases) == 2
        assert cases[0]["id"] == "1"

    def test_compute_summary(self):
        """Summary should compute correctly."""
        from scripts.run_regression import compute_summary

        results = [
            {"status": "success", "metrics": {"claim_precision": 0.8}},
            {"status": "success", "metrics": {"claim_precision": 0.6}},
            {"status": "failed", "metrics": {}},
        ]

        summary = compute_summary(results)
        assert summary["total"] == 3
        assert summary["success"] == 2
        assert summary["success_rate"] == 2 / 3


class TestQualityBarChecker:
    """Tests for quality bar checker."""

    def test_check_pass(self):
        """Should pass when all thresholds met."""
        from scripts.check_quality_bar import check_quality_bar

        metrics = {
            "success_rate": 0.90,
            "claim_precision": 0.75,
            "citation_precision": 0.70,
            "entity_hit_rate": 0.70,
        }

        result = check_quality_bar(metrics)
        assert result["passed"]

    def test_check_fail(self):
        """Should fail when threshold not met."""
        from scripts.check_quality_bar import check_quality_bar

        metrics = {
            "success_rate": 0.50,  # Below threshold
        }

        result = check_quality_bar(metrics)
        assert not result["passed"]

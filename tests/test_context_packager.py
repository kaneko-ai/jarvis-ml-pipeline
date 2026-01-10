"""Tests for workflow.context_packager module."""

from jarvis_core.workflow.context_packager import (
    LogEntry,
    ScoreDiff,
    ContextPackager,
)


class TestLogEntry:
    def test_creation(self):
        entry = LogEntry(
            run_id="run-1",
            step_id="step-1",
            score=0.75,
            output_summary="Test summary",
        )
        
        assert entry.run_id == "run-1"
        assert entry.score == 0.75
        assert entry.timestamp is not None


class TestScoreDiff:
    def test_creation(self):
        diff = ScoreDiff(
            metric="accuracy",
            prev_best=0.80,
            current=0.75,
            diff=-0.05,
            is_regression=True,
        )
        
        assert diff.metric == "accuracy"
        assert diff.is_regression is True


class TestContextPackager:
    def test_init(self):
        packager = ContextPackager(
            bottom_k_percent=30.0,
            max_entries=5,
            summary_max_chars=200,
        )
        
        assert packager.bottom_k_percent == 30.0

    def test_add_log_and_best_tracking(self):
        packager = ContextPackager()
        
        packager.add_log(LogEntry("r1", "s1", 0.5, "summary1"))
        packager.add_log(LogEntry("r2", "s2", 0.8, "summary2"))
        packager.add_log(LogEntry("r3", "s3", 0.6, "summary3"))
        
        assert packager._best_score == 0.8
        assert packager._best_run_id == "r2"

    def test_get_bottom_k_logs(self):
        packager = ContextPackager(bottom_k_percent=50.0)
        
        packager.add_log(LogEntry("r1", "s1", 0.9, "high"))
        packager.add_log(LogEntry("r2", "s2", 0.1, "low"))
        packager.add_log(LogEntry("r3", "s3", 0.5, "mid"))
        packager.add_log(LogEntry("r4", "s4", 0.2, "low2"))
        
        bottom = packager.get_bottom_k_logs()
        
        # Should get bottom 50% (lowest scores)
        assert len(bottom) == 2
        assert bottom[0].score <= bottom[1].score

    def test_get_bottom_k_logs_empty(self):
        packager = ContextPackager()
        
        assert packager.get_bottom_k_logs() == []

    def test_generate_score_diff(self):
        packager = ContextPackager()
        
        current = {"accuracy": 0.75, "f1": 0.80}
        prev_best = {"accuracy": 0.80, "f1": 0.70}
        
        diffs = packager.generate_score_diff(current, prev_best)
        
        assert len(diffs) == 2
        
        accuracy_diff = next(d for d in diffs if d.metric == "accuracy")
        assert accuracy_diff.is_regression is True
        # Use approximate comparison for floating point
        import pytest
        assert accuracy_diff.diff == pytest.approx(-0.05, abs=1e-10)

    def test_generate_score_diff_no_prev(self):
        packager = ContextPackager()
        
        diffs = packager.generate_score_diff({"a": 1.0}, None)
        
        assert diffs == []

    def test_detect_regression_no_best(self):
        packager = ContextPackager()
        
        assert packager.detect_regression(0.5) is False

    def test_detect_regression_with_best(self):
        packager = ContextPackager()
        packager.add_log(LogEntry("r1", "s1", 0.8, "high"))
        
        assert packager.detect_regression(0.5) is True
        assert packager.detect_regression(0.85) is False

    def test_package_for_generator(self):
        packager = ContextPackager()
        
        packager.add_log(LogEntry("r1", "s1", 0.5, "summary"))
        
        package = packager.package_for_generator(
            current_scores={"acc": 0.7},
            prev_best_scores={"acc": 0.8},
        )
        
        assert "bottom_logs" in package
        assert "score_diffs" in package
        assert "regression_cases" in package
        assert "best_score" in package

    def test_clear(self):
        packager = ContextPackager()
        packager.add_log(LogEntry("r1", "s1", 0.5, "summary"))
        
        packager.clear()
        
        assert len(packager._logs) == 0
        assert packager._best_score is None

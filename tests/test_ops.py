"""
JARVIS Ops Module Tests

M4: 運用完備のテスト
- レート制限
- チェックポイント/再開
- メトリクス
"""

from jarvis_core.ops.checkpoint import (
    CheckpointManager,
    RunCheckpoint,
    StageCheckpoint,
    StageStatus,
)
from jarvis_core.ops.metrics import (
    MetricsCollector,
)
from jarvis_core.ops.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    with_retry,
)
from tempfile import TemporaryDirectory

import pytest


class TestRateLimiter:
    """レートリミッターテスト."""

    def test_rate_limit_config_defaults(self):
        """デフォルト設定が正しいこと."""
        config = RateLimitConfig()
        assert config.requests_per_second == 3.0
        assert config.max_retries == 3
        assert config.base_delay_sec == 1.0

    def test_retry_delay_exponential(self):
        """指数バックオフが正しく計算されること."""
        config = RateLimitConfig(base_delay_sec=1.0, exponential_base=2.0, jitter=False)
        limiter = RateLimiter(config)

        assert limiter.get_retry_delay(0) == 1.0
        assert limiter.get_retry_delay(1) == 2.0
        assert limiter.get_retry_delay(2) == 4.0

    def test_retry_delay_max_cap(self):
        """最大遅延でキャップされること."""
        config = RateLimitConfig(base_delay_sec=1.0, max_delay_sec=10.0, jitter=False)
        limiter = RateLimiter(config)

        delay = limiter.get_retry_delay(10)  # 2^10 = 1024 > 10
        assert delay == 10.0


class TestWithRetry:
    """リトライデコレータテスト."""

    def test_retry_on_success(self):
        """成功時はリトライしないこと."""
        call_count = [0]

        @with_retry(max_retries=3)
        def success_func():
            call_count[0] += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count[0] == 1

    def test_retry_on_eventual_success(self):
        """一時的な失敗後に成功すること."""
        call_count = [0]

        @with_retry(max_retries=3, base_delay=0.01)
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count[0] == 2


class TestCheckpointManager:
    """チェックポイントマネージャーテスト."""

    def test_save_and_load(self):
        """保存と読込が動作すること."""
        with TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(base_path=tmpdir)

            checkpoint = RunCheckpoint(run_id="test_run", pipeline="test_pipeline")

            manager.save(checkpoint)
            loaded = manager.load("test_run")

            assert loaded is not None
            assert loaded.run_id == "test_run"
            assert loaded.pipeline == "test_pipeline"

    def test_stage_update(self):
        """ステージ更新が動作すること."""
        with TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(base_path=tmpdir)

            checkpoint = RunCheckpoint(run_id="test_run", pipeline="test")
            manager.save(checkpoint)

            manager.update_stage("test_run", "stage_1", StageStatus.COMPLETED, duration_ms=1000)

            loaded = manager.load("test_run")
            assert "stage_1" in loaded.stages
            assert loaded.stages["stage_1"].status == StageStatus.COMPLETED

    def test_get_completed_stages(self):
        """完了済みステージを取得できること."""
        with TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(base_path=tmpdir)

            checkpoint = RunCheckpoint(run_id="test_run", pipeline="test")
            checkpoint.stages["s1"] = StageCheckpoint(stage_id="s1", status=StageStatus.COMPLETED)
            checkpoint.stages["s2"] = StageCheckpoint(stage_id="s2", status=StageStatus.PENDING)
            checkpoint.stages["s3"] = StageCheckpoint(stage_id="s3", status=StageStatus.COMPLETED)
            manager.save(checkpoint)

            completed = manager.get_completed_stages("test_run")
            assert completed == {"s1", "s3"}

    def test_resume_point(self):
        """再開ポイントを取得できること."""
        with TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(base_path=tmpdir)

            checkpoint = RunCheckpoint(run_id="test_run", pipeline="test", current_stage_idx=3)
            manager.save(checkpoint)

            resume_point = manager.get_resume_point("test_run")
            assert resume_point == 3


class TestMetricsCollector:
    """メトリクスコレクターテスト."""

    def test_start_and_end_run(self):
        """ランの開始と終了が動作すること."""
        with TemporaryDirectory() as tmpdir:
            collector = MetricsCollector(base_path=tmpdir)

            collector.start_run("test_run", "test_pipeline")
            metrics = collector.end_run("completed")

            assert metrics["run"]["run_id"] == "test_run"
            assert metrics["run"]["status"] == "completed"

    def test_stage_timing(self):
        """ステージタイミングが記録されること."""
        import time

        with TemporaryDirectory() as tmpdir:
            collector = MetricsCollector(base_path=tmpdir)

            collector.start_run("test_run", "test")
            collector.start_stage("stage_1")
            time.sleep(0.01)  # 10ms
            collector.end_stage("stage_1")

            metrics = collector.get_current_metrics()
            assert "stage_1" in metrics["run"]["stage_durations"]
            assert metrics["run"]["stage_durations"]["stage_1"] >= 10

    def test_api_call_recording(self):
        """API呼び出しが記録されること."""
        with TemporaryDirectory() as tmpdir:
            collector = MetricsCollector(base_path=tmpdir)

            collector.start_run("test_run", "test")
            collector.record_api_call(success=True)
            collector.record_api_call(success=False)
            collector.record_api_call(success=True, retried=True)

            metrics = collector.get_current_metrics()
            assert metrics["run"]["api_calls"] == 3
            assert metrics["run"]["api_errors"] == 1
            assert metrics["run"]["api_retries"] == 1

    def test_quality_metrics(self):
        """品質メトリクスが更新されること."""
        with TemporaryDirectory() as tmpdir:
            collector = MetricsCollector(base_path=tmpdir)

            collector.start_run("test_run", "test")
            collector.update_quality(
                provenance_rate=0.95,
                pico_consistency_rate=0.88,
                gate_name="provenance",
                gate_passed=True,
            )

            metrics = collector.get_current_metrics()
            assert metrics["quality"]["provenance_rate"] == 0.95
            assert metrics["quality"]["pico_consistency_rate"] == 0.88
            assert metrics["quality"]["gate_results"]["provenance"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

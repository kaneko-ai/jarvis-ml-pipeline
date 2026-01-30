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
    PipelineMetrics,
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


class TestPipelineMetrics:
    """メトリクスコレクターテスト (PipelineMetrics Adapter)."""

    def test_counter_increment(self):
        """カウンタが機能すること."""
        # Reset global metrics for test
        test_metrics = PipelineMetrics()

        test_metrics.inc_counter("test_counter", {"label": "a"})
        output = test_metrics.generate_prometheus_output()

        assert 'test_counter{label="a"} 1.0' in output

    def test_gauge_set(self):
        """ゲージが機能すること."""
        test_metrics = PipelineMetrics()

        test_metrics.set_gauge("test_gauge", 42.0, {"label": "b"})
        output = test_metrics.generate_prometheus_output()

        assert 'test_gauge{label="b"} 42.0' in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

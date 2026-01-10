"""Tests for workflow.repeated_sampling module."""

from jarvis_core.workflow.repeated_sampling import (
    SampleResult,
    RepeatedSampler,
)


class TestSampleResult:
    def test_creation(self):
        result = SampleResult(
            sample_id="sample_0",
            output={"key": "value"},
            score=0.85,
            cost=0.1,
        )
        
        assert result.sample_id == "sample_0"
        assert result.score == 0.85
        assert result.is_valid is True

    def test_invalid_result(self):
        result = SampleResult(
            sample_id="sample_1",
            output=None,
            score=0.0,
            cost=0.0,
            is_valid=False,
            error="Test error",
        )
        
        assert result.is_valid is False
        assert result.error == "Test error"


class TestRepeatedSampler:
    def test_init(self):
        sampler = RepeatedSampler(n_samples=5, max_cost=10.0, min_samples=2)
        
        assert sampler.n_samples == 5
        assert sampler.max_cost == 10.0
        assert sampler.min_samples == 2

    def test_sample_returns_best(self):
        sampler = RepeatedSampler(n_samples=3, max_cost=100.0)
        
        counter = [0]
        def generator():
            counter[0] += 1
            return f"output_{counter[0]}"
        
        def evaluator(output):
            # Score higher for later samples
            return float(counter[0]) / 10
        
        result = sampler.sample(generator, evaluator)
        
        assert result is not None
        assert result.score > 0

    def test_sample_with_cost_estimator(self):
        sampler = RepeatedSampler(n_samples=3, max_cost=100.0)
        
        def generator():
            return "output"
        
        def evaluator(output):
            return 0.5
        
        def cost_estimator(output):
            return 0.01
        
        result = sampler.sample(generator, evaluator, cost_estimator)
        
        assert result is not None
        assert sampler.total_cost > 0

    def test_cost_limit_stops_sampling(self):
        sampler = RepeatedSampler(n_samples=10, max_cost=0.05)
        
        samples_generated = [0]
        
        def generator():
            samples_generated[0] += 1
            return "output"
        
        def evaluator(output):
            return 0.5
        
        def cost_estimator(output):
            return 0.02  # Each sample costs 0.02
        
        sampler.sample(generator, evaluator, cost_estimator)
        
        # Should stop before 10 samples due to cost limit
        assert samples_generated[0] < 10

    def test_reset_cost(self):
        sampler = RepeatedSampler()
        sampler._total_cost = 5.0
        
        sampler.reset_cost()
        
        assert sampler.total_cost == 0.0

    def test_adjust_samples(self):
        sampler = RepeatedSampler(n_samples=10, max_cost=10.0, min_samples=1)
        
        # Full budget
        adjusted = sampler._adjust_samples()
        assert adjusted == 10
        
        # Half budget used
        sampler._total_cost = 5.0
        adjusted = sampler._adjust_samples()
        assert 1 <= adjusted <= 10

    def test_all_samples_fail(self):
        sampler = RepeatedSampler(n_samples=3)
        
        def failing_generator():
            raise ValueError("Always fails")
        
        def evaluator(output):
            return 0.5
        
        result = sampler.sample(failing_generator, evaluator)
        
        assert result is None

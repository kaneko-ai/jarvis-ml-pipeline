"""Tests for infrastructure components.

Core tests for reliability, database, and infra modules.
"""
import pytest
import time
import threading

pytestmark = pytest.mark.core


class TestCircuitBreaker:
    """Tests for RP-575 Circuit Breaker."""

    def test_circuit_closed_on_success(self):
        """Circuit should stay closed on success."""
        from jarvis_core.reliability import CircuitBreaker

        cb = CircuitBreaker("test")

        def success_fn():
            return "ok"

        result = cb.call(success_fn)
        assert result == "ok"
        assert cb.state.value == "closed"

    def test_circuit_opens_on_failures(self):
        """Circuit should open after failures."""
        from jarvis_core.reliability import CircuitBreaker, CircuitConfig

        config = CircuitConfig(failure_threshold=2)
        cb = CircuitBreaker("test", config)

        def fail_fn():
            raise ValueError("fail")

        for _ in range(2):
            try:
                cb.call(fail_fn)
            except ValueError:
                pass

        assert cb.state.value == "open"

    def test_circuit_rejects_when_open(self):
        """Circuit should reject calls when open."""
        from jarvis_core.reliability import CircuitBreaker, CircuitConfig, CircuitOpenError

        config = CircuitConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config)

        def fail_fn():
            raise ValueError("fail")

        try:
            cb.call(fail_fn)
        except ValueError:
            pass

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "ok")


class TestRetry:
    """Tests for RP-576 Retry."""

    def test_success_no_retry(self):
        """Should not retry on success."""
        from jarvis_core.reliability import retry_with_backoff

        call_count = 0

        @retry_with_backoff()
        def success_fn():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = success_fn()
        assert result == "ok"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Should retry on failure."""
        from jarvis_core.reliability import retry_with_backoff, RetryConfig

        config = RetryConfig(max_retries=2, base_delay=0.01)
        call_count = 0

        @retry_with_backoff(config)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 2


class TestRateLimiter:
    """Tests for RP-563 Rate Limiter."""

    def test_allows_within_limit(self):
        """Should allow requests within limit."""
        from jarvis_core.reliability.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_second=100, burst_size=10)
        limiter = RateLimiter(config)

        for _ in range(5):
            assert limiter.is_allowed("user1")

    def test_blocks_over_limit(self):
        """Should block requests over limit."""
        from jarvis_core.reliability.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_second=1, burst_size=2)
        limiter = RateLimiter(config)

        # Exhaust burst
        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")
        
        # Should be blocked
        result = limiter.check("user1")
        assert not result.allowed


class TestHealthCheck:
    """Tests for RP-543 Health Check."""

    def test_liveness(self):
        """Liveness should always pass."""
        from jarvis_core.reliability.health import HealthChecker, HealthStatus

        checker = HealthChecker(version="1.0.0")
        report = checker.check_liveness()

        assert report.status == HealthStatus.HEALTHY
        assert report.version == "1.0.0"

    def test_readiness_with_checks(self):
        """Readiness should run all checks."""
        from jarvis_core.reliability.health import HealthChecker, HealthStatus, CheckResult

        checker = HealthChecker()

        def healthy_check():
            return CheckResult(
                name="test",
                status=HealthStatus.HEALTHY,
                latency_ms=1.0,
            )

        checker.register_check("test", healthy_check)
        report = checker.check_readiness()

        assert report.status == HealthStatus.HEALTHY
        assert len(report.checks) == 1


class TestConnectionPool:
    """Tests for RP-550 Connection Pool."""

    def test_acquire_release(self):
        """Should acquire and release connections."""
        from jarvis_core.database import ConnectionPool, PoolConfig

        connections_created = []

        def create():
            conn = {"id": len(connections_created)}
            connections_created.append(conn)
            return conn

        def close(conn):
            pass

        pool = ConnectionPool(create, close, config=PoolConfig(min_size=1))

        with pool.acquire() as conn:
            assert "id" in conn

        stats = pool.get_stats()
        assert stats.total_checkouts >= 1

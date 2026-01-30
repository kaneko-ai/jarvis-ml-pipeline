"""Health Check Endpoints.

Per RP-543, implements comprehensive health checks.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class CheckResult:
    """Result of a single health check."""

    name: str
    status: HealthStatus
    latency_ms: float
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    """Aggregate health report."""

    status: HealthStatus
    checks: list[CheckResult]
    timestamp: str
    version: str
    uptime_seconds: float


class HealthChecker:
    """Health check manager.

    Per RP-543:
    - /health (basic liveness)
    - /ready (deep readiness)
    - Dependency checks
    """

    def __init__(
        self,
        version: str = "4.4.0",
        start_time: float | None = None,
    ):
        self.version = version
        self.start_time = start_time or time.time()
        self._checks: dict[str, Callable[[], CheckResult]] = {}
        self._async_checks: dict[str, Callable[[], CheckResult]] = {}

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], CheckResult],
    ) -> None:
        """Register a health check.

        Args:
            name: Check name.
            check_fn: Check function.
        """
        self._checks[name] = check_fn

    def register_async_check(
        self,
        name: str,
        check_fn: Callable,
    ) -> None:
        """Register an async health check.

        Args:
            name: Check name.
            check_fn: Async check function.
        """
        self._async_checks[name] = check_fn

    def check_liveness(self) -> HealthReport:
        """Basic liveness check.

        Returns:
            HealthReport for liveness.
        """
        from datetime import datetime

        return HealthReport(
            status=HealthStatus.HEALTHY,
            checks=[],
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
        )

    def check_readiness(self) -> HealthReport:
        """Deep readiness check.

        Returns:
            HealthReport with all checks.
        """
        from datetime import datetime

        results = []
        overall_status = HealthStatus.HEALTHY

        for name, check_fn in self._checks.items():
            try:
                start = time.time()
                result = check_fn()
                result.latency_ms = (time.time() - start) * 1000
                results.append(result)

                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif (
                    result.status == HealthStatus.DEGRADED
                    and overall_status == HealthStatus.HEALTHY
                ):
                    overall_status = HealthStatus.DEGRADED

            except Exception as e:
                results.append(
                    CheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=0,
                        message=str(e),
                    )
                )
                overall_status = HealthStatus.UNHEALTHY

        return HealthReport(
            status=overall_status,
            checks=results,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
        )

    async def check_readiness_async(self) -> HealthReport:
        """Async deep readiness check.

        Returns:
            HealthReport with all checks.
        """
        from datetime import datetime

        results = []
        overall_status = HealthStatus.HEALTHY

        # Run sync checks
        for name, check_fn in self._checks.items():
            try:
                result = check_fn()
                results.append(result)

                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
            except Exception as e:
                results.append(
                    CheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=0,
                        message=str(e),
                    )
                )
                overall_status = HealthStatus.UNHEALTHY

        # Run async checks
        for name, check_fn in self._async_checks.items():
            try:
                start = time.time()
                result = await check_fn()
                result.latency_ms = (time.time() - start) * 1000
                results.append(result)

                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
            except Exception as e:
                results.append(
                    CheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=0,
                        message=str(e),
                    )
                )
                overall_status = HealthStatus.UNHEALTHY

        return HealthReport(
            status=overall_status,
            checks=results,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
        )


# Built-in checks


def check_redis(redis_url: str) -> CheckResult:
    """Check Redis connectivity."""
    try:
        import redis

        r = redis.from_url(redis_url)
        start = time.time()
        r.ping()
        latency = (time.time() - start) * 1000

        return CheckResult(
            name="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=latency,
            message="Connected",
        )
    except Exception as e:
        return CheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=0,
            message=str(e),
        )


def check_postgres(database_url: str) -> CheckResult:
    """Check PostgreSQL connectivity."""
    try:
        import psycopg2

        start = time.time()
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        latency = (time.time() - start) * 1000

        return CheckResult(
            name="postgres",
            status=HealthStatus.HEALTHY,
            latency_ms=latency,
            message="Connected",
        )
    except Exception as e:
        return CheckResult(
            name="postgres",
            status=HealthStatus.UNHEALTHY,
            latency_ms=0,
            message=str(e),
        )


def check_qdrant(qdrant_url: str) -> CheckResult:
    """Check Qdrant connectivity."""
    try:
        import requests

        start = time.time()
        resp = requests.get(f"{qdrant_url}/health", timeout=5)
        latency = (time.time() - start) * 1000

        if resp.status_code == 200:
            return CheckResult(
                name="qdrant",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Connected",
            )
        else:
            return CheckResult(
                name="qdrant",
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"Status {resp.status_code}",
            )
    except Exception as e:
        return CheckResult(
            name="qdrant",
            status=HealthStatus.UNHEALTHY,
            latency_ms=0,
            message=str(e),
        )


def check_disk_space(path: str = "/", min_gb: float = 1.0) -> CheckResult:
    """Check disk space."""
    try:
        import shutil

        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)

        if free_gb >= min_gb:
            status = HealthStatus.HEALTHY
        elif free_gb >= min_gb * 0.5:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        return CheckResult(
            name="disk",
            status=status,
            latency_ms=0,
            message=f"{free_gb:.1f}GB free",
            details={"free_gb": free_gb},
        )
    except Exception as e:
        return CheckResult(
            name="disk",
            status=HealthStatus.UNHEALTHY,
            latency_ms=0,
            message=str(e),
        )


def check_memory(max_percent: float = 90.0) -> CheckResult:
    """Check memory usage."""
    try:
        import psutil

        memory = psutil.virtual_memory()

        if memory.percent < max_percent * 0.8:
            status = HealthStatus.HEALTHY
        elif memory.percent < max_percent:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        return CheckResult(
            name="memory",
            status=status,
            latency_ms=0,
            message=f"{memory.percent:.1f}% used",
            details={"percent": memory.percent},
        )
    except Exception:
        return CheckResult(
            name="memory",
            status=HealthStatus.HEALTHY,  # Don't fail if psutil not available
            latency_ms=0,
            message="Check unavailable",
        )

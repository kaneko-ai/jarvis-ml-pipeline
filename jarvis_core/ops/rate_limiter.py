"""
JARVIS Operations - Rate Limiting & Retry

M4: 運用完備のためのレート制限・リトライ機構
- 指数バックオフ
- 最大リトライ回数
- 全体タイムアウト
"""

from __future__ import annotations

import asyncio
import functools
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    """レート制限設定."""

    requests_per_second: float = 3.0  # PubMed: 3 req/s without API key
    requests_per_minute: int | None = None
    burst_limit: int = 10

    # リトライ設定
    max_retries: int = 3
    base_delay_sec: float = 1.0
    max_delay_sec: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    # タイムアウト
    request_timeout_sec: float = 30.0
    total_timeout_sec: float = 300.0


@dataclass
class RateLimitState:
    """レート制限状態."""

    request_times: list[float] = field(default_factory=list)
    total_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0
    last_request_time: float | None = None

    def add_request(self):
        """リクエストを記録."""
        now = time.time()
        self.request_times.append(now)
        self.total_requests += 1
        self.last_request_time = now

        # 1分より古いエントリを削除
        cutoff = now - 60
        self.request_times = [t for t in self.request_times if t > cutoff]

    def get_requests_in_window(self, window_sec: float) -> int:
        """ウィンドウ内のリクエスト数を取得."""
        now = time.time()
        cutoff = now - window_sec
        return sum(1 for t in self.request_times if t > cutoff)


class RateLimiter:
    """レートリミッター."""

    def __init__(self, config: RateLimitConfig | None = None):
        """
        初期化.

        Args:
            config: レート制限設定
        """
        self.config = config or RateLimitConfig()
        self.state = RateLimitState()
        try:
            asyncio.get_running_loop()
            self._lock = asyncio.Lock()
        except RuntimeError:
            # No active event loop in this thread (common for sync callers).
            self._lock = None

    def _calculate_delay(self) -> float:
        """次のリクエストまでの待機時間を計算."""
        if not self.state.request_times:
            return 0.0

        # 1秒あたりの制限をチェック
        requests_last_second = self.state.get_requests_in_window(1.0)
        if requests_last_second >= self.config.requests_per_second:
            return 1.0 / self.config.requests_per_second

        # 1分あたりの制限をチェック
        if self.config.requests_per_minute:
            requests_last_minute = self.state.get_requests_in_window(60.0)
            if requests_last_minute >= self.config.requests_per_minute:
                return 60.0 / self.config.requests_per_minute

        return 0.0

    def wait_if_needed(self):
        """必要に応じて待機（同期版）."""
        delay = self._calculate_delay()
        if delay > 0:
            logger.debug(f"Rate limiting: waiting {delay:.2f}s")
            time.sleep(delay)
        self.state.add_request()

    async def wait_if_needed_async(self):
        """必要に応じて待機（非同期版）."""
        delay = self._calculate_delay()
        if delay > 0:
            logger.debug(f"Rate limiting: waiting {delay:.2f}s")
            await asyncio.sleep(delay)
        self.state.add_request()

    def get_retry_delay(self, attempt: int) -> float:
        """
        リトライ遅延を計算（指数バックオフ）.

        Args:
            attempt: リトライ回数（0から開始）

        Returns:
            遅延秒数
        """
        delay = self.config.base_delay_sec * (self.config.exponential_base**attempt)
        delay = min(delay, self.config.max_delay_sec)

        if self.config.jitter:
            # ±25%のジッター
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
):
    """
    リトライデコレータ.

    Args:
        max_retries: 最大リトライ回数
        base_delay: 基本遅延（秒）
        max_delay: 最大遅延（秒）
        retryable_exceptions: リトライ対象の例外
        on_retry: リトライ時のコールバック
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt >= max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded: {e}")
                        raise

                    delay = min(base_delay * (2**attempt), max_delay)
                    delay += random.uniform(0, delay * 0.25)  # jitter

                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(delay)

            raise last_exception  # type: ignore

        return wrapper

    return decorator


# PubMed/PMC用のレートリミッター
_pubmed_limiter: RateLimiter | None = None


def get_pubmed_rate_limiter() -> RateLimiter:
    """PubMed用レートリミッターを取得."""
    global _pubmed_limiter
    if _pubmed_limiter is None:
        import os

        # API keyがある場合は10 req/s、ない場合は3 req/s
        has_api_key = bool(os.environ.get("NCBI_API_KEY"))
        rps = 10.0 if has_api_key else 3.0

        _pubmed_limiter = RateLimiter(
            RateLimitConfig(
                requests_per_second=rps,
                max_retries=3,
                base_delay_sec=1.0,
                request_timeout_sec=30.0,
                total_timeout_sec=300.0,
            )
        )

    return _pubmed_limiter

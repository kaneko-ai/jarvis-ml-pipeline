import time

from jarvis_core.scheduler.rate_limit import DomainRateLimiter


def test_rate_limit_backoff():
    limiter = DomainRateLimiter()
    assert limiter.acquire("pubmed")
    limiter.record_response("pubmed", 429)
    assert limiter.backoff_until("pubmed") > time.time()
    assert not limiter.acquire("pubmed")

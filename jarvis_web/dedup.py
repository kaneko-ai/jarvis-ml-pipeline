"""Deduplication helpers for job and chunk idempotency."""

from __future__ import annotations

import os
from typing import Optional, Tuple


DEFAULT_DEDUPE_TTL_SEC = 60 * 60 * 24 * 3
DEFAULT_CHUNK_SEEN_TTL_SEC = 60 * 60 * 24 * 30


def _redis_url() -> str:
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        raise RuntimeError("REDIS_URL is required for dedupe")
    return redis_url


def get_redis():
    import redis

    return redis.from_url(_redis_url())


def claim_dedupe_key(
    redis_client,
    dedupe_key: str,
    job_id: str,
    ttl_sec: Optional[int] = None,
) -> Tuple[bool, Optional[str]]:
    ttl = ttl_sec or int(os.environ.get("DEDUPE_TTL_SEC", DEFAULT_DEDUPE_TTL_SEC))
    key = f"dedupe:{dedupe_key}"
    claimed = redis_client.setnx(key, job_id)
    if claimed:
        if ttl:
            redis_client.expire(key, ttl)
        return True, None
    existing = redis_client.get(key)
    if isinstance(existing, bytes):
        existing = existing.decode("utf-8")
    return False, existing


def claim_chunk_seen(
    redis_client,
    chunk_id: str,
    ttl_sec: Optional[int] = None,
) -> bool:
    ttl = ttl_sec or int(os.environ.get("CHUNK_SEEN_TTL_SEC", DEFAULT_CHUNK_SEEN_TTL_SEC))
    key = f"chunk_seen:{chunk_id}"
    claimed = redis_client.setnx(key, 1)
    if claimed and ttl:
        redis_client.expire(key, ttl)
    return bool(claimed)

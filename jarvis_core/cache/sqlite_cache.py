"""SQLite-based Persistent Cache for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.3: 永続キャッシュ
Provides LRU eviction, TTL management, and thread-safe access.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    accessed_at: float
    ttl_seconds: int | None = None
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return time.time() > (self.created_at + self.ttl_seconds)


class SQLiteCache:
    """SQLite-based persistent cache with LRU eviction.

    Features:
    - Thread-safe access
    - LRU eviction when max size reached
    - TTL support
    - Namespace support for organizing different cache types
    """

    def __init__(
        self,
        db_path: Path | None = None,
        max_size_mb: int = 500,
        default_ttl_seconds: int | None = None,
    ):
        self.db_path = db_path or Path.home() / ".jarvis" / "cache.db"
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl_seconds
        self._local = threading.local()

        # Initialize database
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Get database cursor with automatic commit."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    value BLOB NOT NULL,
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    ttl_seconds INTEGER,
                    size_bytes INTEGER NOT NULL
                )
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_namespace
                ON cache(namespace)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_accessed_at
                ON cache(accessed_at)
            """
            )
        logger.info(f"SQLite cache initialized at {self.db_path}")

    def _hash_key(self, key: str) -> str:
        """Hash key to ensure consistent format."""
        return hashlib.sha256(key.encode()).hexdigest()

    def get(
        self,
        key: str,
        namespace: str = "default",
    ) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key.
            namespace: Cache namespace.

        Returns:
            Cached value or None if not found/expired.
        """
        hashed_key = self._hash_key(f"{namespace}:{key}")

        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM cache WHERE key = ?", (hashed_key,))
            row = cursor.fetchone()

            if row is None:
                return None

            # Check TTL
            if row["ttl_seconds"] is not None:
                if time.time() > (row["created_at"] + row["ttl_seconds"]):
                    # Expired, delete and return None
                    cursor.execute("DELETE FROM cache WHERE key = ?", (hashed_key,))
                    return None

            # Update access time (LRU)
            cursor.execute(
                "UPDATE cache SET accessed_at = ? WHERE key = ?", (time.time(), hashed_key)
            )

            # Deserialize value
            try:
                return json.loads(row["value"])
            except json.JSONDecodeError:
                return row["value"]

    def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl_seconds: int | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            namespace: Cache namespace.
            ttl_seconds: Time-to-live in seconds.
        """
        hashed_key = self._hash_key(f"{namespace}:{key}")
        ttl = ttl_seconds or self.default_ttl

        # Serialize value
        try:
            serialized = json.dumps(value)
        except (TypeError, ValueError):
            serialized = str(value)

        size_bytes = len(serialized.encode())
        now = time.time()

        # Evict if necessary
        self._evict_if_needed(size_bytes)

        with self._cursor() as cursor:
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache
                (key, namespace, value, created_at, accessed_at, ttl_seconds, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (hashed_key, namespace, serialized, now, now, ttl, size_bytes),
            )

    def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete value from cache.

        Returns:
            True if key was deleted.
        """
        hashed_key = self._hash_key(f"{namespace}:{key}")

        with self._cursor() as cursor:
            cursor.execute("DELETE FROM cache WHERE key = ?", (hashed_key,))
            return cursor.rowcount > 0

    def clear(self, namespace: str | None = None) -> int:
        """Clear cache.

        Args:
            namespace: If provided, clear only this namespace.

        Returns:
            Number of entries deleted.
        """
        with self._cursor() as cursor:
            if namespace:
                cursor.execute("DELETE FROM cache WHERE namespace = ?", (namespace,))
            else:
                cursor.execute("DELETE FROM cache")
            return cursor.rowcount

    def _evict_if_needed(self, required_bytes: int) -> None:
        """Evict LRU entries if cache is too large."""
        with self._cursor() as cursor:
            # Get current size
            cursor.execute("SELECT SUM(size_bytes) as total FROM cache")
            row = cursor.fetchone()
            current_size = row["total"] or 0

            if current_size + required_bytes <= self.max_size_bytes:
                return

            # Delete expired entries first
            cursor.execute(
                "DELETE FROM cache WHERE ttl_seconds IS NOT NULL "
                "AND (created_at + ttl_seconds) < ?",
                (time.time(),),
            )

            # Recalculate size
            cursor.execute("SELECT SUM(size_bytes) as total FROM cache")
            row = cursor.fetchone()
            current_size = row["total"] or 0

            if current_size + required_bytes <= self.max_size_bytes:
                return

            # Delete LRU entries until we have space
            target_size = int(self.max_size_bytes * 0.8)  # Free 20% extra

            cursor.execute(
                """
                DELETE FROM cache WHERE key IN (
                    SELECT key FROM cache
                    ORDER BY accessed_at ASC
                    LIMIT (SELECT COUNT(*) * 0.2 FROM cache)
                )
            """
            )

            logger.info(f"Evicted LRU entries, freed {current_size - target_size} bytes")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as count,
                    SUM(size_bytes) as total_bytes,
                    COUNT(DISTINCT namespace) as namespaces
                FROM cache
            """
            )
            row = cursor.fetchone()

            return {
                "entries": row["count"],
                "size_bytes": row["total_bytes"] or 0,
                "size_mb": (row["total_bytes"] or 0) / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "namespaces": row["namespaces"],
                "db_path": str(self.db_path),
            }

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# Singleton instance
_default_cache: SQLiteCache | None = None


def get_cache() -> SQLiteCache:
    """Get default cache instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = SQLiteCache()
    return _default_cache
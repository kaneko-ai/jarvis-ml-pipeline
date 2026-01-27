"""Simple file-based key-value cache (Phase 24).

Used for caching embeddings and other expensive computations.
"""

import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Any, Optional


class KVCache:
    """Persistent Key-Value Store derived from SQLite."""

    def __init__(self, cache_dir: Path, name: str = "embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / f"{name}.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return None
            return None

    def set(self, key: str, value: Any):
        json_val = json.dumps(value)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)", (key, json_val))
            conn.commit()

    def generate_key(self, *args, **kwargs) -> str:
        """Generate a stable hash key from inputs."""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

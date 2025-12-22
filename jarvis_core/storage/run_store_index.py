"""RunStore Index.

Per RP-147, provides indexed run storage for queries.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime


@dataclass
class RunRecord:
    """A run record."""

    run_id: str
    status: str
    category: str
    created_at: str
    query: str
    docs_count: int
    claims_count: int
    duration_seconds: float


class RunStoreIndex:
    """SQLite-backed run index for fast queries."""

    def __init__(self, db_path: str = "data/runs/runs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                status TEXT,
                category TEXT,
                created_at TEXT,
                query TEXT,
                docs_count INTEGER,
                claims_count INTEGER,
                duration_seconds REAL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON runs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON runs(created_at)")
        conn.commit()
        conn.close()

    def add(self, record: RunRecord) -> None:
        """Add a run record."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO runs 
            (run_id, status, category, created_at, query, docs_count, claims_count, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.run_id,
            record.status,
            record.category,
            record.created_at,
            record.query,
            record.docs_count,
            record.claims_count,
            record.duration_seconds,
        ))
        conn.commit()
        conn.close()

    def get(self, run_id: str) -> Optional[RunRecord]:
        """Get a run by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        )
        row = cur.fetchone()
        conn.close()

        if row:
            return RunRecord(*row)
        return None

    def list_recent(self, limit: int = 10) -> List[RunRecord]:
        """List recent runs."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return [RunRecord(*row) for row in rows]

    def list_by_status(self, status: str, limit: int = 100) -> List[RunRecord]:
        """List runs by status."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "SELECT * FROM runs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        )
        rows = cur.fetchall()
        conn.close()
        return [RunRecord(*row) for row in rows]

    def count_by_status(self) -> Dict[str, int]:
        """Count runs by status."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "SELECT status, COUNT(*) FROM runs GROUP BY status"
        )
        result = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return result

    def search(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[RunRecord]:
        """Search runs with filters."""
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if since:
            conditions.append("created_at >= ?")
            params.append(since)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM runs WHERE {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [RunRecord(*row) for row in rows]

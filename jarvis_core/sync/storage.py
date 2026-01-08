from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis_core.sync.schema import QueueItem, QueueItemStatus

logger = logging.getLogger(__name__)

class SyncQueueStorage:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".jarvis" / "sync_queue.db"
        
        self._db_path = Path(db_path)
        self._initialize_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def _initialize_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    params TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    error TEXT,
                    result TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON sync_queue(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON sync_queue(created_at)")

    def add(self, item: QueueItem) -> None:
        # If item needs ID:
        if not item.id:
            item.id = str(uuid.uuid4())
            
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sync_queue 
                (id, operation, params, status, created_at, updated_at, max_retries, retry_count, error, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.operation,
                    json.dumps(item.params),
                    item.status.value,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    item.max_retries,
                    item.retry_count,
                    item.error,
                    json.dumps(item.result) if item.result else None
                ),
            )
        logger.debug(f"Enqueued: {item.id} ({item.operation})")

    def get_pending(self, limit: int = 100) -> List[QueueItem]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM sync_queue 
                WHERE status IN (?, ?)
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (QueueItemStatus.PENDING.value, QueueItemStatus.RETRYING.value, limit),
            ).fetchall()
            return [self._row_to_item(row) for row in rows]

    def update_status(self, item_id: str, status: QueueItemStatus, error: Optional[str] = None) -> None:
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE sync_queue 
                SET status = ?, updated_at = ?, error = ?
                WHERE id = ?
                """,
                (status.value, now, error, item_id),
            )

    def _row_to_item(self, row: sqlite3.Row) -> QueueItem:
        return QueueItem(
            id=row["id"],
            operation=row["operation"],
            params=json.loads(row["params"]),
            status=QueueItemStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            error=row["error"],
            result=json.loads(row["result"]) if row["result"] else None,
        )
        
    def get_queue_status(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM sync_queue GROUP BY status"
            ).fetchall()
            return {row["status"]: row["count"] for row in rows}

    def get_item(self, item_id: str) -> Optional[QueueItem]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM sync_queue WHERE id = ?", (item_id,)).fetchone()
            return self._row_to_item(row) if row else None

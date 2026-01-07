"""Sync Queue Module.

SQLite-backed queue for offline sync operations.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.5.5
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SyncItemStatus(Enum):
    """Status of a sync queue item."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class SyncItem:
    """An item in the sync queue."""
    
    item_id: str
    operation: str  # e.g., "search", "fetch", "upload"
    payload: Dict[str, Any]
    status: SyncItemStatus = SyncItemStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "item_id": self.item_id,
            "operation": self.operation,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "result": self.result,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncItem":
        """Create from dictionary."""
        return cls(
            item_id=data["item_id"],
            operation=data["operation"],
            payload=data.get("payload", {}),
            status=SyncItemStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_message=data.get("error_message"),
            result=data.get("result"),
        )


@dataclass
class QueueStats:
    """Statistics about the sync queue."""
    
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    failed: int = 0
    retrying: int = 0
    oldest_pending_age_seconds: Optional[float] = None


class SyncQueue:
    """SQLite-backed sync queue for offline operations.
    
    Provides a persistent queue for operations that need to be synced
    when network connectivity is restored.
    
    Example:
        >>> queue = SyncQueue()
        >>> item_id = queue.enqueue("search", {"query": "cancer research"})
        >>> item = queue.dequeue()
        >>> if item:
        ...     # Process the item
        ...     queue.mark_complete(item.item_id, result={"papers": [...]})
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the sync queue.
        
        Args:
            db_path: Path to SQLite database. Defaults to ~/.jarvis/sync_queue.db
        """
        if db_path is None:
            db_path = Path.home() / ".jarvis" / "sync_queue.db"
        
        self._db_path = Path(db_path)
        self._initialize_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def _initialize_db(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    item_id TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    error_message TEXT,
                    result TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_queue_status 
                ON sync_queue(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_queue_created 
                ON sync_queue(created_at)
            """)
    
    def enqueue(
        self,
        operation: str,
        payload: Dict[str, Any],
        max_retries: int = 3,
    ) -> str:
        """Add an item to the queue.
        
        Args:
            operation: Type of operation (e.g., "search", "fetch")
            payload: Operation payload
            max_retries: Maximum retry attempts
            
        Returns:
            Generated item ID
        """
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sync_queue 
                (item_id, operation, payload, status, created_at, updated_at, max_retries)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    operation,
                    json.dumps(payload),
                    SyncItemStatus.PENDING.value,
                    now,
                    now,
                    max_retries,
                ),
            )
        
        logger.debug(f"Enqueued sync item: {item_id} ({operation})")
        return item_id
    
    def dequeue(self) -> Optional[SyncItem]:
        """Get the next pending item from the queue.
        
        Marks the item as IN_PROGRESS.
        
        Returns:
            Next pending SyncItem or None if queue is empty
        """
        with self._get_connection() as conn:
            # Find oldest pending or retrying item
            row = conn.execute(
                """
                SELECT * FROM sync_queue 
                WHERE status IN (?, ?)
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (SyncItemStatus.PENDING.value, SyncItemStatus.RETRYING.value),
            ).fetchone()
            
            if not row:
                return None
            
            item_id = row["item_id"]
            
            # Mark as in progress
            conn.execute(
                """
                UPDATE sync_queue 
                SET status = ?, updated_at = ?
                WHERE item_id = ?
                """,
                (SyncItemStatus.IN_PROGRESS.value, datetime.now().isoformat(), item_id),
            )
            
            # Build SyncItem
            return SyncItem(
                item_id=row["item_id"],
                operation=row["operation"],
                payload=json.loads(row["payload"]),
                status=SyncItemStatus.IN_PROGRESS,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.now(),
                retry_count=row["retry_count"],
                max_retries=row["max_retries"],
                error_message=row["error_message"],
                result=json.loads(row["result"]) if row["result"] else None,
            )
    
    def mark_complete(
        self,
        item_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark an item as completed.
        
        Args:
            item_id: ID of the item to mark complete
            result: Optional result data
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE sync_queue 
                SET status = ?, updated_at = ?, result = ?
                WHERE item_id = ?
                """,
                (
                    SyncItemStatus.COMPLETED.value,
                    datetime.now().isoformat(),
                    json.dumps(result) if result else None,
                    item_id,
                ),
            )
        
        logger.debug(f"Marked sync item complete: {item_id}")
    
    def mark_failed(
        self,
        item_id: str,
        error_message: str,
        retry: bool = True,
    ) -> None:
        """Mark an item as failed.
        
        Args:
            item_id: ID of the item
            error_message: Error description
            retry: Whether to retry if retries remaining
        """
        with self._get_connection() as conn:
            # Get current state
            row = conn.execute(
                "SELECT retry_count, max_retries FROM sync_queue WHERE item_id = ?",
                (item_id,),
            ).fetchone()
            
            if not row:
                return
            
            retry_count = row["retry_count"] + 1
            max_retries = row["max_retries"]
            
            if retry and retry_count < max_retries:
                status = SyncItemStatus.RETRYING
            else:
                status = SyncItemStatus.FAILED
            
            conn.execute(
                """
                UPDATE sync_queue 
                SET status = ?, updated_at = ?, retry_count = ?, error_message = ?
                WHERE item_id = ?
                """,
                (
                    status.value,
                    datetime.now().isoformat(),
                    retry_count,
                    error_message,
                    item_id,
                ),
            )
        
        logger.debug(f"Marked sync item failed: {item_id} ({error_message})")
    
    def get_item(self, item_id: str) -> Optional[SyncItem]:
        """Get an item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            SyncItem or None if not found
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sync_queue WHERE item_id = ?",
                (item_id,),
            ).fetchone()
            
            if not row:
                return None
            
            return SyncItem(
                item_id=row["item_id"],
                operation=row["operation"],
                payload=json.loads(row["payload"]),
                status=SyncItemStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                retry_count=row["retry_count"],
                max_retries=row["max_retries"],
                error_message=row["error_message"],
                result=json.loads(row["result"]) if row["result"] else None,
            )
    
    def stats(self) -> QueueStats:
        """Get queue statistics.
        
        Returns:
            QueueStats with counts by status
        """
        with self._get_connection() as conn:
            # Count by status
            rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM sync_queue GROUP BY status"
            ).fetchall()
            
            counts: Dict[str, int] = {row["status"]: row["count"] for row in rows}
            
            # Get oldest pending item age
            oldest = conn.execute(
                """
                SELECT created_at FROM sync_queue 
                WHERE status = ? 
                ORDER BY created_at ASC 
                LIMIT 1
                """,
                (SyncItemStatus.PENDING.value,),
            ).fetchone()
            
            oldest_age = None
            if oldest:
                created = datetime.fromisoformat(oldest["created_at"])
                oldest_age = (datetime.now() - created).total_seconds()
            
            return QueueStats(
                total=sum(counts.values()),
                pending=counts.get(SyncItemStatus.PENDING.value, 0),
                in_progress=counts.get(SyncItemStatus.IN_PROGRESS.value, 0),
                completed=counts.get(SyncItemStatus.COMPLETED.value, 0),
                failed=counts.get(SyncItemStatus.FAILED.value, 0),
                retrying=counts.get(SyncItemStatus.RETRYING.value, 0),
                oldest_pending_age_seconds=oldest_age,
            )
    
    def clear_completed(self, older_than_hours: int = 24) -> int:
        """Remove completed items older than specified hours.
        
        Args:
            older_than_hours: Remove items older than this
            
        Returns:
            Number of items removed
        """
        cutoff = datetime.now().timestamp() - (older_than_hours * 3600)
        cutoff_str = datetime.fromtimestamp(cutoff).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM sync_queue 
                WHERE status = ? AND updated_at < ?
                """,
                (SyncItemStatus.COMPLETED.value, cutoff_str),
            )
            count = cursor.rowcount
        
        if count > 0:
            logger.info(f"Cleared {count} completed sync items")
        
        return count
    
    def get_pending_items(self, limit: int = 100) -> List[SyncItem]:
        """Get all pending items.
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of pending SyncItems
        """
        items = []
        
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM sync_queue 
                WHERE status IN (?, ?)
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (SyncItemStatus.PENDING.value, SyncItemStatus.RETRYING.value, limit),
            ).fetchall()
            
            for row in rows:
                items.append(SyncItem(
                    item_id=row["item_id"],
                    operation=row["operation"],
                    payload=json.loads(row["payload"]),
                    status=SyncItemStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    retry_count=row["retry_count"],
                    max_retries=row["max_retries"],
                    error_message=row["error_message"],
                    result=json.loads(row["result"]) if row["result"] else None,
                ))
        
        return items

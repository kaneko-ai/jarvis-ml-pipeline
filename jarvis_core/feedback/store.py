"""Feedback Store (Phase 36).

Persists user feedback for active learning.
"""

from __future__ import annotations

import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class FeedbackItem:
    """A single feedback entry."""
    query_id: str
    doc_id: str
    rating: int  # 1 (relevant) to 5 (highly relevant), or 0 (irrelevant)
    timestamp: float
    user_id: str = "default_user"
    metadata: Dict[str, Any] = None

class FeedbackStore:
    """Local JSONL storage for feedback."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.data_dir / "feedback.jsonl"

    def log_feedback(self, query_id: str, doc_id: str, rating: int, metadata: Dict = None):
        """Log a feedback event."""
        item = FeedbackItem(
            query_id=query_id,
            doc_id=doc_id,
            rating=rating,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        try:
            with open(self.feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(item)) + "\n")
            logger.info(f"Logged feedback for query {query_id} doc {doc_id}")
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")

    def load_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Load recent feedback items."""
        items = []
        if not self.feedback_file.exists():
            return []
            
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        items.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to load feedback: {e}")
            
        return items

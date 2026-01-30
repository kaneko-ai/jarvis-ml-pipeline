"""
JARVIS Human-in-the-Loop (HITL)

M7: HITL機能
- レビューキュー
- 承認フロー
- フィードバック回収
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """レビューステータス."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewType(Enum):
    """レビュータイプ."""

    CLAIM_VALIDATION = "claim_validation"
    EVIDENCE_VERIFICATION = "evidence_verification"
    ROB_ASSESSMENT = "rob_assessment"
    FINAL_APPROVAL = "final_approval"


@dataclass
class ReviewItem:
    """レビューアイテム."""

    item_id: str
    run_id: str
    review_type: ReviewType
    content: dict[str, Any]
    status: ReviewStatus = ReviewStatus.PENDING
    priority: int = 5  # 1-10, 10 = highest
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    assigned_to: str | None = None
    reviewed_at: str | None = None
    reviewer_notes: str = ""
    feedback: dict[str, Any] = field(default_factory=dict)


@dataclass
class Feedback:
    """フィードバック."""

    feedback_id: str
    item_id: str
    reviewer: str
    rating: int  # 1-5
    accuracy_score: float | None = None
    completeness_score: float | None = None
    comments: str = ""
    corrections: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ReviewQueue:
    """レビューキュー."""

    def __init__(self, queue_path: str = "artifacts/review_queue.jsonl"):
        """
        初期化.

        Args:
            queue_path: キューファイルパス
        """
        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._item_counter = 0

    def add_item(
        self, run_id: str, review_type: ReviewType, content: dict[str, Any], priority: int = 5
    ) -> ReviewItem:
        """
        アイテムを追加.

        Args:
            run_id: 実行ID
            review_type: レビュータイプ
            content: コンテンツ
            priority: 優先度

        Returns:
            レビューアイテム
        """
        self._item_counter += 1

        item = ReviewItem(
            item_id=f"REV-{run_id[:8]}-{self._item_counter:04d}",
            run_id=run_id,
            review_type=review_type,
            content=content,
            priority=priority,
        )

        self._save_item(item)
        logger.info(f"Review item added: {item.item_id}")

        return item

    def _save_item(self, item: ReviewItem):
        """アイテムを保存."""
        data = asdict(item)
        data["review_type"] = item.review_type.value
        data["status"] = item.status.value

        with open(self.queue_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def get_pending_items(self, limit: int = 10) -> list[ReviewItem]:
        """未処理アイテムを取得."""
        items = []

        if not self.queue_path.exists():
            return items

        with open(self.queue_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get("status") == "pending":
                        item = ReviewItem(
                            item_id=data["item_id"],
                            run_id=data["run_id"],
                            review_type=ReviewType(data["review_type"]),
                            content=data["content"],
                            status=ReviewStatus(data["status"]),
                            priority=data.get("priority", 5),
                        )
                        items.append(item)

        # 優先度でソート
        items.sort(key=lambda x: x.priority, reverse=True)
        return items[:limit]

    def assign_item(self, item_id: str, reviewer: str) -> bool:
        """アイテムを割り当て."""
        # 実際の実装では、状態を更新
        logger.info(f"Item {item_id} assigned to {reviewer}")
        return True

    def submit_review(
        self,
        item_id: str,
        status: ReviewStatus,
        reviewer: str,
        notes: str = "",
        feedback: dict[str, Any] | None = None,
    ) -> bool:
        """
        レビューを提出.

        Args:
            item_id: アイテムID
            status: 新しいステータス
            reviewer: レビュアー
            notes: ノート
            feedback: フィードバック

        Returns:
            成功したか
        """
        review_result = {
            "item_id": item_id,
            "status": status.value,
            "reviewer": reviewer,
            "notes": notes,
            "feedback": feedback or {},
            "reviewed_at": datetime.now().isoformat(),
        }

        with open(self.queue_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(review_result, ensure_ascii=False) + "\n")

        logger.info(f"Review submitted for {item_id}: {status.value}")
        return True


class FeedbackCollector:
    """フィードバック収集器."""

    def __init__(self, feedback_path: str = "artifacts/feedback.jsonl"):
        """
        初期化.

        Args:
            feedback_path: フィードバックファイルパス
        """
        self.feedback_path = Path(feedback_path)
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        self._feedback_counter = 0

    def collect(
        self,
        item_id: str,
        reviewer: str,
        rating: int,
        accuracy_score: float | None = None,
        completeness_score: float | None = None,
        comments: str = "",
        corrections: dict[str, Any] | None = None,
    ) -> Feedback:
        """
        フィードバックを収集.

        Args:
            item_id: アイテムID
            reviewer: レビュアー
            rating: 評価（1-5）
            accuracy_score: 正確性スコア
            completeness_score: 完全性スコア
            comments: コメント
            corrections: 修正内容

        Returns:
            フィードバック
        """
        self._feedback_counter += 1

        feedback = Feedback(
            feedback_id=f"FB-{self._feedback_counter:06d}",
            item_id=item_id,
            reviewer=reviewer,
            rating=min(max(rating, 1), 5),
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            comments=comments,
            corrections=corrections or {},
        )

        with open(self.feedback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(feedback), ensure_ascii=False) + "\n")

        return feedback

    def get_statistics(self) -> dict[str, Any]:
        """統計を取得."""
        if not self.feedback_path.exists():
            return {"total": 0, "avg_rating": 0}

        ratings = []
        accuracy_scores = []

        with open(self.feedback_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if "rating" in data:
                        ratings.append(data["rating"])
                    if data.get("accuracy_score"):
                        accuracy_scores.append(data["accuracy_score"])

        return {
            "total": len(ratings),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0,
            "avg_accuracy": (
                sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else None
            ),
        }


# グローバルインスタンス
_review_queue: ReviewQueue | None = None
_feedback_collector: FeedbackCollector | None = None


def get_review_queue() -> ReviewQueue:
    """レビューキューを取得."""
    global _review_queue
    if _review_queue is None:
        _review_queue = ReviewQueue()
    return _review_queue


def get_feedback_collector() -> FeedbackCollector:
    """フィードバック収集器を取得."""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector
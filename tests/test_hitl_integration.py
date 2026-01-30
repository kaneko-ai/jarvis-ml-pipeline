"""
JARVIS M7 HITL & Integration Tests

M7: Human-in-the-loopとエコシステム統合のテスト
"""

from jarvis_core.ops.hitl import (
    FeedbackCollector,
    ReviewQueue,
    ReviewStatus,
    ReviewType,
)
from jarvis_core.ops.integration import (
    ExternalServiceConnector,
    PluginAPIRegistry,
    WebhookConfig,
    WebhookEvent,
    WebhookManager,
)
from tempfile import TemporaryDirectory
import pytest


class TestReviewQueue:
    """レビューキューテスト."""

    def test_add_item(self):
        """アイテム追加が動作すること."""
        with TemporaryDirectory() as tmpdir:
            queue = ReviewQueue(queue_path=f"{tmpdir}/queue.jsonl")

            item = queue.add_item(
                run_id="test_run_123",
                review_type=ReviewType.CLAIM_VALIDATION,
                content={"claim": "Test claim"},
                priority=7,
            )

            assert item.item_id.startswith("REV-")
            assert item.status == ReviewStatus.PENDING
            assert item.priority == 7

    def test_get_pending_items(self):
        """未処理アイテム取得が動作すること."""
        with TemporaryDirectory() as tmpdir:
            queue = ReviewQueue(queue_path=f"{tmpdir}/queue.jsonl")

            queue.add_item("run1", ReviewType.CLAIM_VALIDATION, {"a": 1}, priority=5)
            queue.add_item("run2", ReviewType.EVIDENCE_VERIFICATION, {"b": 2}, priority=9)

            pending = queue.get_pending_items()

            assert len(pending) == 2
            assert pending[0].priority >= pending[1].priority

    def test_submit_review(self):
        """レビュー提出が動作すること."""
        with TemporaryDirectory() as tmpdir:
            queue = ReviewQueue(queue_path=f"{tmpdir}/queue.jsonl")

            item = queue.add_item("run1", ReviewType.ROB_ASSESSMENT, {})
            result = queue.submit_review(
                item.item_id, ReviewStatus.APPROVED, "reviewer1", notes="Looks good"
            )

            assert result is True


class TestFeedbackCollector:
    """フィードバック収集テスト."""

    def test_collect_feedback(self):
        """フィードバック収集が動作すること."""
        with TemporaryDirectory() as tmpdir:
            collector = FeedbackCollector(feedback_path=f"{tmpdir}/fb.jsonl")

            feedback = collector.collect(
                item_id="REV-001",
                reviewer="reviewer1",
                rating=4,
                accuracy_score=0.9,
                comments="Good extraction",
            )

            assert feedback.feedback_id.startswith("FB-")
            assert feedback.rating == 4

    def test_statistics(self):
        """統計取得が動作すること."""
        with TemporaryDirectory() as tmpdir:
            collector = FeedbackCollector(feedback_path=f"{tmpdir}/fb.jsonl")

            collector.collect("item1", "r1", 4)
            collector.collect("item2", "r2", 5)
            collector.collect("item3", "r1", 3)

            stats = collector.get_statistics()

            assert stats["total"] == 3
            assert stats["avg_rating"] == 4.0


class TestWebhookManager:
    """Webhookマネージャーテスト."""

    def test_register_webhook(self):
        """Webhook登録が動作すること."""
        manager = WebhookManager(config_path="nonexistent.json")

        config = WebhookConfig(
            webhook_id="wh1",
            url="https://example.com/webhook",
            secret="secret123",
            events=[WebhookEvent.RUN_COMPLETED],
        )

        manager.register_webhook(config)

        triggered = manager.trigger(WebhookEvent.RUN_COMPLETED, "run_123", {"status": "completed"})

        assert "wh1" in triggered

    def test_trigger_filters_events(self):
        """イベントフィルタが動作すること."""
        manager = WebhookManager(config_path="nonexistent.json")

        config = WebhookConfig(
            webhook_id="wh2",
            url="https://example.com/webhook",
            secret="secret",
            events=[WebhookEvent.RUN_FAILED],  # RUN_COMPLETEDではない
        )

        manager.register_webhook(config)

        triggered = manager.trigger(WebhookEvent.RUN_COMPLETED, "run_456", {})

        assert "wh2" not in triggered


class TestPluginAPIRegistry:
    """プラグインAPIレジストリテスト."""

    def test_register_api(self):
        """API登録が動作すること."""
        registry = PluginAPIRegistry()

        def handler(request):
            return {"status": "ok"}

        registry.register("GET", "/api/status", handler, "Get status")

        retrieved = registry.get_handler("GET", "/api/status")
        assert retrieved is not None

    def test_openapi_spec(self):
        """OpenAPI仕様が生成されること."""
        registry = PluginAPIRegistry()
        registry.register("POST", "/api/data", lambda x: x, "Post data")

        spec = registry.get_openapi_spec()

        assert spec["openapi"] == "3.0.0"
        assert "/api/data" in spec["paths"]


class TestExternalServiceConnector:
    """外部サービスコネクターテスト."""

    def test_register_service(self):
        """サービス登録が動作すること."""
        connector = ExternalServiceConnector()

        connector.register_service("my_zotero", "zotero", {"api_key": "xxx"})

        service = connector.get_service("my_zotero")
        assert service is not None
        assert service["type"] == "zotero"

    def test_list_services(self):
        """サービス一覧が取得できること."""
        connector = ExternalServiceConnector()

        connector.register_service("s1", "slack", {})
        connector.register_service("s2", "notion", {})

        services = connector.list_services()
        assert len(services) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
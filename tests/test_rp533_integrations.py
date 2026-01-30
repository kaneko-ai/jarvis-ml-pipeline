"""Tests for RP-533, RP-534: Slack and PagerDuty integrations."""

import pytest

pytestmark = pytest.mark.core


class TestSlackClient:
    """Tests for Slack integration (RP-533)."""

    def test_client_init(self):
        """Test SlackClient initialization."""
        from jarvis_core.integrations.slack import SlackClient

        client = SlackClient(token="test-token")
        assert client.is_enabled()
        assert client.default_channel == "#jarvis-alerts"

    def test_client_disabled_without_token(self):
        """Test client is disabled without token."""
        from jarvis_core.integrations.slack import SlackClient

        client = SlackClient(token="")
        assert not client.is_enabled()

    def test_send_message(self):
        """Test sending a message."""
        from jarvis_core.integrations.slack import MessageType, SlackClient

        client = SlackClient(token="test-token")
        result = client.send_message("Test message", message_type=MessageType.SUCCESS)

        assert result is not None
        assert result["ok"] is True

    def test_send_alert(self):
        """Test sending an alert."""
        from jarvis_core.integrations.slack import SlackClient

        client = SlackClient(token="test-token")
        result = client.send_alert(
            title="Test Alert",
            description="Test description",
            severity="warning",
            fields={"key": "value"},
        )

        assert result is not None
        assert result["ok"] is True

    def test_send_pipeline_update(self):
        """Test pipeline status update."""
        from jarvis_core.integrations.slack import SlackClient

        client = SlackClient(token="test-token")
        result = client.send_pipeline_update(
            pipeline_id="test-123",
            status="running",
            progress=0.5,
        )

        assert result is not None

    def test_message_types(self):
        """Test different message types."""
        from jarvis_core.integrations.slack import MessageType

        assert MessageType.INFO.value == "info"
        assert MessageType.SUCCESS.value == "success"
        assert MessageType.WARNING.value == "warning"
        assert MessageType.ERROR.value == "error"
        assert MessageType.ALERT.value == "alert"

    def test_global_client(self):
        """Test global Slack client."""
        from jarvis_core.integrations.slack import get_slack_client

        client1 = get_slack_client()
        client2 = get_slack_client()
        assert client1 is client2


class TestPagerDutyClient:
    """Tests for PagerDuty integration (RP-534)."""

    def test_client_init(self):
        """Test PagerDutyClient initialization."""
        from jarvis_core.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient(routing_key="test-key")
        assert client.is_enabled()
        assert client.service_name == "jarvis"

    def test_client_disabled_without_key(self):
        """Test client is disabled without routing key."""
        from jarvis_core.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient(routing_key="")
        assert not client.is_enabled()

    def test_trigger_event(self):
        """Test triggering an event."""
        from jarvis_core.integrations.pagerduty import PagerDutyClient, Severity

        client = PagerDutyClient(routing_key="test-key")
        result = client.trigger(
            summary="Test alert",
            severity=Severity.ERROR,
        )

        assert result is not None
        assert result["status"] == "success"

    def test_acknowledge_event(self):
        """Test acknowledging an event."""
        from jarvis_core.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient(routing_key="test-key")
        result = client.acknowledge(dedup_key="test-dedup")

        assert result is not None

    def test_resolve_event(self):
        """Test resolving an event."""
        from jarvis_core.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient(routing_key="test-key")
        result = client.resolve(dedup_key="test-dedup")

        assert result is not None

    def test_trigger_alert_with_labels(self):
        """Test triggering alert with Prometheus-style labels."""
        from jarvis_core.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient(routing_key="test-key")
        result = client.trigger_alert(
            alert_name="HighErrorRate",
            description="Error rate exceeded threshold",
            severity="critical",
            labels={"service": "api", "env": "prod"},
            annotations={"runbook_url": "https://docs.example.com/runbook"},
        )

        assert result is not None

    def test_severity_enum(self):
        """Test severity enum values."""
        from jarvis_core.integrations.pagerduty import Severity

        assert Severity.CRITICAL.value == "critical"
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_global_client(self):
        """Test global PagerDuty client."""
        from jarvis_core.integrations.pagerduty import get_pagerduty_client

        client1 = get_pagerduty_client()
        client2 = get_pagerduty_client()
        assert client1 is client2


class TestChaosEngineering:
    """Tests for Chaos Engineering (RP-580)."""

    def test_chaos_monkey_init(self):
        """Test ChaosMonkey initialization."""
        from jarvis_core.reliability.chaos import ChaosConfig, ChaosMonkey

        config = ChaosConfig(enabled=True, probability=0.5)
        monkey = ChaosMonkey(config=config)

        assert monkey.is_enabled()

    def test_chaos_disabled_by_default(self):
        """Test chaos is disabled by default."""
        from jarvis_core.reliability.chaos import ChaosMonkey

        monkey = ChaosMonkey()
        assert not monkey.is_enabled()

    def test_start_stop_experiment(self):
        """Test starting and stopping experiments."""
        from jarvis_core.reliability.chaos import ChaosMonkey, ChaosType

        monkey = ChaosMonkey()
        monkey.enable()

        exp = monkey.start_experiment("test-exp", ChaosType.LATENCY)
        assert exp.experiment_id is not None

        monkey.stop_experiment(exp.experiment_id)
        results = monkey.get_experiment_results(exp.experiment_id)

        assert results is not None
        assert results["ended_at"] is not None


class TestFeatureFlags:
    """Tests for Feature Flags (RP-525)."""

    def test_create_flag(self):
        """Test creating a feature flag."""
        from jarvis_core.config.feature_flags import FeatureFlagManager

        manager = FeatureFlagManager()
        flag = manager.create_flag("new_feature", "Test feature")

        assert flag.name == "new_feature"
        assert not flag.enabled

    def test_enable_disable_flag(self):
        """Test enabling and disabling flags."""
        from jarvis_core.config.feature_flags import FeatureFlagManager

        manager = FeatureFlagManager()
        manager.create_flag("test_flag")

        manager.enable_flag("test_flag")
        assert manager.is_enabled("test_flag")

        manager.disable_flag("test_flag")
        assert not manager.is_enabled("test_flag")

    def test_percentage_rollout(self):
        """Test percentage-based rollout."""
        from jarvis_core.config.feature_flags import FeatureFlagManager

        manager = FeatureFlagManager()
        manager.create_flag("gradual_feature")
        manager.set_percentage("gradual_feature", 0.5)

        # Should be deterministic per user
        result1 = manager.is_enabled("gradual_feature", user_id="user-123")
        result2 = manager.is_enabled("gradual_feature", user_id="user-123")
        assert result1 == result2

    def test_user_list_targeting(self):
        """Test user list targeting."""
        from jarvis_core.config.feature_flags import FeatureFlagManager

        manager = FeatureFlagManager()
        manager.create_flag("beta_feature")
        manager.add_users("beta_feature", ["user-1", "user-2"])

        assert manager.is_enabled("beta_feature", user_id="user-1")
        assert not manager.is_enabled("beta_feature", user_id="user-3")
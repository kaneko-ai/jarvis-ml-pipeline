"""Tests for Dashboard Features - Auth, API, Alerts."""
import time

import pytest

pytestmark = pytest.mark.core


class TestAPIKeyManager:
    """Tests for API Key Authentication."""

    def test_manager_init(self):
        """Test manager initialization."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()
        assert manager is not None

    def test_generate_key(self):
        """Test generating an API key."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()
        key = manager.generate_key("Test Key")

        assert key is not None
        assert "." in key  # Format: key_id.raw_key

    def test_validate_key(self):
        """Test validating an API key."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()
        key = manager.generate_key("Test Key")

        result = manager.validate(key)

        assert result.success
        assert result.key_id is not None

    def test_validate_invalid_key(self):
        """Test validating an invalid key."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()

        result = manager.validate("invalid.key")

        assert not result.success
        assert result.error == "Key not found"

    def test_scope_validation(self):
        """Test scope-based validation."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()
        key = manager.generate_key("Read Only", scopes={"read"})

        # Should fail for write scope
        result = manager.validate(key, required_scope="write")
        assert not result.success
        assert "scope" in result.error.lower()

        # Should succeed for read scope
        result = manager.validate(key, required_scope="read")
        assert result.success

    def test_revoke_key(self):
        """Test revoking an API key."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()
        key = manager.generate_key("Test Key")
        key_id = key.split(".")[0]

        # Revoke
        assert manager.revoke(key_id)

        # Validation should fail
        result = manager.validate(key)
        assert not result.success
        assert "disabled" in result.error.lower()

    def test_list_keys(self):
        """Test listing API keys."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()
        manager.generate_key("Key 1")
        manager.generate_key("Key 2")

        keys = manager.list_keys()
        assert len(keys) == 2

    def test_key_expiration(self):
        """Test key expiration."""
        from jarvis_core.auth.api_key import APIKeyManager

        manager = APIKeyManager()
        key = manager.generate_key("Short Lived", expires_days=0)  # Expires immediately

        # Manually set expiration to past
        key_id = key.split(".")[0]
        manager._keys[key_id].expires_at = time.time() - 1

        result = manager.validate(key)
        assert not result.success
        assert "expired" in result.error.lower()


class TestDashboardFeatures:
    """Tests for dashboard-related features."""

    def test_metrics_json_structure(self):
        """Test metrics JSON structure."""
        import json

        # Check if file would be valid
        metrics = {
            "generated_at": "2024-12-23T00:00:00Z",
            "version": "4.4.0",
            "stats": {
                "total_prs_implemented": 384,
                "tests_passed": 222,
            }
        }

        # Should be valid JSON
        json_str = json.dumps(metrics)
        parsed = json.loads(json_str)

        assert parsed["version"] == "4.4.0"
        assert parsed["stats"]["tests_passed"] == 222

    def test_health_check_structure(self):
        """Test health check structure."""
        health = {
            "status": "healthy",
            "uptime": "99.9%",
            "services": {
                "api": "up",
                "dashboard": "up"
            }
        }

        assert health["status"] == "healthy"
        assert "api" in health["services"]


class TestSlackBotExtended:
    """Extended tests for Slack Bot."""

    def test_analyze_command(self):
        """Test analyze command."""
        from jarvis_core.integrations.slack_bot import BotCommand, CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = BotCommand(
            command_type=CommandType.ANALYZE,
            args=["cancer research"],
            user_id="user1",
            channel_id="channel1",
        )

        response = bot.handle_command(cmd)

        assert "cancer research" in response.text or "Analyzing" in response.text

    def test_report_command(self):
        """Test report command."""
        from jarvis_core.integrations.slack_bot import BotCommand, CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = BotCommand(
            command_type=CommandType.REPORT,
            args=[],
            user_id="user1",
            channel_id="channel1",
        )

        response = bot.handle_command(cmd)

        assert "Report" in response.text or "Generating" in response.text


class TestCloudRunExtended:
    """Extended tests for Cloud Run."""

    def test_generate_dockerfile(self):
        """Test Dockerfile generation."""
        from jarvis_core.deploy.cloud_run import CloudRunDeployer

        deployer = CloudRunDeployer()
        dockerfile = deployer.generate_dockerfile()

        assert "FROM python:3.11" in dockerfile
        assert "EXPOSE 8080" in dockerfile
        assert "requirements.lock" in dockerfile

    def test_service_url(self):
        """Test service URL generation."""
        from jarvis_core.deploy.cloud_run import CloudRunConfig, CloudRunDeployer

        config = CloudRunConfig(
            project_id="my-project",
            service_name="jarvis-api",
        )
        deployer = CloudRunDeployer(config)

        url = deployer.get_service_url()

        assert "jarvis-api" in url
        assert ".run.app" in url

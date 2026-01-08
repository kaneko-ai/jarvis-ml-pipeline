"""Tests for Cloud Run Deployment and Slack Bot."""

import pytest

pytestmark = pytest.mark.core


class TestCloudRunDeployer:
    """Tests for Cloud Run Deployment (RP-520)."""

    def test_deployer_init(self):
        """Test CloudRunDeployer initialization."""
        from jarvis_core.deploy.cloud_run import CloudRunDeployer

        deployer = CloudRunDeployer()
        assert deployer is not None

    def test_deploy(self):
        """Test deploying to Cloud Run."""
        from jarvis_core.deploy.cloud_run import CloudRunConfig, CloudRunDeployer

        config = CloudRunConfig(
            project_id="test-project",
            service_name="jarvis-test",
            image="gcr.io/test/jarvis:v1",
        )
        deployer = CloudRunDeployer(config)

        status = deployer.deploy()

        assert status.service_name == "jarvis-test"
        assert status.status == "READY"

    def test_canary_deploy(self):
        """Test canary deployment."""
        from jarvis_core.deploy.cloud_run import CloudRunConfig, CloudRunDeployer

        config = CloudRunConfig(project_id="test-project")
        deployer = CloudRunDeployer(config)

        status = deployer.canary_deploy(
            image="gcr.io/test/jarvis:v2",
            canary_percent=10,
        )

        assert status.traffic[0]["percent"] == 10

    def test_promote_canary(self):
        """Test promoting canary."""
        from jarvis_core.deploy.cloud_run import CloudRunConfig, CloudRunDeployer

        config = CloudRunConfig(project_id="test-project")
        deployer = CloudRunDeployer(config)

        # First deploy
        status = deployer.deploy()
        revision = status.revision

        # Promote
        promoted = deployer.promote_canary(revision)

        assert promoted.traffic[0]["percent"] == 100

    def test_list_revisions(self):
        """Test listing revisions."""
        from jarvis_core.deploy.cloud_run import CloudRunConfig, CloudRunDeployer

        config = CloudRunConfig(project_id="test-project")
        deployer = CloudRunDeployer(config)

        deployer.deploy()

        revisions = deployer.list_revisions()
        assert len(revisions) >= 1

    def test_generate_deploy_command(self):
        """Test generating gcloud command."""
        from jarvis_core.deploy.cloud_run import CloudRegion, CloudRunConfig, CloudRunDeployer

        config = CloudRunConfig(
            project_id="my-project",
            region=CloudRegion.ASIA_NORTHEAST1,
            service_name="jarvis-api",
            image="gcr.io/my-project/jarvis:v1",
        )
        deployer = CloudRunDeployer(config)

        cmd = deployer.generate_deploy_command()

        assert "gcloud run deploy" in cmd
        assert "my-project" in cmd
        assert "asia-northeast1" in cmd

    def test_cloud_region_enum(self):
        """Test CloudRegion enum."""
        from jarvis_core.deploy.cloud_run import CloudRegion

        assert CloudRegion.ASIA_NORTHEAST1.value == "asia-northeast1"
        assert CloudRegion.US_CENTRAL1.value == "us-central1"


class TestSlackBot:
    """Tests for Slack Bot."""

    def test_bot_init(self):
        """Test bot initialization."""
        from jarvis_core.integrations.slack_bot import JarvisSlackBot

        bot = JarvisSlackBot()
        assert bot is not None

    def test_parse_search_command(self):
        """Test parsing search command."""
        from jarvis_core.integrations.slack_bot import CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = bot.parse_command("/jarvis search COVID-19", "user1", "channel1")

        assert cmd.command_type == CommandType.SEARCH
        assert "COVID-19" in cmd.args[0]

    def test_parse_status_command(self):
        """Test parsing status command."""
        from jarvis_core.integrations.slack_bot import CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = bot.parse_command("status", "user1", "channel1")

        assert cmd.command_type == CommandType.STATUS

    def test_parse_help_command(self):
        """Test parsing help command."""
        from jarvis_core.integrations.slack_bot import CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = bot.parse_command("", "user1", "channel1")

        assert cmd.command_type == CommandType.HELP

    def test_handle_search(self):
        """Test handling search command."""
        from jarvis_core.integrations.slack_bot import BotCommand, CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = BotCommand(
            command_type=CommandType.SEARCH,
            args=["machine learning"],
            user_id="user1",
            channel_id="channel1",
        )

        response = bot.handle_command(cmd)

        assert "machine learning" in response.text
        assert len(response.blocks) > 0

    def test_handle_status(self):
        """Test handling status command."""
        from jarvis_core.integrations.slack_bot import BotCommand, CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = BotCommand(
            command_type=CommandType.STATUS,
            args=[],
            user_id="user1",
            channel_id="channel1",
        )

        response = bot.handle_command(cmd)

        assert "Status" in response.text
        assert len(response.blocks) > 0

    def test_handle_help(self):
        """Test handling help command."""
        from jarvis_core.integrations.slack_bot import BotCommand, CommandType, JarvisSlackBot

        bot = JarvisSlackBot()
        cmd = BotCommand(
            command_type=CommandType.HELP,
            args=[],
            user_id="user1",
            channel_id="channel1",
        )

        response = bot.handle_command(cmd)

        assert "Commands" in response.blocks[1]["text"]["text"]

    def test_command_shortcuts(self):
        """Test command shortcuts."""
        from jarvis_core.integrations.slack_bot import CommandType, JarvisSlackBot

        bot = JarvisSlackBot()

        # Test shortcuts
        assert bot.parse_command("s test", "u", "c").command_type == CommandType.SEARCH
        assert bot.parse_command("st", "u", "c").command_type == CommandType.STATUS
        assert bot.parse_command("h", "u", "c").command_type == CommandType.HELP

    def test_global_bot(self):
        """Test global bot instance."""
        from jarvis_core.integrations.slack_bot import get_jarvis_bot

        bot1 = get_jarvis_bot()
        bot2 = get_jarvis_bot()

        assert bot1 is bot2

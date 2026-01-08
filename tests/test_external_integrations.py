"""Tests for external integrations - Phase 3."""

import pytest

from jarvis_core.integrations.external import (
    ArXivClient,
    GitHubIssueCreator,
    NotionConfig,
    NotionSync,
    ORCIDClient,
    SemanticScholarClient,
    SlackConfig,
    SlackNotifier,
    get_arxiv_client,
    get_semantic_scholar_client,
    get_slack_notifier,
)


class TestSlackIntegration:
    """Test Slack integration."""

    def test_slack_config(self):
        """Test Slack configuration."""
        config = SlackConfig(webhook_url="https://hooks.slack.com/test")
        assert config.webhook_url == "https://hooks.slack.com/test"
        assert config.channel == "#jarvis-alerts"
        assert config.username == "JARVIS Bot"

    def test_slack_notifier_init(self):
        """Test Slack notifier initialization."""
        config = SlackConfig(webhook_url="https://test.com")
        notifier = SlackNotifier(config)
        assert notifier.config == config

    def test_get_slack_notifier(self):
        """Test factory function."""
        notifier = get_slack_notifier("https://test.com", "#test")
        assert notifier.config.webhook_url == "https://test.com"
        assert notifier.config.channel == "#test"


class TestNotionIntegration:
    """Test Notion integration."""

    def test_notion_config(self):
        """Test Notion configuration."""
        config = NotionConfig(api_key="test_key", database_id="db_123")
        assert config.api_key == "test_key"
        assert config.database_id == "db_123"

    def test_notion_sync_init(self):
        """Test Notion sync initialization."""
        config = NotionConfig(api_key="key", database_id="db")
        sync = NotionSync(config)
        assert sync.config == config


class TestORCIDIntegration:
    """Test ORCID integration."""

    def test_orcid_client_init(self):
        """Test ORCID client initialization."""
        client = ORCIDClient()
        assert client.BASE_URL == "https://pub.orcid.org/v3.0"


class TestArXivIntegration:
    """Test arXiv integration."""

    def test_arxiv_client_init(self):
        """Test arXiv client initialization."""
        client = ArXivClient()
        assert "arxiv.org" in client.BASE_URL

    def test_arxiv_parse_response(self):
        """Test XML parsing (simplified)."""
        client = ArXivClient()
        xml = """
        <entry>
            <id>http://arxiv.org/abs/2401.12345</id>
            <title>Test Paper Title</title>
            <summary>This is a test abstract.</summary>
        </entry>
        """
        papers = client._parse_response(xml)
        assert len(papers) == 1
        assert papers[0]["title"] == "Test Paper Title"

    def test_get_arxiv_client(self):
        """Test factory function."""
        client = get_arxiv_client()
        assert isinstance(client, ArXivClient)


class TestSemanticScholarIntegration:
    """Test Semantic Scholar integration."""

    def test_ss_client_init(self):
        """Test Semantic Scholar client initialization."""
        client = SemanticScholarClient()
        assert client.api_key is None

        client_with_key = SemanticScholarClient(api_key="test_key")
        assert client_with_key.api_key == "test_key"

    def test_ss_base_url(self):
        """Test base URL."""
        client = SemanticScholarClient()
        assert "semanticscholar.org" in client.BASE_URL

    def test_get_ss_client(self):
        """Test factory function."""
        client = get_semantic_scholar_client("key123")
        assert client.api_key == "key123"


class TestGitHubIssueCreator:
    """Test GitHub issue creator."""

    def test_github_creator_init(self):
        """Test GitHub issue creator initialization."""
        creator = GitHubIssueCreator(token="ghp_test", owner="kaneko-ai", repo="jarvis-ml-pipeline")
        assert creator.token == "ghp_test"
        assert creator.owner == "kaneko-ai"
        assert creator.repo == "jarvis-ml-pipeline"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

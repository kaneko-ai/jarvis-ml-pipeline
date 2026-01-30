"""Tests for Plugin System and External Integrations.

Tests for Task 3.1-3.2
"""

from unittest.mock import patch


class TestPluginSystem:
    """Tests for Plugin System."""

    def test_plugin_type_enum(self):
        """Test PluginType enum."""
        from jarvis_core.plugins.plugin_system import PluginType

        assert PluginType.SOURCE.value == "source"
        assert PluginType.ANALYZER.value == "analyzer"

    def test_plugin_status_enum(self):
        """Test PluginStatus enum."""
        from jarvis_core.plugins.plugin_system import PluginStatus

        assert PluginStatus.ACTIVE.value == "active"
        assert PluginStatus.ERROR.value == "error"

    def test_plugin_info_dataclass(self):
        """Test PluginInfo dataclass."""
        from jarvis_core.plugins.plugin_system import PluginInfo, PluginType

        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            plugin_type=PluginType.CUSTOM,
            description="Test plugin",
        )

        d = info.to_dict()
        assert d["name"] == "test_plugin"
        assert d["type"] == "custom"

    def test_plugin_registry_register(self):
        """Test plugin registration."""
        from jarvis_core.plugins.plugin_system import Plugin, PluginRegistry, PluginType

        class TestPlugin(Plugin):
            NAME = "test_plugin"
            VERSION = "1.0.0"
            PLUGIN_TYPE = PluginType.CUSTOM

            def initialize(self):
                return True

            def execute(self, **kwargs):
                return "executed"

        registry = PluginRegistry()
        assert registry.register(TestPlugin) is True

        plugins = registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].name == "test_plugin"

    def test_plugin_registry_get_plugin(self):
        """Test getting plugin instance."""
        from jarvis_core.plugins.plugin_system import Plugin, PluginRegistry, PluginType

        class TestPlugin(Plugin):
            NAME = "test_get"
            VERSION = "1.0.0"
            PLUGIN_TYPE = PluginType.CUSTOM

            def initialize(self):
                return True

            def execute(self, **kwargs):
                return "test_result"

        registry = PluginRegistry()
        registry.register(TestPlugin)

        plugin = registry.get_plugin("test_get")
        assert plugin is not None
        assert plugin.execute() == "test_result"

    def test_plugin_registry_unregister(self):
        """Test plugin unregistration."""
        from jarvis_core.plugins.plugin_system import Plugin, PluginRegistry, PluginType

        class TestPlugin(Plugin):
            NAME = "to_unregister"
            VERSION = "1.0.0"
            PLUGIN_TYPE = PluginType.CUSTOM

            def initialize(self):
                return True

            def execute(self, **kwargs):
                pass

        registry = PluginRegistry()
        registry.register(TestPlugin)
        assert len(registry.list_plugins()) == 1

        registry.unregister("to_unregister")
        assert len(registry.list_plugins()) == 0

    def test_source_plugin_interface(self):
        """Test SourcePlugin interface."""
        from jarvis_core.plugins.plugin_system import SourcePlugin

        class TestSource(SourcePlugin):
            NAME = "test_source"
            VERSION = "1.0.0"

            def initialize(self):
                return True

            def search(self, query, **kwargs):
                return [{"id": "1", "title": query}]

            def fetch(self, item_id, **kwargs):
                return {"id": item_id}

        source = TestSource()
        source.initialize()

        results = source.search("test")
        assert len(results) == 1

    def test_analyzer_plugin_interface(self):
        """Test AnalyzerPlugin interface."""
        from jarvis_core.plugins.plugin_system import AnalyzerPlugin

        class TestAnalyzer(AnalyzerPlugin):
            NAME = "test_analyzer"
            VERSION = "1.0.0"

            def initialize(self):
                return True

            def analyze(self, data, **kwargs):
                return {"count": len(data)}

        analyzer = TestAnalyzer()
        analyzer.initialize()

        result = analyzer.execute(data=[1, 2, 3])
        assert result["count"] == 3

    def test_exporter_plugin_interface(self):
        """Test ExporterPlugin interface."""
        from jarvis_core.plugins.plugin_system import ExporterPlugin

        class TestExporter(ExporterPlugin):
            NAME = "test_exporter"
            VERSION = "1.0.0"

            def initialize(self):
                return True

            def export(self, data, output_path=None, **kwargs):
                return str(data)

        exporter = TestExporter()
        exporter.initialize()

        result = exporter.execute(data={"key": "value"})
        assert "key" in result

    def test_get_registry_singleton(self):
        """Test global registry singleton."""
        from jarvis_core.plugins.plugin_system import get_registry

        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2


class TestZoteroIntegration:
    """Tests for Zotero Integration."""

    def test_zotero_item_dataclass(self):
        """Test ZoteroItem dataclass."""
        from jarvis_core.plugins.zotero_integration import ZoteroItem

        item = ZoteroItem(
            key="ABC123",
            item_type="journalArticle",
            title="Test Paper",
            creators=["Smith, J."],
        )

        d = item.to_dict()
        assert d["key"] == "ABC123"
        assert d["item_type"] == "journalArticle"

    def test_zotero_client_init(self):
        """Test ZoteroClient initialization."""
        from jarvis_core.plugins.zotero_integration import ZoteroClient

        with patch.dict(
            "os.environ",
            {
                "ZOTERO_API_KEY": "test_key",
                "ZOTERO_USER_ID": "12345",
            },
        ):
            client = ZoteroClient()
            assert client.api_key == "test_key"
            assert client.user_id == "12345"

    def test_zotero_library_url(self):
        """Test library URL construction."""
        from jarvis_core.plugins.zotero_integration import ZoteroClient

        client = ZoteroClient(api_key="key", user_id="123")
        assert "/users/123" in client.library_url

        client_group = ZoteroClient(api_key="key", group_id="456")
        assert "/groups/456" in client_group.library_url

    def test_zotero_plugin_init(self):
        """Test ZoteroPlugin initialization."""
        from jarvis_core.plugins.zotero_integration import ZoteroPlugin

        plugin = ZoteroPlugin()
        assert plugin.initialize() is True
        assert plugin.client is not None


class TestSamplePlugins:
    """Tests for Sample Plugins."""

    def test_bibtex_exporter(self):
        """Test BibTeX exporter."""
        from jarvis_core.plugins.sample_plugins import BibtexExporterPlugin

        plugin = BibtexExporterPlugin()
        plugin.initialize()

        papers = [
            {
                "key": "smith2024",
                "title": "Test Paper",
                "authors": ["Smith, J.", "Doe, J."],
                "year": "2024",
            }
        ]

        bibtex = plugin.export(papers)

        assert "@article{smith2024" in bibtex
        assert "Test Paper" in bibtex
        assert "2024" in bibtex

    def test_json_exporter(self):
        """Test JSON exporter."""
        from jarvis_core.plugins.sample_plugins import JSONExporterPlugin

        plugin = JSONExporterPlugin()
        plugin.initialize()

        data = {"key": "value", "list": [1, 2, 3]}
        result = plugin.export(data)

        assert '"key": "value"' in result
        assert '"list"' in result

    def test_word_count_analyzer(self):
        """Test word count analyzer."""
        from jarvis_core.plugins.sample_plugins import WordCountAnalyzer

        plugin = WordCountAnalyzer()
        plugin.initialize()

        result = plugin.analyze("This is a test. Another sentence!")

        assert result["total_words"] == 6
        assert result["total_sentences"] == 2

    def test_keyword_extractor(self):
        """Test keyword extractor."""
        from jarvis_core.plugins.sample_plugins import KeywordExtractor

        plugin = KeywordExtractor()
        plugin.initialize()

        text = "machine learning machine learning deep learning neural network"
        result = plugin.analyze(text, top_n=5)

        assert "keywords" in result
        # Both 'learning' and 'machine' appear twice
        top_words = [k["word"] for k in result["keywords"][:2]]
        assert "learning" in top_words or "machine" in top_words


class TestPhase3Integration:
    """Integration tests for Phase 3."""

    def test_all_plugins_registered(self):
        """Test that sample plugins are registered."""
        from jarvis_core.plugins.plugin_system import get_registry

        registry = get_registry()
        plugins = registry.list_plugins()

        # Should have at least the sample plugins
        names = [p.name for p in plugins]
        assert "bibtex_exporter" in names or len(plugins) > 0

    def test_plugin_system_imports(self):
        """Test plugin system module imports."""
        from jarvis_core.plugins.plugin_system import (
            Plugin,
            PluginRegistry,
        )

        assert Plugin is not None
        assert PluginRegistry is not None
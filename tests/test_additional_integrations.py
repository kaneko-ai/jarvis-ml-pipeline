"""Tests for additional integrations module."""

from jarvis_core.integrations.additional import (
    Annotation,
    AnnotationManager,
    DashboardManager,
    DiscordConfig,
    FullScreenManager,
    GoogleDriveConfig,
    GoogleDriveExporter,
    ObsidianExporter,
    SplitViewManager,
    ThreeDAnimationConfig,
    Widget,
    ZoteroConfig,
    get_annotation_manager,
    get_dashboard_manager,
    get_obsidian_exporter,
)
import pytest


class TestZoteroClient:
    """Test Zotero integration."""

    def test_config(self):
        config = ZoteroConfig(api_key="test", user_id="123")
        assert config.api_key == "test"
        assert config.library_type == "user"


class TestGoogleDriveExporter:
    """Test Google Drive integration."""

    def test_config(self):
        config = GoogleDriveConfig(access_token="token123")
        assert config.access_token == "token123"

    def test_export_papers(self):
        config = GoogleDriveConfig(access_token="token")
        exporter = GoogleDriveExporter(config)
        result = exporter.export_papers([{"title": "Test"}])
        assert result is not None


class TestDiscordBot:
    """Test Discord integration."""

    def test_config(self):
        config = DiscordConfig(bot_token="token", channel_id="123")
        assert config.bot_token == "token"


class TestObsidianExporter:
    """Test Obsidian export."""

    def test_paper_to_markdown(self):
        exporter = ObsidianExporter()
        paper = {
            "title": "Test Paper",
            "authors": "Smith J",
            "year": 2024,
            "journal": "Nature",
            "abstract": "Test abstract",
        }
        md = exporter.paper_to_markdown(paper)
        assert "# Test Paper" in md
        assert "Smith J" in md
        assert "2024" in md
        assert "Nature" in md

    def test_export_paper_filename(self):
        exporter = ObsidianExporter()
        paper = {"title": "Test Paper Title"}
        filename = exporter.export_paper(paper)
        assert filename.endswith(".md")


class TestDashboardManager:
    """Test dashboard manager."""

    def test_add_widget(self):
        dm = DashboardManager()
        widget = Widget("w1", "stats", "Stats", {"x": 0, "y": 0, "w": 2, "h": 2}, {})
        dm.add_widget(widget)
        assert len(dm.widgets) == 1

    def test_remove_widget(self):
        dm = DashboardManager()
        widget = Widget("w1", "stats", "Stats", {}, {})
        dm.add_widget(widget)
        dm.remove_widget("w1")
        assert len(dm.widgets) == 0

    def test_get_default_layout(self):
        dm = DashboardManager()
        layout = dm.get_default_layout()
        assert len(layout) > 0

    def test_save_load_layout(self):
        dm = DashboardManager()
        widget = Widget("w1", "stats", "Stats", {}, {})
        dm.add_widget(widget)
        dm.save_layout("test")
        dm.widgets = []
        dm.load_layout("test")
        assert len(dm.widgets) == 1


class TestSplitViewManager:
    """Test split view manager."""

    def test_set_layout_vertical(self):
        svm = SplitViewManager()
        svm.set_layout("vertical")
        assert "left" in svm.panes
        assert "right" in svm.panes

    def test_set_layout_horizontal(self):
        svm = SplitViewManager()
        svm.set_layout("horizontal")
        assert "top" in svm.panes
        assert "bottom" in svm.panes

    def test_set_layout_quad(self):
        svm = SplitViewManager()
        svm.set_layout("quad")
        assert len(svm.panes) == 4


class TestFullScreenManager:
    """Test fullscreen manager."""

    def test_toggle(self):
        fsm = FullScreenManager()
        result = fsm.toggle()
        assert result["is_fullscreen"] is True
        result = fsm.toggle()
        assert result["is_fullscreen"] is False


class TestAnnotationManager:
    """Test annotation manager."""

    def test_add_annotation(self):
        am = AnnotationManager()
        ann = Annotation(
            id="",
            paper_id="paper1",
            text="Important finding",
            highlight_color="yellow",
            page=1,
            position={"x": 0, "y": 0},
        )
        ann_id = am.add_annotation("paper1", ann)
        assert ann_id.startswith("ann_")

    def test_get_annotations(self):
        am = AnnotationManager()
        ann = Annotation("", "p1", "text", "yellow", 1, {})
        am.add_annotation("p1", ann)
        anns = am.get_annotations("p1")
        assert len(anns) == 1

    def test_delete_annotation(self):
        am = AnnotationManager()
        ann = Annotation("", "p1", "text", "yellow", 1, {})
        am.add_annotation("p1", ann)
        am.delete_annotation("p1", "ann_0")
        assert len(am.get_annotations("p1")) == 0

    def test_export_annotations(self):
        am = AnnotationManager()
        ann = Annotation("", "p1", "text", "yellow", 1, {})
        am.add_annotation("p1", ann)
        export = am.export_annotations("p1")
        assert "annotations" in export


class TestThreeDAnimationConfig:
    """Test 3D animation config."""

    def test_generate_config(self):
        config = ThreeDAnimationConfig()
        result = config.generate_config()
        assert "particles" in result
        assert "waves" in result


class TestFactoryFunctions:
    """Test factory functions."""

    def test_get_obsidian_exporter(self):
        assert isinstance(get_obsidian_exporter(), ObsidianExporter)

    def test_get_dashboard_manager(self):
        assert isinstance(get_dashboard_manager(), DashboardManager)

    def test_get_annotation_manager(self):
        assert isinstance(get_annotation_manager(), AnnotationManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

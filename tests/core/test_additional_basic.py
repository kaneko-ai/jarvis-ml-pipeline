from unittest.mock import MagicMock, patch
from jarvis_core.integrations.additional import (
    ZoteroClient,
    ZoteroConfig,
    GoogleDriveExporter,
    GoogleDriveConfig,
    DiscordBot,
    DiscordConfig,
    ObsidianExporter,
    DashboardManager,
    Widget,
    AnnotationManager,
    Annotation,
    SplitViewManager,
    FullScreenManager,
    ThreeDAnimationConfig,
)


class TestZoteroClient:
    @patch("urllib.request.urlopen")
    def test_get_items(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'[{"key": "abc"}]'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = ZoteroClient(ZoteroConfig(api_key="key", user_id="id"))
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["key"] == "abc"

    @patch("urllib.request.urlopen")
    def test_add_item(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = ZoteroClient(ZoteroConfig(api_key="key", user_id="id"))
        res = client.add_item({"title": "Test Paper", "authors": "Author A"})
        assert res is True


class TestGoogleDriveExporter:
    def test_export_papers(self):
        config = GoogleDriveConfig(access_token="tok")
        exporter = GoogleDriveExporter(config)
        res = exporter.export_papers([{"title": "P1"}])
        assert res == "file_jarvis_papers.json"


class TestDiscordBot:
    @patch("urllib.request.urlopen")
    def test_send_message(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        bot = DiscordBot(DiscordConfig(bot_token="tok", channel_id="ch"))
        res = bot.send_message("Hello")
        assert res is True


class TestObsidianExporter:
    def test_paper_to_markdown(self):
        exp = ObsidianExporter()
        paper = {"title": "Title", "authors": "A, B", "year": 2024, "pmid": "123"}
        md = exp.paper_to_markdown(paper)
        assert "# Title" in md
        assert 'pmid: "123"' in md


class TestDashboardManager:
    def test_widgets(self):
        dm = DashboardManager()
        w = Widget(id="w1", type="stats", title="T", position={}, config={})
        dm.add_widget(w)
        assert len(dm.widgets) == 1
        dm.update_position("w1", {"x": 1})
        assert dm.widgets[0].position["x"] == 1
        dm.remove_widget("w1")
        assert len(dm.widgets) == 0


class TestAnnotationManager:
    def test_annotation(self):
        am = AnnotationManager()
        ann = Annotation(
            id="", paper_id="P1", text="text", highlight_color="yellow", page=1, position={}
        )
        ann_id = am.add_annotation("P1", ann)
        assert ann_id.startswith("ann_")
        assert len(am.get_annotations("P1")) == 1

        am.delete_annotation("P1", ann_id)
        assert len(am.get_annotations("P1")) == 0


def test_split_view_manager():
    sm = SplitViewManager()
    sm.set_layout("vertical")
    assert "left" in sm.panes
    assert "right" in sm.panes
    css = sm.generate_css()
    assert "flex" in css


def test_fullscreen_manager():
    fm = FullScreenManager()
    info = fm.toggle("elem1")
    assert info["is_fullscreen"] is True
    assert fm.generate_js() != ""


def test_3d_animation_config():
    cfg = ThreeDAnimationConfig()
    res = cfg.generate_config()
    assert res["enabled"] is True
    assert cfg.generate_js_snippet() != ""
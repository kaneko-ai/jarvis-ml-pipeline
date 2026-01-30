"""Comprehensive tests for mobile/performance module."""

from jarvis_core.performance.mobile import (
    BackgroundWorkerManager,
    BottomNavigation,
    GestureHandler,
    LocalCache,
    PullToRefresh,
    PWAHelper,
    ShareManager,
    VirtualScroller,
    get_gesture_handler,
    get_local_cache,
    get_pwa_helper,
    get_share_manager,
    get_virtual_scroller,
)
import pytest


class TestVirtualScroller:
    """Test virtual scrolling."""

    def test_get_visible_items(self):
        items = list(range(100))
        vs = VirtualScroller(items)
        visible = vs.get_visible_items(250, 200, 50)
        assert visible["start_index"] == 0
        assert visible["total_items"] == 100

    def test_get_page(self):
        items = list(range(100))
        vs = VirtualScroller(items, page_size=20)
        page = vs.get_page(0)
        assert len(page) == 20
        assert page[0] == 0


class TestBackgroundWorkerManager:
    """Test background worker."""

    def test_create_task(self):
        wm = BackgroundWorkerManager()
        task_id = wm.create_task("search", {"query": "test"})
        assert len(task_id) == 8

    def test_get_task_status(self):
        wm = BackgroundWorkerManager()
        task_id = wm.create_task("analyze", {})
        status = wm.get_task_status(task_id)
        assert status["status"] == "pending"

    def test_complete_task(self):
        wm = BackgroundWorkerManager()
        task_id = wm.create_task("export", {})
        wm.complete_task(task_id, {"success": True})
        status = wm.get_task_status(task_id)
        assert status["status"] == "complete"
        assert status["progress"] == 100


class TestLocalCache:
    """Test local cache."""

    def test_set_and_get(self):
        cache = LocalCache()
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result["data"] == "value"

    def test_get_missing_key(self):
        cache = LocalCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_clear(self):
        cache = LocalCache()
        cache.set("key", {"x": 1})
        cache.clear()
        assert cache.get("key") is None

    def test_stats(self):
        cache = LocalCache(max_size=100)
        cache.set("k1", {})
        cache.set("k2", {})
        stats = cache.stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 100


class TestGestureHandler:
    """Test gesture detection."""

    def test_detect_swipe_left(self):
        gh = GestureHandler()
        gesture = gh.detect_gesture(100, 100, 0, 100, 300)
        assert gesture == "swipe_left"

    def test_detect_swipe_right(self):
        gh = GestureHandler()
        gesture = gh.detect_gesture(0, 100, 100, 100, 300)
        assert gesture == "swipe_right"

    def test_detect_swipe_down(self):
        gh = GestureHandler()
        gesture = gh.detect_gesture(100, 0, 100, 100, 300)
        assert gesture == "swipe_down"

    def test_get_action(self):
        gh = GestureHandler()
        action = gh.get_action("swipe_left")
        assert action == "next_page"


class TestPullToRefresh:
    """Test pull to refresh."""

    def test_on_pull_not_enough(self):
        ptr = PullToRefresh(threshold=80)
        result = ptr.on_pull(40)
        assert result["progress"] == 50
        assert result["should_refresh"] is False

    def test_on_pull_enough(self):
        ptr = PullToRefresh(threshold=80)
        result = ptr.on_pull(100)
        assert result["should_refresh"] is True

    def test_trigger_refresh(self):
        ptr = PullToRefresh()
        result = ptr.trigger_refresh()
        assert result is True


class TestBottomNavigation:
    """Test bottom navigation."""

    def test_add_item(self):
        nav = BottomNavigation()
        nav.add_item("home", "Home", "🏠", "/")
        nav.add_item("search", "Search", "🔍", "/search")
        assert len(nav.items) == 2

    def test_generate_html(self):
        nav = BottomNavigation()
        nav.add_item("home", "Home", "🏠", "/")
        html = nav.generate_html()
        assert "nav" in html
        assert "Home" in html


class TestPWAHelper:
    """Test PWA helper."""

    def test_generate_manifest(self):
        config = {"name": "Test App", "short_name": "Test"}
        manifest = PWAHelper.generate_manifest(config)
        assert manifest["name"] == "Test App"
        assert "icons" in manifest

    def test_check_installability(self):
        result = PWAHelper.check_installability()
        assert result["installable"] is True


class TestShareManager:
    """Test share manager."""

    def test_share_data(self):
        data = ShareManager.share_data("Title", "Text", "https://example.com")
        assert data["title"] == "Title"
        assert data["url"] == "https://example.com"

    def test_share_paper(self):
        paper = {"title": "Test Paper", "authors": "Smith J", "pmid": "12345"}
        data = ShareManager.share_paper(paper)
        assert "Test Paper" in data["title"]
        assert "12345" in data["url"]


class TestFactoryFunctions:
    """Test factory functions."""

    def test_get_virtual_scroller(self):
        vs = get_virtual_scroller([1, 2, 3])
        assert isinstance(vs, VirtualScroller)

    def test_get_local_cache(self):
        assert isinstance(get_local_cache(), LocalCache)

    def test_get_pwa_helper(self):
        assert isinstance(get_pwa_helper(), PWAHelper)

    def test_get_gesture_handler(self):
        assert isinstance(get_gesture_handler(), GestureHandler)

    def test_get_share_manager(self):
        assert isinstance(get_share_manager(), ShareManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for Degradation Management Module.

Extended tests per JARVIS coverage improvement plan.
"""

import pytest
from unittest.mock import Mock, patch


class TestDegradationLevel:
    """Tests for DegradationLevel enum."""

    def test_full_value(self):
        """Test FULL level value."""
        from jarvis_core.network.degradation import DegradationLevel

        assert DegradationLevel.FULL.value == "full"

    def test_limited_value(self):
        """Test LIMITED level value."""
        from jarvis_core.network.degradation import DegradationLevel

        assert DegradationLevel.LIMITED.value == "limited"

    def test_offline_value(self):
        """Test OFFLINE level value."""
        from jarvis_core.network.degradation import DegradationLevel

        assert DegradationLevel.OFFLINE.value == "offline"

    def test_critical_value(self):
        """Test CRITICAL level value."""
        from jarvis_core.network.degradation import DegradationLevel

        assert DegradationLevel.CRITICAL.value == "critical"

    def test_all_levels_exist(self):
        """Test all expected levels exist."""
        from jarvis_core.network.degradation import DegradationLevel

        levels = [level.value for level in DegradationLevel]
        assert "full" in levels
        assert "limited" in levels
        assert "offline" in levels
        assert "critical" in levels


class TestDegradationManager:
    """Tests for DegradationManager class."""

    def test_initialization(self):
        """Test default initialization."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        manager = DegradationManager()

        assert manager._current_level == DegradationLevel.FULL
        assert manager._listeners == []

    def test_get_level(self):
        """Test get_level method."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        manager = DegradationManager()

        assert manager.get_level() == DegradationLevel.FULL

    def test_set_level(self):
        """Test set_level method."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        manager = DegradationManager()
        manager.set_level(DegradationLevel.OFFLINE)

        assert manager.get_level() == DegradationLevel.OFFLINE

    def test_set_level_notifies_listeners(self):
        """Test set_level notifies listeners."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        manager = DegradationManager()
        callback = Mock()
        manager.add_listener(callback)

        manager.set_level(DegradationLevel.LIMITED)

        callback.assert_called_once_with(DegradationLevel.FULL, DegradationLevel.LIMITED)

    def test_set_level_same_no_notify(self):
        """Test set_level with same level doesn't notify."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        manager = DegradationManager()
        callback = Mock()
        manager.add_listener(callback)

        manager.set_level(DegradationLevel.FULL)  # Same as default

        callback.assert_not_called()

    def test_add_listener(self):
        """Test add_listener method."""
        from jarvis_core.network.degradation import DegradationManager

        manager = DegradationManager()
        callback = Mock()

        manager.add_listener(callback)

        assert callback in manager._listeners

    def test_multiple_listeners(self):
        """Test multiple listeners are notified."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        manager = DegradationManager()
        callback1 = Mock()
        callback2 = Mock()
        manager.add_listener(callback1)
        manager.add_listener(callback2)

        manager.set_level(DegradationLevel.OFFLINE)

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_listener_exception_handled(self):
        """Test listener exception doesn't stop other listeners."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        manager = DegradationManager()
        bad_callback = Mock(side_effect=Exception("Error"))
        good_callback = Mock()
        manager.add_listener(bad_callback)
        manager.add_listener(good_callback)

        # Should not raise
        manager.set_level(DegradationLevel.LIMITED)

        good_callback.assert_called_once()

    def test_get_instance_singleton(self):
        """Test get_instance returns singleton."""
        from jarvis_core.network.degradation import DegradationManager

        DegradationManager._instance = None  # Reset

        instance1 = DegradationManager.get_instance()
        instance2 = DegradationManager.get_instance()

        assert instance1 is instance2

    @patch("jarvis_core.network.detector.is_online")
    def test_auto_detect_level_online(self, mock_is_online):
        """Test auto_detect_level when online."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        mock_is_online.return_value = True

        manager = DegradationManager()
        level = manager.auto_detect_level()

        assert level == DegradationLevel.FULL

    @patch("jarvis_core.network.detector.is_online")
    def test_auto_detect_level_offline(self, mock_is_online):
        """Test auto_detect_level when offline."""
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel

        mock_is_online.return_value = False

        manager = DegradationManager()
        level = manager.auto_detect_level()

        assert level == DegradationLevel.OFFLINE


class TestGetDegradationManager:
    """Tests for get_degradation_manager function."""

    def test_returns_singleton(self):
        """Test returns singleton instance."""
        from jarvis_core.network.degradation import (
            get_degradation_manager,
            DegradationManager,
        )

        DegradationManager._instance = None  # Reset

        manager1 = get_degradation_manager()
        manager2 = get_degradation_manager()

        assert manager1 is manager2


class TestModuleImports:
    """Test module imports."""

    def test_imports(self):
        """Test all exports are importable."""
        from jarvis_core.network.degradation import (
            DegradationLevel,
            DegradationManager,
            get_degradation_manager,
        )

        assert DegradationLevel is not None
        assert DegradationManager is not None
        assert get_degradation_manager is not None

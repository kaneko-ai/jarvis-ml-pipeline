"""Tests for sync.handlers module."""

from unittest.mock import MagicMock

from jarvis_core.sync.handlers import register_default_handlers


class TestRegisterDefaultHandlers:
    def test_register_search_handler(self):
        mock_manager = MagicMock()

        register_default_handlers(mock_manager)

        # Should have called register_handler with "search"
        mock_manager.register_handler.assert_called()
        call_args = mock_manager.register_handler.call_args_list

        # Check that "search" was registered
        handler_names = [call[0][0] for call in call_args]
        assert "search" in handler_names

    def test_search_handler_registered(self):
        mock_manager = MagicMock()

        register_default_handlers(mock_manager)

        # Get the registered search handler
        call_args = mock_manager.register_handler.call_args_list
        search_call = next(c for c in call_args if c[0][0] == "search")
        handler = search_call[0][1]

        # Handler should be a callable
        assert callable(handler)
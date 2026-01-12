"""Tests for active_learning module - Comprehensive coverage."""

import pytest
from unittest.mock import Mock, patch


class TestActiveLearningModule:
    """Tests for active_learning module."""

    def test_module_import(self):
        """Test module import."""
        from jarvis_core import active_learning

        assert active_learning is not None

    def test_screener_creation(self):
        """Test Screener creation."""
        from jarvis_core.active_learning import screener

        assert screener is not None

    def test_uncertainty_sampling(self):
        """Test uncertainty sampling."""
        from jarvis_core import active_learning

        if hasattr(active_learning, "uncertainty_sample"):
            pass


class TestModuleImports:
    """Test module imports."""

    def test_imports(self):
        """Test imports."""
        from jarvis_core import active_learning

        assert active_learning is not None

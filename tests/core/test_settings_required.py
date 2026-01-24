import pytest
import os
from unittest.mock import patch
from jarvis_core.settings import CoreSettings, MissingSettingError


def test_settings_validation_prod_missing_key():
    """Test that production environment fails if mandatory key is missing."""
    with patch.dict(os.environ, {"JARVIS_ENV": "production", "NCBI_API_KEY": ""}):
        settings = CoreSettings()
        with pytest.raises(MissingSettingError) as excinfo:
            settings.validate()
        assert "NCBI_API_KEY is required" in str(excinfo.value)


def test_settings_validation_dev_missing_key():
    """Test that development environment does not necessarily fail if key is missing."""
    with patch.dict(os.environ, {"JARVIS_ENV": "development", "NCBI_API_KEY": ""}):
        settings = CoreSettings()
        # Should not raise
        settings.validate()


def test_settings_validation_prod_with_key():
    """Test that production passes with key."""
    with patch.dict(os.environ, {"JARVIS_ENV": "production", "NCBI_API_KEY": "dummy-key"}):
        settings = CoreSettings()
        settings.validate()

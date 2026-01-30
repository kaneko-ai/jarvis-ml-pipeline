"""Tests for contradiction/normalizer.py (FIXED v2)."""


class TestNormalizerInit:
    """Tests for normalizer initialization."""

    def test_creation_default(self):
        """Test default creation."""
        from jarvis_core.contradiction.normalizer import ClaimNormalizer

        normalizer = ClaimNormalizer()
        assert normalizer is not None


class TestModuleImports:
    """Test module imports."""

    def test_imports(self):
        """Test imports."""
        from jarvis_core.contradiction import normalizer

        assert normalizer is not None

    def test_class_import(self):
        """Test class import."""
        from jarvis_core.contradiction.normalizer import ClaimNormalizer

        assert ClaimNormalizer is not None
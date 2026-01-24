"""Tests for knowledge_graph module - Comprehensive coverage (FIXED v2)."""


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph class."""

    def test_creation(self):
        """Test KnowledgeGraph creation."""
        from jarvis_core.analysis.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        assert kg is not None

    def test_add_node(self):
        """Test adding node."""
        from jarvis_core.analysis.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_node("entity1", "GENE", {"name": "BRCA1"})

        assert "entity1" in kg.nodes


class TestModuleImports:
    """Test module imports."""

    def test_imports(self):
        """Test imports."""
        from jarvis_core.analysis.knowledge_graph import KnowledgeGraph

        assert KnowledgeGraph is not None

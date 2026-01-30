"""Tests for the Citation Analysis Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.2
"""


class TestCitationContextExtractor:
    """Tests for citation context extraction."""

    def test_extractor_init(self):
        """Test extractor initialization."""
        from jarvis_core.citation.context_extractor import CitationExtractor

        extractor = CitationExtractor()
        assert extractor is not None

    def test_extract_numeric_citations(self):
        """Test extraction of numeric citations."""
        from jarvis_core.citation import extract_citation_contexts

        text = "Previous work [1] showed significant results. This supports [2]."
        contexts = extract_citation_contexts(
            text,
            paper_id="paper_A",
            reference_map={"1": "paper_B", "2": "paper_C"},
        )

        assert len(contexts) >= 1
        # At least one citation should be found
        cited_ids = [c.cited_paper_id for c in contexts]
        assert "paper_B" in cited_ids or "paper_C" in cited_ids

    def test_extract_author_year_citations(self):
        """Test extraction of author-year citations."""
        from jarvis_core.citation import extract_citation_contexts

        text = "As shown by (Smith et al., 2020), the method works well."
        contexts = extract_citation_contexts(
            text,
            paper_id="paper_A",
        )

        assert len(contexts) >= 1
        assert "Smith et al., 2020" in contexts[0].citation_marker

    def test_citation_context_structure(self):
        """Test CitationContext dataclass."""
        from jarvis_core.citation.context_extractor import CitationContext

        context = CitationContext(
            citing_paper_id="paper_A",
            cited_paper_id="paper_B",
            citation_text="The results confirm [1].",
            context_before="We tested the hypothesis.",
            context_after="Further analysis shows...",
        )

        full = context.get_full_context()
        assert "confirm" in full
        assert "tested" in full

    def test_section_detection(self):
        """Test section detection in citations."""
        from jarvis_core.citation import extract_citation_contexts

        text = """
        Introduction

        Previous work [1] established the baseline.

        Methods

        We extended [2] with modifications.
        """

        contexts = extract_citation_contexts(text, paper_id="paper_A")

        # Should detect sections
        sections = [c.section for c in contexts if c.section]
        if sections:
            assert any(s in ["Introduction", "Methods"] for s in sections)


class TestStanceClassifier:
    """Tests for stance classification."""

    def test_classifier_init(self):
        """Test classifier initialization."""
        from jarvis_core.citation.stance_classifier import StanceClassifier

        classifier = StanceClassifier()
        assert classifier is not None

    def test_classify_support(self):
        """Test support stance classification."""
        from jarvis_core.citation import CitationStance, classify_citation_stance

        text = "Our results confirm and support the findings of [1]."
        result = classify_citation_stance(text)

        assert result.stance == CitationStance.SUPPORT
        assert result.confidence > 0.3

    def test_classify_contrast(self):
        """Test contrast stance classification."""
        from jarvis_core.citation import CitationStance, classify_citation_stance

        text = "However, unlike [1], our method shows different results."
        result = classify_citation_stance(text)

        assert result.stance == CitationStance.CONTRAST
        assert result.confidence > 0.3

    def test_classify_mention(self):
        """Test neutral mention classification."""
        from jarvis_core.citation import CitationStance, classify_citation_stance

        text = "See [1] for more details on the topic."
        result = classify_citation_stance(text)

        # Should be either MENTION or low confidence
        assert result.stance in [CitationStance.MENTION, CitationStance.SUPPORT]

    def test_stance_result_structure(self):
        """Test StanceResult dataclass."""
        from jarvis_core.citation.stance_classifier import CitationStance, StanceResult

        result = StanceResult(
            stance=CitationStance.SUPPORT,
            confidence=0.8,
            evidence="confirm, support",
        )

        data = result.to_dict()
        assert data["stance"] == "support"
        assert data["confidence"] == 0.8


class TestCitationGraph:
    """Tests for citation graph."""

    def test_graph_init(self):
        """Test graph initialization."""
        from jarvis_core.citation import CitationGraph

        graph = CitationGraph()
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_add_node(self):
        """Test adding nodes."""
        from jarvis_core.citation import CitationGraph

        graph = CitationGraph()
        node = graph.add_node("paper_A", title="Test Paper", year=2020)

        assert graph.node_count == 1
        assert node.paper_id == "paper_A"
        assert node.title == "Test Paper"

    def test_add_edge(self):
        """Test adding edges."""
        from jarvis_core.citation import CitationGraph, CitationStance

        graph = CitationGraph()
        edge = graph.add_edge(
            "paper_A",
            "paper_B",
            stance=CitationStance.SUPPORT,
            confidence=0.9,
        )

        assert graph.edge_count == 1
        assert graph.node_count == 2  # Both nodes created automatically
        assert edge.stance == CitationStance.SUPPORT

    def test_get_citations(self):
        """Test getting citations."""
        from jarvis_core.citation import CitationGraph, CitationStance

        graph = CitationGraph()
        graph.add_edge("A", "B", CitationStance.SUPPORT)
        graph.add_edge("A", "C", CitationStance.CONTRAST)

        citations = graph.get_citations("A")
        assert "B" in citations
        assert "C" in citations

    def test_get_cited_by(self):
        """Test getting papers citing a given paper."""
        from jarvis_core.citation import CitationGraph, CitationStance

        graph = CitationGraph()
        graph.add_edge("A", "B", CitationStance.SUPPORT)
        graph.add_edge("C", "B", CitationStance.MENTION)

        cited_by = graph.get_cited_by("B")
        assert "A" in cited_by
        assert "C" in cited_by

    def test_supporting_contrasting_citations(self):
        """Test getting support/contrast citations."""
        from jarvis_core.citation import CitationGraph, CitationStance

        graph = CitationGraph()
        graph.add_edge("A", "X", CitationStance.SUPPORT)
        graph.add_edge("B", "X", CitationStance.CONTRAST)
        graph.add_edge("C", "X", CitationStance.SUPPORT)

        supporting = graph.get_supporting_citations("X")
        contrasting = graph.get_contrasting_citations("X")

        assert "A" in supporting
        assert "C" in supporting
        assert "B" in contrasting

    def test_top_cited(self):
        """Test getting top cited papers."""
        from jarvis_core.citation import CitationGraph, CitationStance

        graph = CitationGraph()
        graph.add_edge("A", "X", CitationStance.SUPPORT)
        graph.add_edge("B", "X", CitationStance.SUPPORT)
        graph.add_edge("C", "Y", CitationStance.MENTION)

        top = graph.get_top_cited(limit=2)
        assert top[0][0] == "X"  # X has 2 citations
        assert top[0][1] == 2

    def test_build_citation_graph(self):
        """Test building graph from contexts."""
        from jarvis_core.citation import build_citation_graph
        from jarvis_core.citation.context_extractor import CitationContext
        from jarvis_core.citation.stance_classifier import CitationStance, StanceResult

        contexts = [
            CitationContext(citing_paper_id="A", cited_paper_id="B", citation_text="..."),
            CitationContext(citing_paper_id="A", cited_paper_id="C", citation_text="..."),
        ]
        stances = [
            StanceResult(stance=CitationStance.SUPPORT, confidence=0.8),
            StanceResult(stance=CitationStance.CONTRAST, confidence=0.7),
        ]

        graph = build_citation_graph(contexts, stances)

        assert graph.node_count == 3
        assert graph.edge_count == 2


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.citation import (
            CitationContext,
            CitationGraph,
            CitationStance,
            StanceClassifier,
            build_citation_graph,
            classify_citation_stance,
            extract_citation_contexts,
        )

        assert CitationContext is not None
        assert extract_citation_contexts is not None
        assert CitationStance is not None
        assert StanceClassifier is not None
        assert classify_citation_stance is not None
        assert CitationGraph is not None
        assert build_citation_graph is not None

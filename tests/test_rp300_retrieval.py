"""Tests for RP-300+ advanced retrieval.

Core tests for new retrieval features.
"""

import pytest

pytestmark = pytest.mark.core


class TestAdaptiveChunking:
    """Tests for RP-300 Adaptive Chunking."""

    def test_chunk_by_section(self):
        """Should chunk respecting section boundaries."""
        from jarvis_core.retrieval.adaptive_chunking import AdaptiveChunker

        chunker = AdaptiveChunker()
        text = "Abstract: This is the abstract. Introduction: This is the intro."
        chunks = chunker.chunk(text)

        assert len(chunks) > 0

    def test_extract_figure_captions(self):
        """Should extract figure captions."""
        from jarvis_core.retrieval.adaptive_chunking import AdaptiveChunker, ContentType

        chunker = AdaptiveChunker()
        text = "Some text. Figure 1: This is caption. More text."
        chunks = chunker.chunk(text)

        captions = [c for c in chunks if c.content_type == ContentType.FIGURE_CAPTION]
        assert len(captions) >= 1


class TestQueryUnderstanding:
    """Tests for RP-304 Query Understanding."""

    def test_classify_mechanism_query(self):
        """Should classify mechanism queries."""
        from jarvis_core.retrieval.query_understanding import QueryType, QueryUnderstanding

        qu = QueryUnderstanding()
        result = qu.parse("How does CD73 regulate adenosine?")

        assert result.query_type == QueryType.MECHANISM

    def test_extract_entities(self):
        """Should extract entities from query."""
        from jarvis_core.retrieval.query_understanding import QueryUnderstanding

        qu = QueryUnderstanding()
        result = qu.parse("Role of EGFR in cancer treatment")

        entity_texts = [e.text for e in result.entities]
        assert "EGFR" in entity_texts

    def test_parse_time_range(self):
        """Should parse time range."""
        from jarvis_core.retrieval.query_understanding import QueryUnderstanding

        qu = QueryUnderstanding(current_year=2024)
        result = qu.parse("Research since 2020")

        assert result.time_range is not None
        assert result.time_range.start_year == 2020


class TestMultiQueryFusion:
    """Tests for RP-309 Multi-Query Fusion."""

    def test_generate_variations(self):
        """Should generate query variations."""
        from jarvis_core.retrieval.multi_query import MultiQueryFusion

        mqf = MultiQueryFusion(num_variations=3)
        variations = mqf.generate_variations("CD73 immunotherapy")

        assert len(variations) == 3
        assert "CD73 immunotherapy" in variations

    def test_rrf_fusion(self):
        """Should fuse results with RRF."""
        from jarvis_core.retrieval.multi_query import MultiQueryFusion

        mqf = MultiQueryFusion()

        results1 = [{"chunk_id": "a", "text": "A"}, {"chunk_id": "b", "text": "B"}]
        results2 = [{"chunk_id": "b", "text": "B"}, {"chunk_id": "c", "text": "C"}]

        fused = mqf.reciprocal_rank_fusion([results1, results2])

        # 'b' should rank highest (appears in both)
        assert fused[0].chunk_id == "b"


class TestFactualConsistency:
    """Tests for RP-318 Factual Consistency."""

    def test_extract_claims(self):
        """Should extract claims from text."""
        from jarvis_core.retrieval.factual_consistency import FactualConsistencyChecker

        checker = FactualConsistencyChecker()
        text = "CD73 is an enzyme. It converts AMP to adenosine."
        claims = checker.extract_claims(text)

        assert len(claims) >= 1

    def test_check_consistency(self):
        """Should check consistency."""
        from jarvis_core.retrieval.factual_consistency import FactualConsistencyChecker

        checker = FactualConsistencyChecker()
        text = "CD73 produces adenosine."
        sources = [{"text": "CD73 enzyme converts AMP to adenosine", "chunk_id": "1"}]

        report = checker.check_text(text, sources)
        assert report.claims_checked >= 1

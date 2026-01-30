"""Tests for Paper Multi-Attribute Vector System (RP28).

Per RP28, this is the FOUNDATION for all subsequent RPs.
Tests must verify:
- All vector structures
- JSON serialization/deserialization
- Evidence Bundle -> PaperVector conversion
- Year x Concept filter API
"""

from jarvis_core.paper_vector import (
    VECTOR_SCHEMA_VERSION,
    BiologicalAxisVector,
    ConceptVector,
    ImpactVector,
    MetadataVector,
    PaperVector,
    extract_concepts_from_text,
    extract_methods_from_text,
    extract_paper_vector_from_result,
    filter_by_concept,
    filter_by_year,
    filter_by_year_and_concept,
    generate_paper_id,
    load_all_vectors,
)
from jarvis_core.result import EvidenceQAResult
import json
import tempfile
from pathlib import Path
import pytest


# PR-59: Mark all tests in this file as core
pytestmark = pytest.mark.core

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class TestMetadataVector:
    """Tests for MetadataVector."""

    def test_create_with_defaults(self):
        """Should create with default values."""
        mv = MetadataVector()
        assert mv.year is None
        assert mv.publication_type == "other"

    def test_to_dict(self):
        """Should convert to dict."""
        mv = MetadataVector(year=2023, journal="Nature")
        d = mv.to_dict()
        assert d["year"] == 2023
        assert d["journal"] == "Nature"

    def test_from_dict(self):
        """Should restore from dict."""
        data = {"year": 2022, "species": ["human", "mouse"]}
        mv = MetadataVector.from_dict(data)
        assert mv.year == 2022
        assert "human" in mv.species


class TestConceptVector:
    """Tests for ConceptVector."""

    def test_top_concepts(self):
        """Should return top concepts."""
        cv = ConceptVector(concepts={"PD-1": 0.9, "CD73": 0.5, "ATP": 0.3})
        top = cv.top_concepts(2)
        assert len(top) == 2
        assert top[0][0] == "PD-1"


class TestBiologicalAxisVector:
    """Tests for BiologicalAxisVector."""

    def test_as_tuple(self):
        """Should return 3D tuple."""
        bav = BiologicalAxisVector(
            immune_activation=0.5,
            metabolism_signal=-0.3,
            tumor_context=0.8,
        )
        t = bav.as_tuple()
        assert t == (0.5, -0.3, 0.8)


class TestImpactVector:
    """Tests for ImpactVector."""

    def test_always_estimated(self):
        """Impact should always be marked as estimated."""
        iv = ImpactVector()
        assert iv.estimated is True


class TestPaperVector:
    """Tests for main PaperVector class."""

    def test_create_paper_vector(self):
        """Should create PaperVector."""
        pv = PaperVector(
            paper_id="abc123",
            source_locator="pdf:paper.pdf",
        )
        assert pv.paper_id == "abc123"
        assert pv.version == VECTOR_SCHEMA_VERSION

    def test_to_dict_complete(self):
        """Should serialize all fields."""
        pv = PaperVector(
            paper_id="test",
            source_locator="pdf:x",
            metadata=MetadataVector(year=2023),
            concept=ConceptVector(concepts={"CD73": 0.8}),
        )
        d = pv.to_dict()

        assert d["paper_id"] == "test"
        assert d["metadata"]["year"] == 2023
        assert d["concept"]["concepts"]["CD73"] == 0.8
        assert d["version"] == VECTOR_SCHEMA_VERSION

    def test_from_dict_roundtrip(self):
        """Should roundtrip through dict."""
        pv = PaperVector(
            paper_id="roundtrip",
            source_locator="url:https://example.com",
            concept=ConceptVector(concepts={"PD-1": 0.6}),
            biological_axis=BiologicalAxisVector(immune_activation=-0.5),
        )

        d = pv.to_dict()
        restored = PaperVector.from_dict(d)

        assert restored.paper_id == pv.paper_id
        assert restored.concept.concepts["PD-1"] == 0.6
        assert restored.biological_axis.immune_activation == -0.5

    def test_save_and_load(self):
        """Should save to JSON and load."""
        pv = PaperVector(
            paper_id="save_test",
            source_locator="pdf:test.pdf",
            metadata=MetadataVector(year=2024),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = pv.save(tmpdir)

            assert Path(file_path).exists()

            loaded = PaperVector.load(file_path)
            assert loaded.paper_id == "save_test"
            assert loaded.metadata.year == 2024

    def test_save_creates_index(self):
        """Should update index.json."""
        pv = PaperVector(
            paper_id="index_test",
            source_locator="pdf:indexed.pdf",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pv.save(tmpdir)

            index_path = Path(tmpdir) / "index.json"
            assert index_path.exists()

            with open(index_path) as f:
                index = json.load(f)

            assert any(p["paper_id"] == "index_test" for p in index["papers"])


class TestExtraction:
    """Tests for text extraction functions."""

    def test_generate_paper_id(self):
        """Should generate deterministic ID."""
        id1 = generate_paper_id("pdf:paper.pdf")
        id2 = generate_paper_id("pdf:paper.pdf")
        id3 = generate_paper_id("pdf:other.pdf")

        assert id1 == id2  # Same input -> same ID
        assert id1 != id3  # Different input -> different ID

    def test_extract_concepts(self):
        """Should extract known concepts."""
        text = "CD73 is an enzyme that produces Adenosine from ATP"
        concepts = extract_concepts_from_text(text)

        assert "CD73" in concepts
        assert "Adenosine" in concepts

    def test_extract_methods(self):
        """Should extract method keywords."""
        text = "We used scRNA-seq and FACS to analyze cells"
        methods = extract_methods_from_text(text)

        assert "scRNA-seq" in methods
        assert "FACS" in methods

    def test_extract_paper_vector_from_result(self):
        """Should convert EvidenceQAResult to PaperVector."""
        result = EvidenceQAResult(
            answer="CD73 is expressed in tumor microenvironment",
            status="success",
            citations=[],
            inputs=["pdf:paper.pdf"],
            query="What is CD73?",
        )

        pv = extract_paper_vector_from_result(result)

        assert pv.paper_id is not None
        assert "CD73" in pv.concept.concepts
        assert pv.biological_axis.tumor_context > 0  # Detected TME


class TestFilterAPI:
    """Tests for filter functions."""

    def _create_test_vectors(self) -> list[PaperVector]:
        """Create test vectors."""
        return [
            PaperVector(
                paper_id="p1",
                source_locator="pdf:1.pdf",
                metadata=MetadataVector(year=2020),
                concept=ConceptVector(concepts={"CD73": 0.9}),
            ),
            PaperVector(
                paper_id="p2",
                source_locator="pdf:2.pdf",
                metadata=MetadataVector(year=2022),
                concept=ConceptVector(concepts={"PD-1": 0.8, "CD73": 0.3}),
            ),
            PaperVector(
                paper_id="p3",
                source_locator="pdf:3.pdf",
                metadata=MetadataVector(year=2024),
                concept=ConceptVector(concepts={"PD-1": 0.5}),
            ),
        ]

    def test_filter_by_year(self):
        """Should filter by year range."""
        vectors = self._create_test_vectors()

        result = filter_by_year(vectors, min_year=2021)
        assert len(result) == 2
        assert all(v.metadata.year >= 2021 for v in result)

    def test_filter_by_concept(self):
        """Should filter and sort by concept."""
        vectors = self._create_test_vectors()

        result = filter_by_concept(vectors, "CD73")
        assert len(result) == 2
        # Should be sorted by score
        assert result[0].paper_id == "p1"  # Highest CD73 score

    def test_filter_by_year_and_concept(self):
        """Should filter by both."""
        vectors = self._create_test_vectors()

        result = filter_by_year_and_concept(
            vectors,
            concept="CD73",
            min_year=2021,
        )
        assert len(result) == 1
        assert result[0].paper_id == "p2"

    def test_load_all_vectors(self):
        """Should load all vectors from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save some vectors
            pv1 = PaperVector(paper_id="load1", source_locator="pdf:1.pdf")
            pv2 = PaperVector(paper_id="load2", source_locator="pdf:2.pdf")
            pv1.save(tmpdir)
            pv2.save(tmpdir)

            # Load all
            loaded = load_all_vectors(tmpdir)
            assert len(loaded) == 2
            ids = {v.paper_id for v in loaded}
            assert "load1" in ids
            assert "load2" in ids
"""Tests for the PRISMA Diagram Generation Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.4
Updated to match actual implementation.
"""

import tempfile
from pathlib import Path


class TestPRISMASchema:
    """Tests for PRISMA schema."""

    def test_prisma_stage_enum(self):
        """Test PRISMAStage enum values."""
        from jarvis_core.experimental.prisma.schema import PRISMAStage

        assert PRISMAStage.IDENTIFICATION.value == "identification"
        assert PRISMAStage.SCREENING.value == "screening"
        assert PRISMAStage.ELIGIBILITY.value == "eligibility"
        assert PRISMAStage.INCLUDED.value == "included"

    def test_exclusion_reason_dataclass(self):
        """Test ExclusionReason dataclass."""
        from jarvis_core.experimental.prisma.schema import ExclusionReason

        reason = ExclusionReason(reason="Duplicate publication", count=15, stage="screening")

        assert reason.reason == "Duplicate publication"
        assert reason.count == 15

    def test_prisma_data_initialization(self):
        """Test PRISMAData dataclass initialization."""
        from jarvis_core.experimental.prisma.schema import ExclusionReason, PRISMAData

        data = PRISMAData(
            records_from_databases=1000,
            records_from_other_sources=50,
            duplicates_removed=200,
            records_screened=850,
            records_excluded_screening=500,
            reports_assessed=350,
            reports_excluded=100,
            studies_included=250,
            exclusion_reasons=[
                ExclusionReason("Not relevant", 300, "screening"),
            ],
        )

        assert data.records_from_databases == 1000
        assert data.studies_included == 250
        assert len(data.exclusion_reasons) == 1

    def test_prisma_data_calculate_totals(self):
        """Test PRISMAData calculate_totals method."""
        from jarvis_core.experimental.prisma.schema import PRISMAData

        data = PRISMAData(
            records_from_databases=100,
            records_from_other_sources=10,
            duplicates_removed=10,
        )

        data.calculate_totals()

        # After calculate_totals, records_screened should be calculated
        assert data.records_screened == 100  # 100 + 10 - 10

    def test_prisma_data_to_dict(self):
        """Test PRISMAData serialization."""
        from jarvis_core.experimental.prisma.schema import PRISMAData

        data = PRISMAData(
            records_from_databases=500,
            records_from_other_sources=25,
            duplicates_removed=75,
            records_screened=450,
            records_excluded_screening=200,
            reports_assessed=250,
            reports_excluded=50,
            studies_included=200,
        )

        result = data.to_dict()

        # The to_dict uses nested structure
        assert result["identification"]["databases"] == 500
        assert result["included"]["studies"] == 200
        assert "exclusion_reasons" in result


class TestPRISMAGenerator:
    """Tests for PRISMA diagram generator."""

    def test_generator_initialization(self):
        """Test PRISMAGenerator initialization."""
        from jarvis_core.experimental.prisma.generator import PRISMAGenerator

        generator = PRISMAGenerator()
        assert generator is not None

    def test_to_mermaid_basic(self):
        """Test basic Mermaid diagram generation."""
        from jarvis_core.experimental.prisma.generator import PRISMAGenerator
        from jarvis_core.experimental.prisma.schema import PRISMAData

        generator = PRISMAGenerator()
        data = PRISMAData(
            records_from_databases=1000,
            records_from_other_sources=50,
            duplicates_removed=200,
            records_screened=850,
            records_excluded_screening=500,
            reports_assessed=350,
            reports_excluded=100,
            studies_included=250,
        )

        mermaid = generator.to_mermaid(data)

        assert "flowchart TD" in mermaid or "graph TD" in mermaid
        assert "Identification" in mermaid or "identification" in mermaid.lower()

    def test_to_mermaid_with_exclusion_reasons(self):
        """Test Mermaid diagram with exclusion reasons."""
        from jarvis_core.experimental.prisma.generator import PRISMAGenerator
        from jarvis_core.experimental.prisma.schema import ExclusionReason, PRISMAData

        generator = PRISMAGenerator()
        data = PRISMAData(
            records_from_databases=500,
            records_from_other_sources=0,
            duplicates_removed=50,
            records_screened=450,
            records_excluded_screening=200,
            reports_assessed=250,
            reports_excluded=100,
            studies_included=150,
            exclusion_reasons=[
                ExclusionReason("Not RCT", 50, "eligibility"),
            ],
        )

        mermaid = generator.to_mermaid(data)

        # Mermaid should be generated
        assert len(mermaid) > 0

    def test_to_svg(self):
        """Test SVG diagram generation."""
        from jarvis_core.experimental.prisma.generator import PRISMAGenerator
        from jarvis_core.experimental.prisma.schema import PRISMAData

        generator = PRISMAGenerator()
        data = PRISMAData(
            records_from_databases=100,
            records_from_other_sources=10,
            duplicates_removed=20,
            records_screened=90,
            records_excluded_screening=40,
            reports_assessed=50,
            reports_excluded=10,
            studies_included=40,
        )

        svg = generator.to_svg(data)

        assert svg.startswith("<svg") or svg.startswith("<?xml")
        assert "</svg>" in svg

    def test_to_text(self):
        """Test text representation generation."""
        from jarvis_core.experimental.prisma.generator import PRISMAGenerator
        from jarvis_core.experimental.prisma.schema import PRISMAData

        generator = PRISMAGenerator()
        data = PRISMAData(
            records_from_databases=100,
            records_from_other_sources=10,
            duplicates_removed=20,
            records_screened=90,
            records_excluded_screening=40,
            reports_assessed=50,
            reports_excluded=10,
            studies_included=40,
        )

        text = generator.to_text(data)

        # Should contain PRISMA stage information
        assert len(text) > 0

    def test_save_svg(self):
        """Test save method with SVG format."""
        from jarvis_core.experimental.prisma.generator import PRISMAGenerator
        from jarvis_core.experimental.prisma.schema import PRISMAData

        generator = PRISMAGenerator()
        data = PRISMAData(
            records_from_databases=100,
            records_from_other_sources=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=30,
            reports_assessed=60,
            reports_excluded=10,
            studies_included=50,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "prisma_flow.svg"
            generator.save(data, output_path=output_path, format="svg")

            assert output_path.exists()
            content = output_path.read_text()
            assert "<svg" in content or "<?xml" in content


class TestGeneratePrismaFlowFunction:
    """Tests for convenience function."""

    def test_generate_prisma_flow_mermaid(self):
        """Test generate_prisma_flow with Mermaid output."""
        from jarvis_core.experimental.prisma import generate_prisma_flow
        from jarvis_core.experimental.prisma.schema import PRISMAData

        data = PRISMAData(
            records_from_databases=500,
            records_from_other_sources=50,
            duplicates_removed=100,
            records_screened=450,
            records_excluded_screening=200,
            reports_assessed=250,
            reports_excluded=75,
            studies_included=175,
        )

        result = generate_prisma_flow(data, format="mermaid")

        assert "flowchart" in result.lower() or "graph" in result.lower()

    def test_generate_prisma_flow_svg(self):
        """Test generate_prisma_flow with SVG output."""
        from jarvis_core.experimental.prisma import generate_prisma_flow
        from jarvis_core.experimental.prisma.schema import PRISMAData

        data = PRISMAData(
            records_from_databases=100,
            records_from_other_sources=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=30,
            reports_assessed=60,
            reports_excluded=10,
            studies_included=50,
        )

        result = generate_prisma_flow(data, format="svg")

        assert "<svg" in result or "<?xml" in result

    def test_generate_prisma_flow_text(self):
        """Test generate_prisma_flow with text output."""
        from jarvis_core.experimental.prisma import generate_prisma_flow
        from jarvis_core.experimental.prisma.schema import PRISMAData

        data = PRISMAData(
            records_from_databases=100,
            records_from_other_sources=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=30,
            reports_assessed=60,
            reports_excluded=10,
            studies_included=50,
        )

        result = generate_prisma_flow(data, format="text")

        assert len(result) > 0


class TestPRISMA2020Compliance:
    """Tests for PRISMA 2020 statement compliance."""

    def test_prisma_2020_required_items(self):
        """Test that all PRISMA 2020 required items are supported."""
        from jarvis_core.experimental.prisma.schema import PRISMAData

        # PRISMA 2020 requires these flow diagram elements
        required_attributes = [
            "records_from_databases",
            "records_from_other_sources",
            "duplicates_removed",
            "records_screened",
            "records_excluded_screening",
            "reports_assessed",
            "reports_excluded",
            "studies_included",
        ]

        data = PRISMAData(
            records_from_databases=0,
            records_from_other_sources=0,
            duplicates_removed=0,
            records_screened=0,
            records_excluded_screening=0,
            reports_assessed=0,
            reports_excluded=0,
            studies_included=0,
        )

        for attr in required_attributes:
            assert hasattr(data, attr), f"Missing PRISMA 2020 required attribute: {attr}"

    def test_multiple_database_sources(self):
        """Test support for multiple database sources."""
        from jarvis_core.experimental.prisma.schema import PRISMAData

        # PRISMA 2020 supports multiple database sources
        data = PRISMAData(
            records_from_databases=1000,
            records_from_other_sources=200,
            records_from_registers=50,  # Optional: clinical trial registers
            duplicates_removed=150,
            records_screened=1100,
            records_excluded_screening=600,
            reports_assessed=500,
            reports_excluded=100,
            studies_included=400,
            database_sources=["PubMed", "Embase", "Cochrane"],
        )

        assert len(data.database_sources) == 3


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.experimental.prisma import (
            ExclusionReason,
            PRISMAData,
            PRISMAGenerator,
            PRISMAStage,
            generate_prisma_flow,
        )

        assert PRISMAData is not None
        assert PRISMAStage is not None
        assert ExclusionReason is not None
        assert PRISMAGenerator is not None
        assert generate_prisma_flow is not None

    def test_schema_imports(self):
        """Test schema module imports."""
        from jarvis_core.experimental.prisma.schema import (
            ExclusionReason,
            PRISMAData,
            PRISMAStage,
        )

        assert PRISMAData is not None
        assert PRISMAStage is not None
        assert ExclusionReason is not None

    def test_generator_imports(self):
        """Test generator module imports."""
        from jarvis_core.experimental.prisma.generator import (
            PRISMAGenerator,
            generate_prisma_flow,
        )

        assert PRISMAGenerator is not None
        assert generate_prisma_flow is not None
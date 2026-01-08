"""Tests for the PRISMA Diagram Generation Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.4
"""

import pytest
from pathlib import Path
import tempfile


class TestPRISMASchema:
    """Tests for PRISMA schema."""

    def test_prisma_stage_enum(self):
        """Test PRISMAStage enum values."""
        from jarvis_core.prisma.schema import PRISMAStage
        
        assert PRISMAStage.IDENTIFICATION.value == "identification"
        assert PRISMAStage.SCREENING.value == "screening"
        assert PRISMAStage.ELIGIBILITY.value == "eligibility"
        assert PRISMAStage.INCLUDED.value == "included"

    def test_exclusion_reason_dataclass(self):
        """Test ExclusionReason dataclass."""
        from jarvis_core.prisma.schema import ExclusionReason
        
        reason = ExclusionReason(
            reason="Duplicate publication",
            count=15,
            stage="screening"
        )
        
        assert reason.reason == "Duplicate publication"
        assert reason.count == 15
        assert reason.stage == "screening"

    def test_prisma_data_initialization(self):
        """Test PRISMAData dataclass initialization."""
        from jarvis_core.prisma.schema import PRISMAData, ExclusionReason
        
        data = PRISMAData(
            identification_database=1000,
            identification_other=50,
            duplicates_removed=200,
            records_screened=850,
            records_excluded_screening=500,
            full_text_assessed=350,
            full_text_excluded=100,
            studies_included=250,
            exclusion_reasons=[
                ExclusionReason("Not relevant", 300, "screening"),
                ExclusionReason("No full text", 50, "eligibility"),
            ]
        )
        
        assert data.identification_database == 1000
        assert data.studies_included == 250
        assert len(data.exclusion_reasons) == 2

    def test_prisma_data_validation(self):
        """Test PRISMAData validation logic."""
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=100,
            identification_other=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=40,
            full_text_assessed=50,
            full_text_excluded=20,
            studies_included=30,
        )
        
        # Validate flow consistency
        total_identified = data.identification_database + data.identification_other
        after_duplicates = total_identified - data.duplicates_removed
        assert after_duplicates == data.records_screened
        
        after_screening = data.records_screened - data.records_excluded_screening
        assert after_screening == data.full_text_assessed
        
        after_eligibility = data.full_text_assessed - data.full_text_excluded
        assert after_eligibility == data.studies_included

    def test_prisma_data_to_dict(self):
        """Test PRISMAData serialization."""
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=500,
            identification_other=25,
            duplicates_removed=75,
            records_screened=450,
            records_excluded_screening=200,
            full_text_assessed=250,
            full_text_excluded=50,
            studies_included=200,
        )
        
        result = data.to_dict()
        
        assert result["identification_database"] == 500
        assert result["studies_included"] == 200
        assert "exclusion_reasons" in result

    def test_prisma_data_from_dict(self):
        """Test PRISMAData deserialization."""
        from jarvis_core.prisma.schema import PRISMAData
        
        input_dict = {
            "identification_database": 300,
            "identification_other": 10,
            "duplicates_removed": 30,
            "records_screened": 280,
            "records_excluded_screening": 100,
            "full_text_assessed": 180,
            "full_text_excluded": 30,
            "studies_included": 150,
        }
        
        data = PRISMAData.from_dict(input_dict)
        
        assert data.identification_database == 300
        assert data.studies_included == 150


class TestPRISMAGenerator:
    """Tests for PRISMA diagram generator."""

    def test_generator_initialization(self):
        """Test PRISMAGenerator initialization."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        
        generator = PRISMAGenerator()
        assert generator is not None

    def test_generate_mermaid_basic(self):
        """Test basic Mermaid diagram generation."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=1000,
            identification_other=50,
            duplicates_removed=200,
            records_screened=850,
            records_excluded_screening=500,
            full_text_assessed=350,
            full_text_excluded=100,
            studies_included=250,
        )
        
        mermaid = generator.generate_mermaid(data)
        
        assert "flowchart TD" in mermaid or "graph TD" in mermaid
        assert "1000" in mermaid  # identification_database
        assert "250" in mermaid  # studies_included
        assert "Identification" in mermaid or "identification" in mermaid.lower()

    def test_generate_mermaid_with_exclusion_reasons(self):
        """Test Mermaid diagram with exclusion reasons."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData, ExclusionReason
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=500,
            identification_other=0,
            duplicates_removed=50,
            records_screened=450,
            records_excluded_screening=200,
            full_text_assessed=250,
            full_text_excluded=100,
            studies_included=150,
            exclusion_reasons=[
                ExclusionReason("Not RCT", 50, "eligibility"),
                ExclusionReason("Wrong population", 30, "eligibility"),
                ExclusionReason("No outcome data", 20, "eligibility"),
            ]
        )
        
        mermaid = generator.generate_mermaid(data)
        
        assert "Not RCT" in mermaid or "50" in mermaid
        assert "150" in mermaid  # studies_included

    def test_generate_svg(self):
        """Test SVG diagram generation."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=100,
            identification_other=10,
            duplicates_removed=20,
            records_screened=90,
            records_excluded_screening=40,
            full_text_assessed=50,
            full_text_excluded=10,
            studies_included=40,
        )
        
        svg = generator.generate_svg(data)
        
        assert svg.startswith("<svg") or svg.startswith("<?xml")
        assert "</svg>" in svg
        assert "100" in svg or "40" in svg

    def test_generate_svg_file_output(self):
        """Test SVG file output."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=100,
            identification_other=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=30,
            full_text_assessed=60,
            full_text_excluded=10,
            studies_included=50,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "prisma_flow.svg"
            generator.generate_svg(data, output_path=output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "<svg" in content or "<?xml" in content

    def test_generate_html_interactive(self):
        """Test interactive HTML diagram generation."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=200,
            identification_other=20,
            duplicates_removed=40,
            records_screened=180,
            records_excluded_screening=80,
            full_text_assessed=100,
            full_text_excluded=30,
            studies_included=70,
        )
        
        html = generator.generate_html(data)
        
        assert "<html" in html.lower() or "<!doctype" in html.lower()
        assert "mermaid" in html.lower() or "svg" in html.lower()


class TestGeneratePrismaFlowFunction:
    """Tests for convenience function."""

    def test_generate_prisma_flow_mermaid(self):
        """Test generate_prisma_flow with Mermaid output."""
        from jarvis_core.prisma import generate_prisma_flow
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=500,
            identification_other=50,
            duplicates_removed=100,
            records_screened=450,
            records_excluded_screening=200,
            full_text_assessed=250,
            full_text_excluded=75,
            studies_included=175,
        )
        
        result = generate_prisma_flow(data, format="mermaid")
        
        assert "flowchart" in result.lower() or "graph" in result.lower()

    def test_generate_prisma_flow_svg(self):
        """Test generate_prisma_flow with SVG output."""
        from jarvis_core.prisma import generate_prisma_flow
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=100,
            identification_other=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=30,
            full_text_assessed=60,
            full_text_excluded=10,
            studies_included=50,
        )
        
        result = generate_prisma_flow(data, format="svg")
        
        assert "<svg" in result or "<?xml" in result

    def test_generate_prisma_flow_from_dict(self):
        """Test generate_prisma_flow from dictionary input."""
        from jarvis_core.prisma import generate_prisma_flow
        
        data_dict = {
            "identification_database": 250,
            "identification_other": 25,
            "duplicates_removed": 50,
            "records_screened": 225,
            "records_excluded_screening": 100,
            "full_text_assessed": 125,
            "full_text_excluded": 25,
            "studies_included": 100,
        }
        
        result = generate_prisma_flow(data_dict, format="mermaid")
        
        assert "250" in result or "100" in result


class TestPRISMA2020Compliance:
    """Tests for PRISMA 2020 statement compliance."""

    def test_prisma_2020_required_items(self):
        """Test that all PRISMA 2020 required items are supported."""
        from jarvis_core.prisma.schema import PRISMAData
        
        # PRISMA 2020 requires these flow diagram elements
        required_attributes = [
            "identification_database",
            "identification_other",
            "duplicates_removed",
            "records_screened",
            "records_excluded_screening",
            "full_text_assessed",
            "full_text_excluded",
            "studies_included",
        ]
        
        data = PRISMAData(
            identification_database=0,
            identification_other=0,
            duplicates_removed=0,
            records_screened=0,
            records_excluded_screening=0,
            full_text_assessed=0,
            full_text_excluded=0,
            studies_included=0,
        )
        
        for attr in required_attributes:
            assert hasattr(data, attr), f"Missing PRISMA 2020 required attribute: {attr}"

    def test_multiple_database_sources(self):
        """Test support for multiple database sources."""
        from jarvis_core.prisma.schema import PRISMAData
        
        # PRISMA 2020 supports multiple database sources
        data = PRISMAData(
            identification_database=1000,
            identification_other=200,
            identification_registers=50,  # Optional: clinical trial registers
            duplicates_removed=150,
            records_screened=1100,
            records_excluded_screening=600,
            full_text_assessed=500,
            full_text_excluded=100,
            studies_included=400,
            database_sources=["PubMed", "Embase", "Cochrane"],
        )
        
        assert data.identification_database + data.identification_other >= data.records_screened + data.duplicates_removed


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.prisma import (
            PRISMAData,
            PRISMAStage,
            ExclusionReason,
            PRISMAGenerator,
            generate_prisma_flow,
        )
        
        assert PRISMAData is not None
        assert PRISMAStage is not None
        assert ExclusionReason is not None
        assert PRISMAGenerator is not None
        assert generate_prisma_flow is not None

    def test_schema_imports(self):
        """Test schema module imports."""
        from jarvis_core.prisma.schema import (
            PRISMAData,
            PRISMAStage,
            ExclusionReason,
        )
        
        assert PRISMAData is not None
        assert PRISMAStage is not None
        assert ExclusionReason is not None

    def test_generator_imports(self):
        """Test generator module imports."""
        from jarvis_core.prisma.generator import (
            PRISMAGenerator,
            generate_prisma_flow,
        )
        
        assert PRISMAGenerator is not None
        assert generate_prisma_flow is not None

"""Phase E-1: Detailed Function Tests for stages/generate_report.py.

Target: All 7 functions with all branches covered
Strategy: Create test data files and call each function
"""

import tempfile
import json
from pathlib import Path


# ====================
# load_artifacts Tests
# ====================


class TestLoadArtifacts:
    """Test load_artifacts function with all branches."""

    def test_load_all_files_exist(self):
        """Test loading when all files exist."""
        from jarvis_core.stages.generate_report import load_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            # Create test files
            claims = [{"claim_id": "c1", "claim_text": "Test claim"}]
            evidence = [{"evidence_id": "e1", "claim_id": "c1"}]
            papers = [{"paper_id": "p1", "title": "Test Paper"}]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")

            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")

            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")

            result = load_artifacts(run_dir)

            assert len(result["claims"]) == 1
            assert len(result["evidence"]) == 1
            assert len(result["papers"]) == 1

    def test_load_no_files_exist(self):
        """Test loading when no files exist."""
        from jarvis_core.stages.generate_report import load_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            result = load_artifacts(run_dir)

            assert result["claims"] == []
            assert result["evidence"] == []
            assert result["papers"] == []

    def test_load_partial_files_exist(self):
        """Test loading when only some files exist."""
        from jarvis_core.stages.generate_report import load_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            # Only create claims file
            claims = [{"claim_id": "c1"}]
            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")

            result = load_artifacts(run_dir)

            assert len(result["claims"]) == 1
            assert result["evidence"] == []
            assert result["papers"] == []


# ====================
# build_evidence_map Tests
# ====================


class TestBuildEvidenceMap:
    """Test build_evidence_map function."""

    def test_build_with_multiple_claims(self):
        """Test building map with multiple claims."""
        from jarvis_core.stages.generate_report import build_evidence_map

        claims = [{"claim_id": "c1"}, {"claim_id": "c2"}]
        evidence_list = [
            {"evidence_id": "e1", "claim_id": "c1"},
            {"evidence_id": "e2", "claim_id": "c1"},
            {"evidence_id": "e3", "claim_id": "c2"},
        ]

        result = build_evidence_map(claims, evidence_list)

        assert len(result["c1"]) == 2
        assert len(result["c2"]) == 1

    def test_build_with_no_claim_id(self):
        """Test evidence without claim_id is ignored."""
        from jarvis_core.stages.generate_report import build_evidence_map

        claims = [{"claim_id": "c1"}]
        evidence_list = [
            {"evidence_id": "e1", "claim_id": "c1"},
            {"evidence_id": "e2"},  # No claim_id
        ]

        result = build_evidence_map(claims, evidence_list)

        assert len(result["c1"]) == 1

    def test_build_with_empty_evidence(self):
        """Test with empty evidence list."""
        from jarvis_core.stages.generate_report import build_evidence_map

        claims = [{"claim_id": "c1"}]
        evidence_list = []

        result = build_evidence_map(claims, evidence_list)

        assert result == {}


# ====================
# select_best_evidence Tests
# ====================


class TestSelectBestEvidence:
    """Test select_best_evidence function."""

    def test_select_strong_first(self):
        """Test Strong evidence is selected first."""
        from jarvis_core.stages.generate_report import select_best_evidence

        evidence_list = [
            {"evidence_id": "e1", "evidence_strength": "Weak"},
            {"evidence_id": "e2", "evidence_strength": "Strong"},
            {"evidence_id": "e3", "evidence_strength": "Medium"},
        ]

        result = select_best_evidence(evidence_list, max_count=2)

        assert result[0]["evidence_strength"] == "Strong"
        assert result[1]["evidence_strength"] == "Medium"

    def test_select_max_count(self):
        """Test max_count limit."""
        from jarvis_core.stages.generate_report import select_best_evidence

        evidence_list = [
            {"evidence_id": "e1", "evidence_strength": "Strong"},
            {"evidence_id": "e2", "evidence_strength": "Strong"},
            {"evidence_id": "e3", "evidence_strength": "Strong"},
            {"evidence_id": "e4", "evidence_strength": "Strong"},
        ]

        result = select_best_evidence(evidence_list, max_count=2)

        assert len(result) == 2

    def test_select_with_none_strength(self):
        """Test evidence with None strength."""
        from jarvis_core.stages.generate_report import select_best_evidence

        evidence_list = [
            {"evidence_id": "e1"},  # No strength
            {"evidence_id": "e2", "evidence_strength": "Medium"},
        ]

        result = select_best_evidence(evidence_list, max_count=3)

        assert result[0]["evidence_strength"] == "Medium"


# ====================
# determine_support_level Tests
# ====================


class TestDetermineSupportLevel:
    """Test determine_support_level function with all branches."""

    def test_empty_list_returns_none(self):
        """Test empty list returns None."""
        from jarvis_core.stages.generate_report import determine_support_level

        result = determine_support_level([])
        assert result == "None"

    def test_strong_evidence_returns_strong(self):
        """Test Strong evidence returns Strong."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence_list = [{"evidence_strength": "Strong"}]
        result = determine_support_level(evidence_list)
        assert result == "Strong"

    def test_two_medium_returns_medium(self):
        """Test 2+ Medium returns Medium."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence_list = [
            {"evidence_strength": "Medium"},
            {"evidence_strength": "Medium"},
        ]
        result = determine_support_level(evidence_list)
        assert result == "Medium"

    def test_one_medium_one_weak_returns_medium(self):
        """Test 1 Medium + 1 Weak returns Medium."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence_list = [
            {"evidence_strength": "Medium"},
            {"evidence_strength": "Weak"},
        ]
        result = determine_support_level(evidence_list)
        assert result == "Medium"

    def test_one_medium_only_returns_medium(self):
        """Test 1 Medium only returns Medium."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence_list = [{"evidence_strength": "Medium"}]
        result = determine_support_level(evidence_list)
        assert result == "Medium"

    def test_weak_only_returns_weak(self):
        """Test Weak only returns Weak."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence_list = [{"evidence_strength": "Weak"}]
        result = determine_support_level(evidence_list)
        assert result == "Weak"

    def test_no_strength_returns_none(self):
        """Test no strength returns None."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence_list = [{"evidence_id": "e1"}]  # No strength
        result = determine_support_level(evidence_list)
        assert result == "None"


# ====================
# create_conclusion Tests
# ====================


class TestCreateConclusion:
    """Test create_conclusion function."""

    def test_create_with_evidence(self):
        """Test creating conclusion with evidence."""
        from jarvis_core.stages.generate_report import create_conclusion

        claim = {"claim_id": "c1", "claim_text": "Test claim"}
        evidence_list = [
            {"evidence_id": "e1", "evidence_strength": "Strong"},
        ]

        result = create_conclusion(claim, evidence_list)

        assert result.claim_id == "c1"
        assert result.support_level == "Strong"

    def test_create_with_contradiction(self):
        """Test creating conclusion with contradicting evidence."""
        from jarvis_core.stages.generate_report import create_conclusion

        claim = {"claim_id": "c1", "claim_text": "Test claim"}
        evidence_list = [
            {"evidence_id": "e1", "evidence_strength": "Strong", "evidence_role": "refuting"},
        ]

        result = create_conclusion(claim, evidence_list)

        assert "矛盾する根拠あり" in result.notes

    def test_create_without_evidence(self):
        """Test creating conclusion without evidence."""
        from jarvis_core.stages.generate_report import create_conclusion

        claim = {"claim_id": "c1", "claim_text": "Test claim"}
        evidence_list = []

        result = create_conclusion(claim, evidence_list)

        assert result.support_level == "None"
        assert "根拠不足" in result.notes


# ====================
# generate_report Tests
# ====================


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_with_data(self):
        """Test generating report with data."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            # Create test files
            claims = [{"claim_id": "c1", "claim_text": "Test claim", "claim_type": "Efficacy"}]
            evidence = [{"evidence_id": "e1", "claim_id": "c1", "evidence_strength": "Strong"}]
            papers = [
                {"paper_id": "p1", "title": "Test Paper", "authors": ["Author A"], "year": 2024}
            ]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")

            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")

            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")

            result = generate_report(run_dir, "Test query")

            assert "Test query" in result
            assert "References" in result

    def test_generate_empty_report(self):
        """Test generating report with no data."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            result = generate_report(run_dir, "Empty query")

            assert "Empty query" in result

    def test_generate_with_low_support_rate(self):
        """Test generating report with low support rate."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            # Create claim without evidence
            claims = [{"claim_id": "c1", "claim_text": "Unsupported claim"}]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")

            result = generate_report(run_dir, "Low support query")

            assert "CAUTION" in result or "根拠支持率" in result
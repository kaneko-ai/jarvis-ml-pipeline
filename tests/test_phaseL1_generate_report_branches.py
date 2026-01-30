"""Phase L-1: Complete Branch Coverage for generate_report.py.

Strategy: Analyze each branch (if/else, for) and create tests that hit EVERY line
Based on source code analysis of lines 1-322
"""

import tempfile
import json
from pathlib import Path


class TestLoadArtifactsAllBranches:
    """Test load_artifacts() - lines 18-53."""

    def test_all_files_exist(self):
        """Covers lines 31-33, 39-41, 47-49."""
        from jarvis_core.stages.generate_report import load_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            # Create all files
            (run_dir / "claims.jsonl").write_text('{"claim_id": "c1"}\n')
            (run_dir / "evidence.jsonl").write_text('{"evidence_id": "e1"}\n')
            (run_dir / "papers.jsonl").write_text('{"paper_id": "p1"}\n')

            result = load_artifacts(run_dir)
            assert len(result["claims"]) == 1
            assert len(result["evidence"]) == 1
            assert len(result["papers"]) == 1

    def test_no_files_exist(self):
        """Covers lines 34-35, 42-43, 50-51."""
        from jarvis_core.stages.generate_report import load_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            result = load_artifacts(run_dir)
            assert result["claims"] == []
            assert result["evidence"] == []
            assert result["papers"] == []

    def test_partial_files_exist(self):
        """Covers mixed branches."""
        from jarvis_core.stages.generate_report import load_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "claims.jsonl").write_text('{"claim_id": "c1"}\n')
            # No evidence or papers files

            result = load_artifacts(run_dir)
            assert len(result["claims"]) == 1
            assert result["evidence"] == []
            assert result["papers"] == []


class TestBuildEvidenceMapAllBranches:
    """Test build_evidence_map() - lines 56-75."""

    def test_empty_evidence(self):
        """Covers empty loop case."""
        from jarvis_core.stages.generate_report import build_evidence_map

        result = build_evidence_map([], [])
        assert result == {}

    def test_evidence_with_claim_id(self):
        """Covers lines 68-73."""
        from jarvis_core.stages.generate_report import build_evidence_map

        claims = [{"claim_id": "c1"}, {"claim_id": "c2"}]
        evidence = [
            {"evidence_id": "e1", "claim_id": "c1"},
            {"evidence_id": "e2", "claim_id": "c1"},
            {"evidence_id": "e3", "claim_id": "c2"},
        ]

        result = build_evidence_map(claims, evidence)
        assert len(result["c1"]) == 2
        assert len(result["c2"]) == 1

    def test_evidence_without_claim_id(self):
        """Covers line 70 (if claim_id: False branch)."""
        from jarvis_core.stages.generate_report import build_evidence_map

        claims = [{"claim_id": "c1"}]
        evidence = [
            {"evidence_id": "e1"},  # No claim_id!
            {"evidence_id": "e2", "claim_id": None},  # claim_id is None
        ]

        result = build_evidence_map(claims, evidence)
        assert "c1" not in result or len(result.get("c1", [])) == 0


class TestSelectBestEvidenceAllBranches:
    """Test select_best_evidence() - lines 78-96."""

    def test_empty_list(self):
        """Covers empty input."""
        from jarvis_core.stages.generate_report import select_best_evidence

        result = select_best_evidence([], max_count=3)
        assert result == []

    def test_sorting_by_strength(self):
        """Covers lines 91-94."""
        from jarvis_core.stages.generate_report import select_best_evidence

        evidence = [
            {"id": 1, "evidence_strength": "Weak"},
            {"id": 2, "evidence_strength": "Strong"},
            {"id": 3, "evidence_strength": "Medium"},
            {"id": 4, "evidence_strength": "None"},
        ]

        result = select_best_evidence(evidence, max_count=4)
        assert result[0]["evidence_strength"] == "Strong"
        assert result[1]["evidence_strength"] == "Medium"
        assert result[2]["evidence_strength"] == "Weak"
        assert result[3]["evidence_strength"] == "None"

    def test_max_count_limit(self):
        """Covers line 96."""
        from jarvis_core.stages.generate_report import select_best_evidence

        evidence = [{"id": i, "evidence_strength": "Medium"} for i in range(10)]

        result = select_best_evidence(evidence, max_count=3)
        assert len(result) == 3


class TestDetermineSupportLevelAllBranches:
    """Test determine_support_level() - lines 99-134."""

    def test_empty_list(self):
        """Covers line 114-115."""
        from jarvis_core.stages.generate_report import determine_support_level

        result = determine_support_level([])
        assert result == "None"

    def test_strong_evidence(self):
        """Covers lines 119-120."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence = [{"evidence_strength": "Strong"}]
        result = determine_support_level(evidence)
        assert result == "Strong"

    def test_two_or_more_medium(self):
        """Covers lines 125-126."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence = [
            {"evidence_strength": "Medium"},
            {"evidence_strength": "Medium"},
        ]
        result = determine_support_level(evidence)
        assert result == "Medium"

    def test_one_medium_and_weak(self):
        """Covers lines 127-128."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence = [
            {"evidence_strength": "Medium"},
            {"evidence_strength": "Weak"},
        ]
        result = determine_support_level(evidence)
        assert result == "Medium"

    def test_one_medium_only(self):
        """Covers lines 129-130."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence = [{"evidence_strength": "Medium"}]
        result = determine_support_level(evidence)
        assert result == "Medium"

    def test_weak_only(self):
        """Covers lines 131-132."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence = [{"evidence_strength": "Weak"}]
        result = determine_support_level(evidence)
        assert result == "Weak"

    def test_none_strength(self):
        """Covers lines 133-134."""
        from jarvis_core.stages.generate_report import determine_support_level

        evidence = [{"evidence_strength": "None"}]
        result = determine_support_level(evidence)
        assert result == "None"


class TestCreateConclusionAllBranches:
    """Test create_conclusion() - lines 137-182."""

    def test_no_contradiction(self):
        """Covers line 157 (False branch)."""
        from jarvis_core.stages.generate_report import create_conclusion

        claim = {"claim_id": "c1", "claim_text": "Test claim"}
        evidence = [
            {"evidence_id": "e1", "evidence_strength": "Strong", "evidence_role": "supporting"}
        ]

        result = create_conclusion(claim, evidence)
        assert "矛盾" not in result.notes

    def test_with_contradiction(self):
        """Covers line 157 (True branch), lines 170-171."""
        from jarvis_core.stages.generate_report import create_conclusion

        claim = {"claim_id": "c1", "claim_text": "Test claim"}
        evidence = [
            {"evidence_id": "e1", "evidence_strength": "Strong", "evidence_role": "refuting"}
        ]

        result = create_conclusion(claim, evidence)
        assert "矛盾" in result.notes

    def test_no_evidence_support(self):
        """Covers lines 172-173."""
        from jarvis_core.stages.generate_report import create_conclusion

        claim = {"claim_id": "c1", "claim_text": "Test claim"}
        evidence = []

        result = create_conclusion(claim, evidence)
        assert result.support_level == "None"
        assert "根拠不足" in result.notes

    def test_evidence_without_ids(self):
        """Covers line 166 (filter condition)."""
        from jarvis_core.stages.generate_report import create_conclusion

        claim = {"claim_id": "c1", "claim_text": "Test claim"}
        evidence = [{"evidence_strength": "Strong"}]  # No evidence_id!

        result = create_conclusion(claim, evidence)
        assert len(result.evidence_ids) == 0


class TestGenerateReportAllBranches:
    """Test generate_report() - lines 185-321."""

    def test_low_support_rate(self):
        """Covers lines 250-258 (support_rate < 0.90)."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            # Many claims, few with evidence
            claims = [{"claim_id": f"c{i}", "claim_text": f"Claim {i}"} for i in range(10)]
            evidence = [
                {"evidence_id": "e1", "claim_id": "c0", "evidence_strength": "Strong"}
            ]  # Only 1 claim supported
            papers = [{"paper_id": "p1", "title": "Paper 1", "authors": ["A"], "year": 2024}]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")
            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")
            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")

            report = generate_report(run_dir, "Test query")
            assert "CAUTION" in report or "根拠支持率" in report

    def test_high_support_rate(self):
        """Covers line 250 (False branch - support_rate >= 0.90)."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            claims = [{"claim_id": "c1", "claim_text": "Claim 1"}]
            evidence = [{"evidence_id": "e1", "claim_id": "c1", "evidence_strength": "Strong"}]
            papers = [{"paper_id": "p1", "title": "Paper 1", "authors": ["A"], "year": 2024}]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")
            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")
            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")

            report = generate_report(run_dir, "Test query")
            assert "CAUTION" not in report

    def test_claim_types_general_and_specific(self):
        """Covers lines 274-291 (claim type grouping)."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            claims = [
                {"claim_id": "c1", "claim_text": "Claim 1", "claim_type": "Efficacy"},
                {"claim_id": "c2", "claim_text": "Claim 2", "claim_type": "Safety"},
                {"claim_id": "c3", "claim_text": "Claim 3"},  # No claim_type = General
            ]
            evidence = [
                {"evidence_id": "e1", "claim_id": "c1", "evidence_strength": "Strong"},
                {"evidence_id": "e2", "claim_id": "c2", "evidence_strength": "Medium"},
                {"evidence_id": "e3", "claim_id": "c3", "evidence_strength": "Weak"},
            ]
            papers = [{"paper_id": "p1", "title": "Paper 1", "authors": ["A"], "year": 2024}]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")
            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")
            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")

            report = generate_report(run_dir, "Test query")
            assert "Efficacy" in report
            assert "Safety" in report

    def test_many_authors(self):
        """Covers lines 314-315 (more than 3 authors)."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            claims = [{"claim_id": "c1", "claim_text": "Claim 1"}]
            evidence = [{"evidence_id": "e1", "claim_id": "c1", "evidence_strength": "Strong"}]
            papers = [
                {
                    "paper_id": "p1",
                    "title": "Paper 1",
                    "authors": ["A", "B", "C", "D", "E"],
                    "year": 2024,
                }
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

            report = generate_report(run_dir, "Test query")
            assert "et al." in report

    def test_few_authors(self):
        """Covers line 313 (3 or fewer authors)."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            claims = [{"claim_id": "c1", "claim_text": "Claim 1"}]
            evidence = [{"evidence_id": "e1", "claim_id": "c1", "evidence_strength": "Strong"}]
            papers = [{"paper_id": "p1", "title": "Paper 1", "authors": ["A", "B"], "year": 2024}]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")
            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")
            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")

            report = generate_report(run_dir, "Test query")
            assert "et al." not in report

    def test_no_authors(self):
        """Covers line 313 (empty authors)."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            claims = [{"claim_id": "c1", "claim_text": "Claim 1"}]
            evidence = [{"evidence_id": "e1", "claim_id": "c1", "evidence_strength": "Strong"}]
            papers = [{"paper_id": "p1", "title": "Paper 1", "authors": [], "year": 2024}]

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")
            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")
            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")

            report = generate_report(run_dir, "Test query")
            assert "Unknown" in report

    def test_validation_errors(self):
        """Covers lines 224-225 (validation errors logging)."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            # Create claims that might cause validation errors
            claims = [{"claim_id": "c1", "claim_text": ""}]  # Empty claim text

            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")
            with open(run_dir / "evidence.jsonl", "w") as f:
                pass
            with open(run_dir / "papers.jsonl", "w") as f:
                pass

            report = generate_report(run_dir, "Test query")
            assert report is not None

    def test_more_than_10_papers(self):
        """Covers line 307 (papers[:10])."""
        from jarvis_core.stages.generate_report import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)

            claims = [{"claim_id": "c1", "claim_text": "Claim 1"}]
            evidence = [{"evidence_id": "e1", "claim_id": "c1", "evidence_strength": "Strong"}]
            papers = [
                {"paper_id": f"p{i}", "title": f"Paper {i}", "authors": ["A"], "year": 2024}
                for i in range(15)
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

            report = generate_report(run_dir, "Test query")
            # Should only show 10 papers in references
            assert "p9" in report
            assert "p10" not in report  # 11th paper not shown

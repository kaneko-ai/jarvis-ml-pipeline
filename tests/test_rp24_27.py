"""Tests for RP24-RP27 features.

Per requirements:
- RP24: Multi-Query Review Mode
- RP25: Podcast Script Generator
- RP26: Research Log / Diff
- RP27: Collaborative Review (ReviewNote)
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.claim import Claim, ClaimSet, ReviewNote
from jarvis_core.review_mode import ReviewResult, export_review_bundle, _generate_review_index
from jarvis_core.audio_script import export_podcast_script
from jarvis_core.logging.run_log import save_run, load_run, diff_runs
from jarvis_core.result import EvidenceQAResult


class TestReviewNote:
    """Tests for ReviewNote (RP27)."""

    def test_create_review_note(self):
        """Should create review note."""
        note = ReviewNote(
            author="Dr. Smith",
            note_type="comment",
            text="This needs clarification",
        )
        assert note.author == "Dr. Smith"
        assert note.note_type == "comment"

    def test_claim_add_review(self):
        """Should add review to claim."""
        claim = Claim.create("Test claim.", [])
        note = claim.add_review(
            author="Dr. Jones",
            text="Needs more evidence",
            note_type="challenge",
        )

        assert len(claim.reviews) == 1
        assert note.note_type == "challenge"

    def test_claim_to_dict_includes_reviews(self):
        """Claim.to_dict should include reviews."""
        claim = Claim.create("Test.", [])
        claim.add_review("Author", "Note text")

        d = claim.to_dict()

        assert "reviews" in d
        assert len(d["reviews"]) == 1

    def test_claim_from_dict_restores_reviews(self):
        """Claim.from_dict should restore reviews."""
        data = {
            "text": "Test claim",
            "reviews": [
                {
                    "author": "Dr. A",
                    "note_type": "todo",
                    "text": "Follow up",
                    "created_at": datetime.now().isoformat(),
                }
            ],
        }

        claim = Claim.from_dict(data)

        assert len(claim.reviews) == 1
        assert claim.reviews[0].note_type == "todo"


class TestReviewMode:
    """Tests for Multi-Query Review Mode (RP24)."""

    def test_review_result_dataclass(self):
        """Should create ReviewResult."""
        result = ReviewResult(
            queries=["Q1", "Q2"],
            results=[],
            inputs=["input.pdf"],
        )
        assert len(result.queries) == 2

    def test_generate_review_index(self):
        """Should generate review index markdown."""
        mock_result = EvidenceQAResult(
            answer="Answer 1",
            status="success",
            citations=[],
            inputs=[],
            query="Query 1",
        )

        review = ReviewResult(
            queries=["Query 1"],
            results=[mock_result],
            inputs=["test.pdf"],
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        index = _generate_review_index(review)

        assert "Query 1" in index
        assert "Research Review" in index


class TestPodcastScript:
    """Tests for Podcast Script Generator (RP25)."""

    def test_export_podcast_script(self):
        """Should generate podcast script."""
        cs = ClaimSet()
        cs.add_new("CD73 is an enzyme.", [])

        result = EvidenceQAResult(
            answer="CD73 is important.",
            status="success",
            citations=[],
            inputs=[],
            query="What is CD73?",
            claims=cs,
        )

        script = export_podcast_script(result)

        assert "PODCAST SCRIPT" in script
        assert "What is CD73?" in script
        assert "SECTION 1" in script

    def test_script_has_all_sections(self):
        """Script should have all required sections."""
        result = EvidenceQAResult(
            answer="Test",
            status="success",
            citations=[],
            inputs=[],
            query="Test query",
        )

        script = export_podcast_script(result)

        assert "HOOK" in script
        assert "ANSWER" in script
        assert "EVIDENCE" in script
        assert "CONCLUSION" in script


class TestRunLog:
    """Tests for Research Log (RP26)."""

    def test_save_and_load_run(self):
        """Should save and load run."""
        cs = ClaimSet()
        cs.add_new("Test claim.", ["chunk_1"])

        result = EvidenceQAResult(
            answer="Test answer",
            status="success",
            citations=[],
            inputs=[],
            query="Test query",
            claims=cs,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = save_run(result, tmpdir)

            loaded = load_run(run_dir)

            assert loaded["query"] == "Test query"
            assert len(loaded["claims"]) == 1

    def test_diff_runs(self):
        """Should generate diff between runs."""
        cs1 = ClaimSet()
        cs1.add_new("Claim A.", [])

        cs2 = ClaimSet()
        cs2.add_new("Claim A.", [])
        cs2.add_new("Claim B (new).", [])

        result1 = EvidenceQAResult(
            answer="Answer 1",
            status="success",
            citations=[],
            inputs=[],
            query="Query",
            claims=cs1,
        )

        result2 = EvidenceQAResult(
            answer="Answer 2 modified",
            status="success",
            citations=[],
            inputs=[],
            query="Query",
            claims=cs2,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dir1 = save_run(result1, tmpdir)
            dir2 = save_run(result2, tmpdir)

            diff = diff_runs(dir1, dir2)

            assert "Run Comparison" in diff
            assert "Claims Comparison" in diff

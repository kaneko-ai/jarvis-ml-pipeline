"""Tests for Claim-Level Citation (RP13).

Per RP13, these tests verify:
- Claim structure creation
- Claim parsing from agent response
- ClaimSet operations
"""

from jarvis_core.claim import Claim, ClaimSet
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class TestClaim:
    """Tests for Claim dataclass."""

    def test_create_claim(self):
        """Should create claim with text and citations."""
        claim = Claim.create(
            text="CD73 is an ectoenzyme.",
            citations=["chunk_abc123"],
        )
        assert claim.text == "CD73 is an ectoenzyme."
        assert claim.citations == ["chunk_abc123"]
        assert claim.valid is True
        assert claim.id.startswith("claim_")

    def test_claim_to_dict(self):
        """Should convert claim to dict."""
        claim = Claim.create("Test claim", ["c1", "c2"])
        d = claim.to_dict()

        assert d["text"] == "Test claim"
        assert d["citations"] == ["c1", "c2"]
        assert d["valid"] is True

    def test_claim_from_dict(self):
        """Should create claim from dict."""
        data = {
            "id": "claim_test",
            "text": "A claim",
            "citations": ["c1"],
            "valid": False,
            "validation_notes": ["missing evidence"],
        }
        claim = Claim.from_dict(data)

        assert claim.id == "claim_test"
        assert claim.text == "A claim"
        assert claim.valid is False


class TestClaimSet:
    """Tests for ClaimSet."""

    def test_add_claim(self):
        """Should add claims to set."""
        cs = ClaimSet()
        cs.add_new("Claim 1", ["c1"])
        cs.add_new("Claim 2", ["c2"])

        assert len(cs) == 2

    def test_get_valid_claims(self):
        """Should filter valid claims."""
        cs = ClaimSet()
        c1 = cs.add_new("Valid claim", ["c1"])
        c2 = cs.add_new("Invalid claim", [])
        c2.valid = False

        valid = cs.get_valid_claims()
        assert len(valid) == 1
        assert valid[0].text == "Valid claim"

    def test_get_all_citations(self):
        """Should collect all unique chunk_ids."""
        cs = ClaimSet()
        cs.add_new("Claim 1", ["c1", "c2"])
        cs.add_new("Claim 2", ["c2", "c3"])

        all_ids = cs.get_all_citations()
        assert set(all_ids) == {"c1", "c2", "c3"}

    def test_generate_answer(self):
        """Should generate answer from valid claims."""
        cs = ClaimSet()
        c1 = cs.add_new("First claim.", ["c1"])
        c2 = cs.add_new("Second claim.", ["c2"])
        c3 = cs.add_new("Invalid claim.", [])
        c3.valid = False

        answer = cs.generate_answer(include_invalid=False)
        assert "First claim." in answer
        assert "Second claim." in answer
        assert "Invalid claim." not in answer

    def test_generate_answer_with_invalid(self):
        """Should include invalid claims with marker."""
        cs = ClaimSet()
        c1 = cs.add_new("Valid.", ["c1"])
        c2 = cs.add_new("Invalid.", [])
        c2.valid = False

        answer = cs.generate_answer(include_invalid=True)
        assert "[Unverified] Invalid." in answer

    def test_has_any_valid(self):
        """Should check if any claim is valid."""
        cs = ClaimSet()
        c1 = cs.add_new("Claim", [])
        c1.valid = False

        assert cs.has_any_valid() is False

        c1.valid = True
        assert cs.has_any_valid() is True

    def test_all_valid(self):
        """Should check if all claims are valid."""
        cs = ClaimSet()
        cs.add_new("Claim 1", ["c1"])
        cs.add_new("Claim 2", ["c2"])

        assert cs.all_valid() is True

        cs.claims[0].valid = False
        assert cs.all_valid() is False

    def test_to_dict_from_dict(self):
        """Should serialize and deserialize."""
        cs = ClaimSet()
        cs.add_new("Claim 1", ["c1"])
        cs.add_new("Claim 2", ["c2"])

        d = cs.to_dict()
        cs2 = ClaimSet.from_dict(d)

        assert len(cs2) == 2
        assert cs2.claims[0].text == "Claim 1"

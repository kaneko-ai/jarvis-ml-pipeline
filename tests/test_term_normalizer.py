"""Tests for style.term_normalizer module."""

from jarvis_core.style.term_normalizer import (
    TermIssue,
    NormalizationResult,
    _apply_variants,
    normalize_lines,
    check_abbrev_rules,
    normalize_markdown,
    normalize_docx_paragraphs,
    normalize_pptx_slides,
)


class TestTermIssue:
    def test_creation(self):
        issue = TermIssue(
            issue_type="term_variant",
            location="md:5",
            original="color",
            suggested="colour",
            rule_id="spelling",
            severity="WARN",
        )
        assert issue.issue_type == "term_variant"
        assert issue.severity == "WARN"


class TestNormalizationResult:
    def test_creation(self):
        result = NormalizationResult(
            normalized_lines=["line1", "line2"],
            issues=[],
            replacements=[],
        )
        assert len(result.normalized_lines) == 2


class TestApplyVariants:
    def test_replace_variant(self):
        line = "The color of the sample was red."
        variants = ["color"]
        preferred = "colour"

        new_line, issues, replacements = _apply_variants(
            line, variants, preferred, "test_rule", "test:1", "term_variant", "WARN"
        )

        assert "colour" in new_line
        assert len(issues) == 1
        assert issues[0].original == "color"

    def test_no_replacement_when_already_preferred(self):
        line = "The colour of the sample."
        variants = ["color"]
        preferred = "colour"

        new_line, issues, _ = _apply_variants(
            line, variants, preferred, "test_rule", "test:1", "term_variant", "WARN"
        )

        assert new_line == line
        assert len(issues) == 0


class TestNormalizeLines:
    def test_normalize_with_style_guide(self):
        lines = ["The drug was effective.", "Treatment worked well."]
        style_guide = {
            "preferred_terms": [],
            "forbidden_terms": [],
            "units_and_notation": {},
        }

        result = normalize_lines(lines, style_guide, "test")

        assert isinstance(result, NormalizationResult)
        assert len(result.normalized_lines) == 2

    def test_normalize_with_preferred_terms(self):
        lines = ["We observed a color change."]
        style_guide = {
            "preferred_terms": [{"id": "spelling", "variants": ["color"], "preferred": "colour"}],
            "forbidden_terms": [],
            "units_and_notation": {},
        }

        result = normalize_lines(lines, style_guide, "test")

        assert "colour" in result.normalized_lines[0]
        assert len(result.issues) == 1


class TestCheckAbbrevRules:
    def test_abbrev_without_definition(self):
        text = "The FDA approved the drug."
        style_guide = {
            "abbrev_rules": [
                {
                    "id": "fda",
                    "abbreviation": "FDA",
                    "full_form": "Food and Drug Administration",
                    "first_use_format": "Food and Drug Administration (FDA)",
                }
            ]
        }

        issues = check_abbrev_rules(text, style_guide, "test")

        assert len(issues) == 1
        assert issues[0].issue_type == "abbrev_missing"

    def test_abbrev_with_definition(self):
        text = "Food and Drug Administration (FDA) regulates drugs. The FDA approved it."
        style_guide = {
            "abbrev_rules": [
                {
                    "id": "fda",
                    "abbreviation": "FDA",
                    "full_form": "Food and Drug Administration",
                }
            ]
        }

        issues = check_abbrev_rules(text, style_guide, "test")

        # Definition appears before first use
        assert len(issues) == 0


class TestNormalizeMarkdown:
    def test_normalize_markdown_basic(self):
        text = "# Header\nContent here."
        style_guide = {
            "preferred_terms": [],
            "forbidden_terms": [],
            "units_and_notation": {},
            "abbrev_rules": [],
        }

        normalized, issues, replacements = normalize_markdown(text, style_guide)

        assert "# Header" in normalized


class TestNormalizeDocxParagraphs:
    def test_normalize_docx(self):
        paragraphs = ["Paragraph 1", "Paragraph 2"]
        style_guide = {
            "preferred_terms": [],
            "forbidden_terms": [],
            "units_and_notation": {},
        }

        result = normalize_docx_paragraphs(paragraphs, style_guide)

        assert len(result.normalized_lines) == 2


class TestNormalizePptxSlides:
    def test_normalize_pptx(self):
        slides = ["Slide 1 content", "Slide 2 content"]
        style_guide = {
            "preferred_terms": [],
            "forbidden_terms": [],
            "units_and_notation": {},
        }

        result = normalize_pptx_slides(slides, style_guide)

        assert len(result.normalized_lines) == 2

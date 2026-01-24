"""Tests for submission.email_generator module."""

import pytest
from jarvis_core.submission.email_generator import (
    EmailDraft,
    generate_email_draft,
    _load_templates,
)


class TestEmailDraft:
    def test_creation(self):
        draft = EmailDraft(
            subject="Test Subject",
            body="Test body content",
            recipient_type="professor",
        )
        assert draft.subject == "Test Subject"
        assert draft.body == "Test body content"
        assert draft.recipient_type == "professor"


class TestLoadTemplates:
    def test_load_from_yaml(self, tmp_path):
        template_file = tmp_path / "templates.yaml"
        template_file.write_text(
            """
professor:
  subject: "{title} submit"
  body: Please check
  salutation: Dear Sir
""",
            encoding="utf-8",
        )
        templates = _load_templates(template_file)

        assert "professor" in templates
        assert templates["professor"]["subject"] == "{title} submit"


class TestGenerateEmailDraft:
    @pytest.fixture
    def template_file(self, tmp_path):
        file = tmp_path / "templates.yaml"
        file.write_text(
            """
professor:
  subject: "{title} submit ver{version}"
  body: |
    Submitting revised version of {title}.
    
    Attachments:
    {attachments_list}
  salutation: Dear Professor
lab:
  subject: "[Share] {title}"
  body: Please review
""",
            encoding="utf-8",
        )
        return file

    def test_generate_for_professor(self, template_file):
        context = {"title": "ResearchPlan", "version": "1.0"}
        attachments = ["document.docx", "slides.pptx"]

        draft = generate_email_draft(
            templates_path=template_file,
            recipient_type="professor",
            context=context,
            attachments=attachments,
        )

        assert "ResearchPlan submit ver1.0" in draft.subject
        assert "document.docx" in draft.body
        assert draft.recipient_type == "professor"

    def test_generate_for_lab(self, template_file):
        context = {"title": "ProgressReport"}

        draft = generate_email_draft(
            templates_path=template_file,
            recipient_type="lab",
            context=context,
            attachments=[],
        )

        assert "[Share]" in draft.subject
        assert draft.recipient_type == "lab"

    def test_unknown_recipient_type(self, template_file):
        with pytest.raises(ValueError, match="unknown recipient_type"):
            generate_email_draft(
                templates_path=template_file,
                recipient_type="unknown",
                context={},
                attachments=[],
            )

    def test_empty_attachments(self, template_file):
        context = {"title": "Test", "version": "1"}

        draft = generate_email_draft(
            templates_path=template_file,
            recipient_type="professor",
            context=context,
            attachments=[],
        )

        # Empty attachments show "- None" as placeholder
        assert draft.body is not None

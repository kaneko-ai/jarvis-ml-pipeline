from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class EmailDraft:
    subject: str
    body: str
    recipient_type: str


def generate_email_draft(
    templates_path: Path,
    recipient_type: str,
    context: dict[str, str],
    attachments: list[str],
) -> EmailDraft:
    templates = _load_templates(templates_path)
    if recipient_type not in templates:
        raise ValueError(f"unknown recipient_type: {recipient_type}")

    template = templates[recipient_type]
    attachments_list = "\n".join([f"- {item}" for item in attachments]) if attachments else "- なし"
    payload = {
        **context,
        "attachments_list": attachments_list,
    }

    subject = template["subject"].format(**payload)
    body = template["body"].format(**payload)
    body = f"{template.get('salutation', '')}\n\n{body}".strip() + "\n"

    return EmailDraft(subject=subject, body=body, recipient_type=recipient_type)


def _load_templates(path: Path) -> dict[str, dict[str, str]]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data

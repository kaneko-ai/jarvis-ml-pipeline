from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml


@dataclass
class EmailDraft:
    subject: str
    body: str
    recipient_type: str


def generate_email_draft(
    templates_path: Path,
    recipient_type: str,
    context: Dict[str, str],
    attachments: List[str],
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


def _load_templates(path: Path) -> Dict[str, Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data

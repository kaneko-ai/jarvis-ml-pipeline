"""Package builder for finance/optimization reports."""
from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def build_finance_package(
    report_md: str,
    report_html: str,
    data: dict[str, Any],
    output_path: Path | None = None,
) -> Path:
    """Build a zip package with finance reports and raw data."""
    if output_path is None:
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        output_path = Path(temp.name)
        temp.close()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("finance_report.md", report_md)
        archive.writestr("finance_report.html", report_html)
        archive.writestr("finance_data.json", json.dumps(data, ensure_ascii=False, indent=2))

    return output_path

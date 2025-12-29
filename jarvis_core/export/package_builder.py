"""Package builder for finance/optimization reports."""
from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

from jarvis_core.optimization.report import build_report
from jarvis_core.optimization.solver import OptimizationResult


def build_finance_package(results: Iterable[OptimizationResult], format: str = "md") -> Path:
    """Build a zip package containing the finance report."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        report_text = build_report(results, format=format)
        report_name = f"finance_report.{format}"
        report_path = temp_path / report_name
        report_path.write_text(report_text, encoding="utf-8")

        json_path = temp_path / "finance_report.json"
        json_path.write_text(
            json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        zip_path = temp_path / "finance_report.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(report_path, report_name)
            zip_file.write(json_path, "finance_report.json")

        output_path = Path(tempfile.gettempdir()) / "finance_report.zip"
        output_path.write_bytes(zip_path.read_bytes())
        return output_path

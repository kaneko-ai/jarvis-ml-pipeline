"""PRISMA Flow Generator.

Generates PRISMA 2020 flow diagrams.
"""

from __future__ import annotations

import logging
from pathlib import Path

from jarvis_core.experimental.prisma.schema import PRISMAData

logger = logging.getLogger(__name__)


# Mermaid template for PRISMA flow
MERMAID_TEMPLATE = """flowchart TD
    subgraph Identification
        A[Records from databases<br>n = {db_records}] --> D[Records after duplicates removed<br>n = {after_dup}]
        B[Records from registers<br>n = {reg_records}] --> D
        C[Records from other sources<br>n = {other_records}] --> D
    end

    subgraph Screening
        D --> E[Records screened<br>n = {screened}]
        E --> F[Records excluded<br>n = {screen_excluded}]
        E --> G[Reports sought<br>n = {sought}]
    end

    subgraph Eligibility
        G --> H[Reports not retrieved<br>n = {not_retrieved}]
        G --> I[Reports assessed<br>n = {assessed}]
        I --> J[Reports excluded<br>n = {elig_excluded}]
        I --> K[Studies included<br>n = {included}]
    end

    subgraph Included
        K --> L[Final included studies<br>n = {included}<br>Reports: n = {reports}]
    end
"""

# SVG template for PRISMA flow (simplified)
SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <style>
    .box {{ fill: #fff; stroke: #333; stroke-width: 2; }}
    .text {{ font-family: Arial; font-size: 12px; text-anchor: middle; }}
    .header {{ font-family: Arial; font-size: 14px; font-weight: bold; text-anchor: middle; }}
    .arrow {{ stroke: #333; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }}
  </style>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>
    </marker>
  </defs>

  <!-- Identification -->
  <rect x="50" y="30" width="200" height="60" rx="5" class="box"/>
  <text x="150" y="55" class="header">Identification</text>
  <text x="150" y="75" class="text">Records: {total_records}</text>

  <!-- Duplicates -->
  <rect x="300" y="30" width="180" height="60" rx="5" class="box"/>
  <text x="390" y="55" class="header">Duplicates removed</text>
  <text x="390" y="75" class="text">n = {duplicates}</text>

  <!-- Screening -->
  <rect x="50" y="130" width="200" height="60" rx="5" class="box"/>
  <text x="150" y="155" class="header">Screening</text>
  <text x="150" y="175" class="text">Records: {screened}</text>

  <!-- Excluded screening -->
  <rect x="300" y="130" width="180" height="60" rx="5" class="box"/>
  <text x="390" y="155" class="header">Excluded</text>
  <text x="390" y="175" class="text">n = {excluded_screening}</text>

  <!-- Eligibility -->
  <rect x="50" y="230" width="200" height="60" rx="5" class="box"/>
  <text x="150" y="255" class="header">Eligibility</text>
  <text x="150" y="275" class="text">Reports: {assessed}</text>

  <!-- Excluded eligibility -->
  <rect x="300" y="230" width="180" height="60" rx="5" class="box"/>
  <text x="390" y="255" class="header">Excluded</text>
  <text x="390" y="275" class="text">n = {excluded_eligibility}</text>

  <!-- Included -->
  <rect x="50" y="330" width="200" height="60" rx="5" class="box" style="fill: #e8f5e9;"/>
  <text x="150" y="355" class="header">Included</text>
  <text x="150" y="375" class="text">Studies: {included}</text>

  <!-- Arrows -->
  <path d="M 150 90 L 150 130" class="arrow"/>
  <path d="M 250 60 L 300 60" class="arrow"/>
  <path d="M 150 190 L 150 230" class="arrow"/>
  <path d="M 250 160 L 300 160" class="arrow"/>
  <path d="M 150 290 L 150 330" class="arrow"/>
  <path d="M 250 260 L 300 260" class="arrow"/>
</svg>
"""


class PRISMAGenerator:
    """Generates PRISMA 2020 flow diagrams.

    Supports multiple output formats:
    - Mermaid (for markdown/web)
    - SVG (for embedding/printing)
    - Text (for accessibility)

    Example:
        >>> generator = PRISMAGenerator()
        >>> data = PRISMAData(records_from_databases=1000, ...)
        >>> mermaid_code = generator.to_mermaid(data)
    """

    def to_mermaid(self, data: PRISMAData) -> str:
        """Generate Mermaid flowchart code.

        Args:
            data: PRISMA flow data

        Returns:
            Mermaid diagram code
        """
        data.calculate_totals()

        after_dup = (
            data.records_from_databases
            + data.records_from_registers
            + data.records_from_other_sources
            - data.duplicates_removed
        )

        return MERMAID_TEMPLATE.format(
            db_records=data.records_from_databases,
            reg_records=data.records_from_registers,
            other_records=data.records_from_other_sources,
            after_dup=after_dup,
            screened=data.records_screened,
            screen_excluded=data.records_excluded_screening,
            sought=data.reports_sought,
            not_retrieved=data.reports_not_retrieved,
            assessed=data.reports_assessed,
            elig_excluded=data.reports_excluded,
            included=data.studies_included,
            reports=data.reports_included,
        )

    def to_svg(self, data: PRISMAData) -> str:
        """Generate SVG diagram.

        Args:
            data: PRISMA flow data

        Returns:
            SVG code
        """
        data.calculate_totals()

        total_records = (
            data.records_from_databases
            + data.records_from_registers
            + data.records_from_other_sources
        )

        return SVG_TEMPLATE.format(
            total_records=total_records,
            duplicates=data.duplicates_removed,
            screened=data.records_screened,
            excluded_screening=data.records_excluded_screening,
            assessed=data.reports_assessed,
            excluded_eligibility=data.reports_excluded,
            included=data.studies_included,
        )

    def to_text(self, data: PRISMAData) -> str:
        """Generate text representation.

        Args:
            data: PRISMA flow data

        Returns:
            Text summary
        """
        data.calculate_totals()

        lines = [
            "PRISMA 2020 Flow Diagram",
            "=" * 40,
            "",
            "IDENTIFICATION",
            f"  Records from databases: {data.records_from_databases}",
            f"  Records from registers: {data.records_from_registers}",
            f"  Records from other sources: {data.records_from_other_sources}",
            f"  Duplicates removed: {data.duplicates_removed}",
            "",
            "SCREENING",
            f"  Records screened: {data.records_screened}",
            f"  Records excluded: {data.records_excluded_screening}",
            "",
            "ELIGIBILITY",
            f"  Reports sought: {data.reports_sought}",
            f"  Reports not retrieved: {data.reports_not_retrieved}",
            f"  Reports assessed: {data.reports_assessed}",
            f"  Reports excluded: {data.reports_excluded}",
            "",
            "INCLUDED",
            f"  Studies included: {data.studies_included}",
            f"  Reports included: {data.reports_included}",
        ]

        if data.exclusion_reasons:
            lines.extend(["", "EXCLUSION REASONS"])
            for reason in data.exclusion_reasons:
                lines.append(f"  {reason.reason}: {reason.count}")

        return "\n".join(lines)

    def save(
        self,
        data: PRISMAData,
        output_path: Path,
        format: str = "svg",
    ) -> None:
        """Save PRISMA diagram to file.

        Args:
            data: PRISMA flow data
            output_path: Output file path
            format: Output format (svg, mermaid, txt)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "svg":
            content = self.to_svg(data)
        elif format == "mermaid":
            content = self.to_mermaid(data)
        else:
            content = self.to_text(data)

        output_path.write_text(content, encoding="utf-8")
        logger.info(f"PRISMA diagram saved to: {output_path}")


def generate_prisma_flow(
    data: PRISMAData,
    format: str = "mermaid",
) -> str:
    """Generate PRISMA flow diagram.

    Convenience function for quick generation.

    Args:
        data: PRISMA flow data
        format: Output format (mermaid, svg, text)

    Returns:
        Diagram code/content
    """
    generator = PRISMAGenerator()

    if format == "svg":
        return generator.to_svg(data)
    elif format == "text":
        return generator.to_text(data)
    else:
        return generator.to_mermaid(data)
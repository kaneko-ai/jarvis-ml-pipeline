"""RIS/BibTeX Import/Export Integration.

Per JARVIS_COMPLETION_PLAN_v3 Sprint 20: 外部連携
Provides import/export functionality for common reference formats.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Reference:
    """A bibliographic reference."""

    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    keywords: list[str] = field(default_factory=list)
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "pmid": self.pmid,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "url": self.url,
        }


class RISParser:
    """Parse RIS format files."""

    TAG_MAP = {
        "TY": "type",
        "TI": "title",
        "T1": "title",
        "AU": "author",
        "A1": "author",
        "PY": "year",
        "Y1": "year",
        "JO": "journal",
        "JF": "journal",
        "VL": "volume",
        "IS": "issue",
        "SP": "start_page",
        "EP": "end_page",
        "DO": "doi",
        "AB": "abstract",
        "KW": "keyword",
        "UR": "url",
        "AN": "pmid",
    }

    def parse(self, content: str) -> list[Reference]:
        """Parse RIS content.

        Args:
            content: RIS file content

        Returns:
            List of Reference objects
        """
        references = []
        current = {}

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.match(r"^([A-Z0-9]{2})\s+-\s+(.*)$", line)
            if match:
                tag, value = match.groups()
                field_name = self.TAG_MAP.get(tag)

                if tag == "ER":  # End of record
                    if current:
                        ref = self._build_reference(current, len(references) + 1)
                        references.append(ref)
                        current = {}
                elif field_name == "author":
                    current.setdefault("authors", []).append(value)
                elif field_name == "keyword":
                    current.setdefault("keywords", []).append(value)
                elif field_name:
                    current[field_name] = value

        # Handle last record if no ER tag
        if current:
            ref = self._build_reference(current, len(references) + 1)
            references.append(ref)

        return references

    def _build_reference(self, data: dict, index: int) -> Reference:
        """Build Reference from parsed data."""
        pages = ""
        if data.get("start_page"):
            pages = data["start_page"]
            if data.get("end_page"):
                pages += f"-{data['end_page']}"

        year = None
        if data.get("year"):
            try:
                year = int(data["year"][:4])
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse year '{data.get('year')}': {e}")

        return Reference(
            id=f"ris_{index}",
            title=data.get("title", ""),
            authors=data.get("authors", []),
            year=year,
            journal=data.get("journal", ""),
            volume=data.get("volume", ""),
            issue=data.get("issue", ""),
            pages=pages,
            doi=data.get("doi", ""),
            pmid=data.get("pmid", ""),
            abstract=data.get("abstract", ""),
            keywords=data.get("keywords", []),
            url=data.get("url", ""),
        )


class BibTeXParser:
    """Parse BibTeX format files."""

    def parse(self, content: str) -> list[Reference]:
        """Parse BibTeX content.

        Args:
            content: BibTeX file content

        Returns:
            List of Reference objects
        """
        references = []

        # Simple regex-based parsing
        pattern = r"@(\w+)\s*\{\s*([^,]+)\s*,([^@]*)\}"

        for match in re.finditer(pattern, content, re.DOTALL):
            entry_type, cite_key, fields_str = match.groups()
            fields = self._parse_fields(fields_str)

            ref = self._build_reference(cite_key.strip(), fields)
            references.append(ref)

        return references

    def _parse_fields(self, fields_str: str) -> dict[str, str]:
        """Parse BibTeX fields."""
        fields = {}

        # Match field = {value} or field = "value"
        pattern = r'(\w+)\s*=\s*[\{"]([^}"]*)[\}"]'

        for match in re.finditer(pattern, fields_str):
            key, value = match.groups()
            fields[key.lower()] = value.strip()

        return fields

    def _build_reference(self, cite_key: str, fields: dict) -> Reference:
        """Build Reference from parsed fields."""
        authors = []
        if fields.get("author"):
            # Split on " and "
            authors = [a.strip() for a in fields["author"].split(" and ")]

        year = None
        if fields.get("year"):
            try:
                year = int(fields["year"])
            except ValueError as e:
                logger.debug(f"Failed to parse year '{fields.get('year')}': {e}")

        keywords = []
        if fields.get("keywords"):
            keywords = [k.strip() for k in fields["keywords"].split(",")]

        return Reference(
            id=cite_key,
            title=fields.get("title", ""),
            authors=authors,
            year=year,
            journal=fields.get("journal", ""),
            volume=fields.get("volume", ""),
            issue=fields.get("number", ""),
            pages=fields.get("pages", ""),
            doi=fields.get("doi", ""),
            pmid=fields.get("pmid", ""),
            abstract=fields.get("abstract", ""),
            keywords=keywords,
            url=fields.get("url", ""),
        )


class RISExporter:
    """Export to RIS format."""

    def export(self, references: list[Reference]) -> str:
        """Export references to RIS format.

        Args:
            references: List of Reference objects

        Returns:
            RIS formatted string
        """
        lines = []

        for ref in references:
            lines.append("TY  - JOUR")
            lines.append(f"TI  - {ref.title}")

            for author in ref.authors:
                lines.append(f"AU  - {author}")

            if ref.year:
                lines.append(f"PY  - {ref.year}")
            if ref.journal:
                lines.append(f"JO  - {ref.journal}")
            if ref.volume:
                lines.append(f"VL  - {ref.volume}")
            if ref.issue:
                lines.append(f"IS  - {ref.issue}")
            if ref.pages:
                if "-" in ref.pages:
                    sp, ep = ref.pages.split("-", 1)
                    lines.append(f"SP  - {sp}")
                    lines.append(f"EP  - {ep}")
                else:
                    lines.append(f"SP  - {ref.pages}")
            if ref.doi:
                lines.append(f"DO  - {ref.doi}")
            if ref.pmid:
                lines.append(f"AN  - {ref.pmid}")
            if ref.abstract:
                lines.append(f"AB  - {ref.abstract}")
            for kw in ref.keywords:
                lines.append(f"KW  - {kw}")
            if ref.url:
                lines.append(f"UR  - {ref.url}")

            lines.append("ER  - ")
            lines.append("")

        return "\n".join(lines)


class BibTeXExporter:
    """Export to BibTeX format."""

    def export(self, references: list[Reference]) -> str:
        """Export references to BibTeX format.

        Args:
            references: List of Reference objects

        Returns:
            BibTeX formatted string
        """
        entries = []

        for ref in references:
            cite_key = self._generate_cite_key(ref)

            lines = [f"@article{{{cite_key},"]
            lines.append(f"  title = {{{ref.title}}},")

            if ref.authors:
                authors_str = " and ".join(ref.authors)
                lines.append(f"  author = {{{authors_str}}},")

            if ref.year:
                lines.append(f"  year = {{{ref.year}}},")
            if ref.journal:
                lines.append(f"  journal = {{{ref.journal}}},")
            if ref.volume:
                lines.append(f"  volume = {{{ref.volume}}},")
            if ref.issue:
                lines.append(f"  number = {{{ref.issue}}},")
            if ref.pages:
                lines.append(f"  pages = {{{ref.pages}}},")
            if ref.doi:
                lines.append(f"  doi = {{{ref.doi}}},")
            if ref.abstract:
                # Escape special characters
                abstract = ref.abstract.replace("{", "\\{").replace("}", "\\}")
                lines.append(f"  abstract = {{{abstract}}},")
            if ref.url:
                lines.append(f"  url = {{{ref.url}}},")

            lines.append("}")
            entries.append("\n".join(lines))

        return "\n\n".join(entries)

    def _generate_cite_key(self, ref: Reference) -> str:
        """Generate a citation key."""
        author_part = ""
        if ref.authors:
            # Use first author's last name
            first_author = ref.authors[0]
            if "," in first_author:
                author_part = first_author.split(",")[0]
            else:
                author_part = first_author.split()[-1]
            author_part = re.sub(r"[^a-zA-Z]", "", author_part).lower()

        year_part = str(ref.year) if ref.year else ""

        return f"{author_part}{year_part}" or ref.id


def import_references(
    input_path: Path,
    format: str,
) -> list[Reference]:
    """Import references from file.

    Args:
        input_path: Path to input file
        format: Format (ris, bibtex)

    Returns:
        List of Reference objects
    """
    content = input_path.read_text(encoding="utf-8")

    if format == "ris":
        parser = RISParser()
    elif format == "bibtex":
        parser = BibTeXParser()
    else:
        raise ValueError(f"Unsupported import format: {format}")

    return parser.parse(content)


def export_references(
    references: list[Reference],
    output_path: Path,
    format: str,
) -> None:
    """Export references to file.

    Args:
        references: List of Reference objects
        output_path: Path to output file
        format: Format (ris, bibtex)
    """
    if format == "ris":
        exporter = RISExporter()
    elif format == "bibtex":
        exporter = BibTeXExporter()
    else:
        raise ValueError(f"Unsupported export format: {format}")

    content = exporter.export(references)
    output_path.write_text(content, encoding="utf-8")


def references_to_jsonl(references: list[Reference], output_path: Path) -> None:
    """Save references as JSONL.

    Args:
        references: List of Reference objects
        output_path: Path to output JSONL file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for ref in references:
            f.write(json.dumps(ref.to_dict(), ensure_ascii=False) + "\n")


def jsonl_to_references(input_path: Path) -> list[Reference]:
    """Load references from JSONL.

    Args:
        input_path: Path to input JSONL file

    Returns:
        List of Reference objects
    """
    references = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                ref = Reference(
                    id=data.get("id", ""),
                    title=data.get("title", ""),
                    authors=data.get("authors", []),
                    year=data.get("year"),
                    journal=data.get("journal", ""),
                    volume=data.get("volume", ""),
                    issue=data.get("issue", ""),
                    pages=data.get("pages", ""),
                    doi=data.get("doi", ""),
                    pmid=data.get("pmid", ""),
                    abstract=data.get("abstract", ""),
                    keywords=data.get("keywords", []),
                    url=data.get("url", ""),
                )
                references.append(ref)
    return references
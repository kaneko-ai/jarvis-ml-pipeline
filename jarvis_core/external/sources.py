"""External Data Sources Management (Phase 2-ΩΩ P2).

Tracks origin, retrieval time, and licensing of external data
(IF, citation counts, Altmetrics, etc.)
"""
import datetime
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def log_external_source(
    run_dir: Path,
    paper_id: str,
    field: str,
    value: Any,
    source: str,
    license_type: str | None = None
) -> None:
    """Log external data source.
    
    Args:
        run_dir: Path to run directory
        paper_id: Paper identifier
        field: Field name (e.g., 'impact_factor', 'citation_count')
        value: Field value
        source: Data source (e.g., 'JCR', 'Crossref', 'OpenAlex')
        license_type: License type (e.g., 'CC-BY', 'proprietary')
    """
    sources_file = run_dir / "external_sources.json"

    # Load existing
    if sources_file.exists():
        with open(sources_file, encoding="utf-8") as f:
            sources = json.load(f)
    else:
        sources = []

    # Add entry
    entry = {
        "paper_id": paper_id,
        "field": field,
        "value": value,
        "source": source,
        "retrieved_at": datetime.datetime.now().isoformat(),
        "license": license_type,
        "status": "success" if value is not None else "missing"
    }

    sources.append(entry)

    # Save
    with open(sources_file, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)


def check_data_usage_allowed(
    run_dir: Path,
    paper_id: str,
    field: str
) -> bool:
    """Check if external data can be used in ranking.
    
    Args:
        run_dir: Path to run directory
        paper_id: Paper identifier
        field: Field name
        
    Returns:
        True if allowed to use
    """
    sources_file = run_dir / "external_sources.json"

    if not sources_file.exists():
        return False

    with open(sources_file, encoding="utf-8") as f:
        sources = json.load(f)

    # Find entry
    for entry in sources:
        if entry["paper_id"] == paper_id and entry["field"] == field:
            # Must have successful retrieval
            if entry["status"] != "success":
                return False

            # Must have valid value
            if entry["value"] is None:
                return False

            return True

    return False


def get_license_log(run_dir: Path) -> list[dict[str, Any]]:
    """Get license log for all papers.
    
    Args:
        run_dir: Path to run directory
        
    Returns:
        List of license entries
    """
    license_file = run_dir / "license_log.jsonl"

    if not license_file.exists():
        return []

    licenses = []
    with open(license_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                licenses.append(json.loads(line))

    return licenses


def log_license(
    run_dir: Path,
    paper_id: str,
    source_url: str,
    license_type: str,
    fulltext_store_allowed: bool
) -> None:
    """Log paper license information.
    
    Args:
        run_dir: Path to run directory
        paper_id: Paper identifier
        source_url: URL to paper
        license_type: License type
        fulltext_store_allowed: Whether fulltext storage is allowed
    """
    license_file = run_dir / "license_log.jsonl"

    entry = {
        "paper_id": paper_id,
        "source_url": source_url,
        "license_type": license_type,
        "fulltext_store_allowed": fulltext_store_allowed,
        "timestamp": datetime.datetime.now().isoformat()
    }

    with open(license_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

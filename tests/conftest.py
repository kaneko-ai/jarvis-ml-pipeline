"""Shared pytest fixtures and markers for JARVIS test suite."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --------------- markers ---------------

def pytest_configure(config):
    config.addinivalue_line("markers", "network: requires internet access")
    config.addinivalue_line("markers", "slow: slow test (>10s)")
    config.addinivalue_line("markers", "gemini: requires Gemini API key")


# --------------- fixtures ---------------

@pytest.fixture
def sample_papers():
    """Return a minimal list of paper dicts for testing."""
    return [
        {
            "title": "PD-1 blockade in tumors with mismatch-repair deficiency",
            "authors": ["Le DT", "Uram JN", "Wang H"],
            "year": 2015,
            "doi": "10.1056/NEJMoa1500596",
            "pmid": "26028255",
            "abstract": "Mismatch-repair status predicted clinical benefit of immune checkpoint blockade with pembrolizumab.",
            "source": "pubmed",
            "evidence_level": "1b",
            "score": 0.85,
        },
        {
            "title": "Spermidine promotes autophagy and longevity",
            "authors": ["Eisenberg T", "Knauer H", "Schauer A"],
            "year": 2009,
            "doi": "10.1038/ncb1975",
            "pmid": "19801973",
            "abstract": "Spermidine induces autophagy in yeast, flies, worms, and human cells, extending lifespan.",
            "source": "semantic_scholar",
            "evidence_level": "2b",
            "score": 0.72,
        },
        {
            "title": "Immunosenescence and autophagy in aging",
            "authors": ["Phadwal K", "Alegre-Abarrategui J"],
            "year": 2020,
            "doi": "10.1111/imm.13205",
            "pmid": "32463525",
            "abstract": "Autophagy declines with age, contributing to immunosenescence and chronic inflammation.",
            "source": "openalex",
            "evidence_level": "3",
            "score": 0.65,
        },
    ]


@pytest.fixture
def sample_papers_json(sample_papers, tmp_path):
    """Write sample papers to a temp JSON file and return path."""
    p = tmp_path / "test_papers.json"
    p.write_text(json.dumps(sample_papers, indent=2), encoding="utf-8")
    return str(p)


@pytest.fixture
def config_yaml():
    """Return path to project config.yaml."""
    p = PROJECT_ROOT / "config.yaml"
    if p.exists():
        return str(p)
    return None

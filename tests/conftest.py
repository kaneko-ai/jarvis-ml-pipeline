"""Shared pytest fixtures and configuration."""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# =============================================================================
# Environment Setup
# =============================================================================

# Disable network calls by default in tests
os.environ.setdefault("JARVIS_OFFLINE", "1")
os.environ.setdefault("JARVIS_TEST_MODE", "1")
os.environ.setdefault("JARVIS_LOG_LEVEL", "WARNING")

# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "network: mark test as requiring network")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip network tests by default."""
    skip_network = pytest.mark.skip(
        reason="Network tests disabled (set JARVIS_NETWORK_TESTS=1 to enable)"
    )
    skip_slow = pytest.mark.skip(reason="Slow tests disabled (set JARVIS_SLOW_TESTS=1 to enable)")

    for item in items:
        if "network" in item.keywords and not os.environ.get("JARVIS_NETWORK_TESTS"):
            item.add_marker(skip_network)
        if "slow" in item.keywords and not os.environ.get("JARVIS_SLOW_TESTS"):
            item.add_marker(skip_slow)


# =============================================================================
# Directory Fixtures
# =============================================================================


@pytest.fixture
def tmp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def fixtures_dir(project_root: Path) -> Path:
    """Return the fixtures directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def data_dir(tmp_dir: Path) -> Path:
    """Create and return a temporary data directory."""
    data = tmp_dir / "data"
    data.mkdir(parents=True, exist_ok=True)
    return data


@pytest.fixture
def runs_dir(data_dir: Path) -> Path:
    """Create and return a temporary runs directory."""
    runs = data_dir / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    return runs


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_llm() -> Generator[MagicMock, None, None]:
    """Mock LLM responses."""
    with patch("jarvis_core.llm.gemini.GeminiLLM") as mock:
        instance = MagicMock()
        instance.generate.return_value = "Mock LLM response"
        instance.generate_json.return_value = {"result": "mock"}
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_embeddings() -> Generator[MagicMock, None, None]:
    """Mock embeddings model."""
    with patch("jarvis_core.embeddings.sentence_transformer.SentenceTransformerEmbedding") as mock:
        instance = MagicMock()
        instance.encode.return_value = [[0.1] * 384]  # Mock embedding vector
        instance.dimension.return_value = 384
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_network() -> Generator[MagicMock, None, None]:
    """Mock network detector to always return offline."""
    with patch("jarvis_core.network.detector.NetworkDetector") as mock:
        instance = MagicMock()
        instance.is_online.return_value = False
        instance.check_endpoint.return_value = False
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_requests() -> Generator[MagicMock, None, None]:
    """Mock requests library for API tests."""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {"results": []}, text="", content=b""
        )
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"success": True}, text="", content=b""
        )
        yield {"get": mock_get, "post": mock_post}


@pytest.fixture
def mock_httpx() -> Generator[MagicMock, None, None]:
    """Mock httpx library for async API tests."""
    with patch("httpx.AsyncClient") as mock:
        client = MagicMock()
        client.get = MagicMock(
            return_value=MagicMock(status_code=200, json=lambda: {"results": []}, text="")
        )
        client.post = MagicMock(
            return_value=MagicMock(status_code=200, json=lambda: {"success": True}, text="")
        )
        mock.return_value.__aenter__ = MagicMock(return_value=client)
        mock.return_value.__aexit__ = MagicMock(return_value=None)
        yield client


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_paper() -> dict:
    """Return a sample paper dictionary."""
    return {
        "paper_id": "test_paper_001",
        "title": "A Randomized Controlled Trial of Drug X",
        "abstract": "Methods: We conducted a double-blind RCT with 500 participants...",
        "authors": ["Smith J", "Johnson A"],
        "year": 2024,
        "doi": "10.1234/test.001",
        "source": "pubmed",
        "pmid": "12345678",
    }


@pytest.fixture
def sample_papers(sample_paper: dict) -> list:
    """Return a list of sample papers."""
    papers = [sample_paper]
    for i in range(1, 5):
        paper = sample_paper.copy()
        paper["paper_id"] = f"test_paper_{i:03d}"
        paper["title"] = f"Test Paper {i}"
        papers.append(paper)
    return papers


@pytest.fixture
def sample_claim() -> dict:
    """Return a sample claim dictionary."""
    return {
        "claim_id": "claim_001",
        "text": "Drug X significantly improves survival rates",
        "paper_id": "test_paper_001",
        "evidence_level": "1b",
        "confidence": 0.85,
    }


@pytest.fixture
def sample_evidence() -> dict:
    """Return a sample evidence dictionary."""
    return {
        "evidence_id": "evidence_001",
        "claim_id": "claim_001",
        "text": "Survival rate improved from 60% to 85%",
        "locator": {"page": 5, "section": "Results"},
        "source_paper_id": "test_paper_001",
    }


@pytest.fixture
def sample_run_config() -> dict:
    """Return a sample run configuration."""
    return {
        "seed": 42,
        "max_papers": 10,
        "offline": True,
        "llm_backend": "mock",
        "embedding_model": "mock",
    }


# =============================================================================
# File Fixtures
# =============================================================================


@pytest.fixture
def sample_papers_jsonl(tmp_dir: Path, sample_papers: list) -> Path:
    """Create a sample papers.jsonl file."""
    filepath = tmp_dir / "papers.jsonl"
    with open(filepath, "w") as f:
        for paper in sample_papers:
            f.write(json.dumps(paper) + "\n")
    return filepath


@pytest.fixture
def sample_claims_jsonl(tmp_dir: Path, sample_claim: dict) -> Path:
    """Create a sample claims.jsonl file."""
    filepath = tmp_dir / "claims.jsonl"
    with open(filepath, "w") as f:
        f.write(json.dumps(sample_claim) + "\n")
    return filepath


@pytest.fixture
def sample_run_dir(runs_dir: Path, sample_paper: dict, sample_claim: dict) -> Path:
    """Create a sample run directory with all required files."""
    run_id = "test_run_001"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Create required bundle files
    files = {
        "input.json": {"query": "test query", "max_papers": 10},
        "run_config.json": {"seed": 42, "offline": True},
        "papers.jsonl": [sample_paper],
        "claims.jsonl": [sample_claim],
        "evidence.jsonl": [],
        "scores.json": {"papers": {}},
        "result.json": {"status": "success", "timestamp": "2024-01-01T00:00:00Z"},
        "eval_summary.json": {"gate_passed": True, "metrics": {}},
        "warnings.jsonl": [],
        "report.md": "# Test Report\n\nThis is a test report.",
    }

    for filename, content in files.items():
        filepath = run_dir / filename
        if filename.endswith(".jsonl"):
            with open(filepath, "w") as f:
                for item in content:
                    f.write(json.dumps(item) + "\n")
        elif filename.endswith(".json"):
            with open(filepath, "w") as f:
                json.dump(content, f)
        else:
            with open(filepath, "w") as f:
                f.write(content)

    return run_dir


# =============================================================================
# API Test Fixtures
# =============================================================================


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    try:
        from fastapi.testclient import TestClient
        from jarvis_web.app import app

        if app is None:
            pytest.skip("FastAPI not available")

        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI not installed")


@pytest.fixture
def auth_headers() -> dict:
    """Return authentication headers for API tests."""
    return {"Authorization": "Bearer test_token", "X-API-Key": "test_api_key"}


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def mock_db() -> Generator[MagicMock, None, None]:
    """Mock database connection."""
    with patch("jarvis_core.database.pool.get_connection") as mock:
        conn = MagicMock()
        conn.execute.return_value = MagicMock(fetchall=lambda: [])
        conn.commit.return_value = None
        mock_db_instance = MagicMock()
        mock_db_instance.__enter__ = MagicMock(return_value=conn)
        mock_db_instance.__exit__ = MagicMock(return_value=None)
        mock.return_value = mock_db_instance
        yield conn


# =============================================================================
# Cleanup Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances after each test."""
    yield
    # Add singleton reset logic here if needed

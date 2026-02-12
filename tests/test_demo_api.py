"""Landing page demo API contract tests."""

from __future__ import annotations

import pytest

import jarvis_web.app as app_module

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


@pytest.fixture()
def client():
    if TestClient is None or app_module.app is None:
        pytest.skip("FastAPI not available")
    return TestClient(app_module.app)


def _assert_envelope(payload: dict) -> None:
    assert payload["status"] == "ok"
    assert "data" in payload
    assert "errors" in payload
    assert isinstance(payload["errors"], list)


def test_demo_evidence_grade_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/demo/evidence/grade",
        json={
            "title": "A randomized controlled trial for chronic insomnia",
            "abstract": "Methods: double-blind placebo-controlled randomized trial.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    data = payload["data"]
    assert data["level"] in {"1a", "1b", "1c", "2a", "2b", "2c", "3a", "3b", "4", "5", "unknown"}
    assert 0 <= data["confidence"] <= 100
    assert data["source"] == "api"


def test_demo_citation_analyze_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/demo/citation/analyze",
        json={
            "text": (
                "Previous studies showed positive outcomes (Smith et al., 2020), "
                "however later work disputed the method (Jones, 2021)."
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    data = payload["data"]
    assert "citations" in data
    assert "summary" in data
    assert data["source"] == "api"
    assert isinstance(data["summary"]["total"], int)


def test_demo_contradiction_detect_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/demo/contradiction/detect",
        json={
            "claim_a": "Drug X significantly increases survival rates.",
            "claim_b": "Drug X significantly decreases survival rates.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    data = payload["data"]
    assert "isContradictory" in data
    assert "confidence" in data
    assert "contradictionType" in data
    assert data["source"] == "api"

from fastapi.testclient import TestClient

from jarvis_core.api import app


def test_literature_survey_endpoint(monkeypatch):
    """Smoke test for the literature survey endpoint."""

    def fake_run_jarvis(prompt: str) -> str:  # type: ignore[override]
        assert "literature" in prompt.lower()
        return "mocked literature summary"

    monkeypatch.setattr("jarvis_core.api.run_jarvis", fake_run_jarvis)

    client = TestClient(app)
    response = client.post(
        "/literature-survey",
        json={"topic": "DNA repair", "max_papers": 3, "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert body["summary"] == "mocked literature summary"

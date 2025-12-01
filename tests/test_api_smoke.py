from fastapi.testclient import TestClient

from jarvis_core.api import app


def test_jarvis_endpoint(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr("jarvis_core.api.run_jarvis", lambda goal: f"processed: {goal}")

    response = client.post("/jarvis", json={"goal": "test goal"})

    assert response.status_code == 200
    assert response.json() == {"answer": "processed: test goal"}

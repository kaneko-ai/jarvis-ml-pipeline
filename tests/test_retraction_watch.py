import pytest

from jarvis_core.sources.retraction_watch import check_retraction, RetractionStatus


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.core
def test_retraction_watch_detects(monkeypatch):
    def fake_get(url, timeout=10):
        return _FakeResponse(
            {
                "count": 1,
                "results": [
                    {
                        "retraction_date": "2024-01-01",
                        "reason": "Data issues",
                        "url": url,
                    }
                ],
            }
        )

    monkeypatch.setattr("jarvis_core.sources.retraction_watch.requests.get", fake_get)
    status = check_retraction("10.1234/example")
    assert isinstance(status, RetractionStatus)
    assert status.is_retracted is True
    assert status.reason == "Data issues"

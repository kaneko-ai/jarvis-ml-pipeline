import pytest

from jarvis_core.security.pii_detector import detect_pii


@pytest.mark.core
def test_detect_pii():
    text = "Contact me at test@example.com or 123-45-6789."
    detections = detect_pii(text)
    types = {d.type for d in detections}
    assert "email" in types
    assert "ssn" in types
import pytest

from jarvis_core.security.anonymizer import anonymize
from jarvis_core.security.pii_detector import PIIDetection


@pytest.mark.core
def test_anonymize_mask():
    text = "Email test@example.com"
    detections = [
        PIIDetection(type="email", value="test@example.com", start=6, end=22, confidence=0.9)
    ]
    result = anonymize(text, detections, strategy="mask")
    assert "*" in result


@pytest.mark.core
def test_anonymize_remove():
    text = "SSN 123-45-6789"
    detections = [PIIDetection(type="ssn", value="123-45-6789", start=4, end=15, confidence=0.9)]
    result = anonymize(text, detections, strategy="remove")
    assert "123-45-6789" not in result
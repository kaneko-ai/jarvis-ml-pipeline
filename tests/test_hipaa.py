import pytest

from jarvis_core.advanced.features import HIPAAComplianceChecker


@pytest.mark.core
def test_hipaa_identifiers():
    checker = HIPAAComplianceChecker()
    result = checker.check("Patient John Doe SSN 123-45-6789")
    assert result.compliant is False
    assert "ssn" in result.violations
    assert result.recommendations

from jarvis_core.compliance.license import LicenseFilter, LicenseType


def test_license_parsing():
    f = LicenseFilter()

    assert f._parse_license("CC-BY") == LicenseType.CC_BY
    assert f._parse_license("cc by 4.0") == LicenseType.CC_BY
    assert f._parse_license("Public Domain") == LicenseType.CC0
    assert f._parse_license("CC-BY-NC") == LicenseType.CC_BY_NC
    assert f._parse_license("All rights reserved") == LicenseType.UNKNOWN


def test_license_filtering():
    f = LicenseFilter()

    results = [
        {"id": "1", "license": "CC-BY"},
        {"id": "2", "license": "CC-BY-NC"},  # Default disallowed
        {"id": "3", "license": "Unknown"},
        {"id": "4", "license": "CC0"},
    ]

    filtered = f.filter_results(results)
    ids = [r["id"] for r in filtered]

    assert "1" in ids
    assert "4" in ids
    assert "2" not in ids
    assert "3" not in ids


def test_custom_allowlist():
    allowlist = {LicenseType.CC_BY_NC}
    f = LicenseFilter(allowlist=allowlist)

    assert f.is_allowed("CC-BY-NC")
    assert not f.is_allowed("CC-BY")
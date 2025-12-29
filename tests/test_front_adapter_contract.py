import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.core

ROOT = Path(__file__).resolve().parents[1]
API_MAP_PATH = ROOT / "schemas" / "api_map_v1.json"
ADAPTER_MANIFEST_PATH = ROOT / "dashboard" / "adapter_manifest.js"
CAPABILITIES_PATH = ROOT / "schemas" / "capabilities_v1.json"


def load_manifest():
    content = ADAPTER_MANIFEST_PATH.read_text(encoding="utf-8")
    match = re.search(r"JARVIS_ADAPTER_MANIFEST\s*=\s*(\{.*\});", content, re.S)
    if not match:
        raise AssertionError("adapter_manifest.js does not define JARVIS_ADAPTER_MANIFEST")
    return json.loads(match.group(1))


def test_adapter_manifest_matches_api_map():
    api_map = json.loads(API_MAP_PATH.read_text(encoding="utf-8"))
    manifest = load_manifest()

    assert manifest["apiMapVersion"] == api_map["version"]

    api_paths = {item["path"] for item in api_map["endpoints"]}
    manifest_paths = set(manifest["endpoints"].values())

    assert manifest_paths.issubset(api_paths)


def test_adapter_manifest_capabilities_match():
    manifest = load_manifest()
    capabilities = json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))

    assert set(manifest["capabilities"]) == set(capabilities["capabilities"].keys())

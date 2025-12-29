import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.core

ROOT = Path(__file__).resolve().parents[1]
API_MAP_PATH = ROOT / "schemas" / "api_map_v1.json"
CAPABILITIES_PATH = ROOT / "schemas" / "capabilities_v1.json"


def test_api_map_matches_capabilities():
    api_map = json.loads(API_MAP_PATH.read_text(encoding="utf-8"))
    capabilities = json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))

    endpoint_caps = {item["capability"] for item in api_map["endpoints"]}
    declared_caps = set(capabilities["capabilities"].keys())

    assert endpoint_caps == declared_caps


def test_api_map_has_unique_routes():
    api_map = json.loads(API_MAP_PATH.read_text(encoding="utf-8"))
    routes = {(item["method"], item["path"]) for item in api_map["endpoints"]}
    assert len(routes) == len(api_map["endpoints"])

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_MAP_PATH = ROOT / "jarvis_web" / "contracts" / "api_map_v1.json"
ADAPTER_MANIFEST_PATH = ROOT / "dashboard" / "assets" / "adapter_manifest.js"


def _load_adapter_requirements() -> dict:
    content = ADAPTER_MANIFEST_PATH.read_text(encoding="utf-8")
    match = re.search(r"ADAPTER_REQUIREMENTS\s*=\s*(\{.*?\});", content, re.S)
    if not match:
        raise AssertionError("ADAPTER_REQUIREMENTS not found in adapter_manifest.js")
    return json.loads(match.group(1))


def test_adapter_manifest_matches_api_map():
    api_map = json.loads(API_MAP_PATH.read_text(encoding="utf-8"))
    base_paths = api_map.get("base_paths", {})
    requirements = _load_adapter_requirements()

    required_keys = sorted({key for group in requirements.values() for key in group})
    missing = [key for key in required_keys if key not in base_paths]

    assert not missing, f"Missing API map keys: {missing}"
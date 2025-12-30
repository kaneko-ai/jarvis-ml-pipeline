from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_MAP_PATH = ROOT / "jarvis_web" / "contracts" / "api_map_v1.json"
ADAPTER_MANIFEST_PATH = ROOT / "dashboard" / "assets" / "adapter_manifest.js"


def _normalize_manifest_payload(payload: str) -> str:
    return re.sub(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", r'"\1":', payload)


def _load_adapter_requirements() -> dict:
    content = ADAPTER_MANIFEST_PATH.read_text(encoding="utf-8")
    match = re.search(r"ADAPTER_REQUIREMENTS\s*=\s*(\{.*?\});", content, re.S)
    if not match:
        raise ValueError("ADAPTER_REQUIREMENTS not found in adapter_manifest.js")
    payload = _normalize_manifest_payload(match.group(1))
    return json.loads(payload)


def audit_ui_contract() -> int:
    if not API_MAP_PATH.exists():
        print(f"Missing API map: {API_MAP_PATH}", file=sys.stderr)
        return 1
    if not ADAPTER_MANIFEST_PATH.exists():
        print(f"Missing adapter manifest: {ADAPTER_MANIFEST_PATH}", file=sys.stderr)
        return 1

    api_map = json.loads(API_MAP_PATH.read_text(encoding="utf-8"))
    base_paths = api_map.get("base_paths", {})
    requirements = _load_adapter_requirements()

    required_keys = sorted({key for group in requirements.values() for key in group})
    missing = [key for key in required_keys if key not in base_paths]
    if missing:
        print(f"Missing API map keys for UI adapter: {missing}", file=sys.stderr)
        return 1

    print("UI contract audit passed")
    return 0


def main() -> None:
    raise SystemExit(audit_ui_contract())


if __name__ == "__main__":
    main()

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_MAP_PATH = ROOT / "jarvis_web" / "contracts" / "api_map_v1.json"

API_MAP = {
    "version": "v1",
    "base_path": "/api",
    "endpoints": [
        {"path": "/health", "method": "GET", "capability": "health"},
        {"path": "/capabilities", "method": "GET", "capability": "capabilities"},
        {"path": "/runs", "method": "GET", "capability": "runs"},
        {"path": "/runs/{id}", "method": "GET", "capability": "runs.detail"},
        {"path": "/runs/{id}/files", "method": "GET", "capability": "runs.files"},
        {"path": "/runs/{id}/files/{path}", "method": "GET", "capability": "runs.files.download"},
        {"path": "/research/rank", "method": "GET", "capability": "research.rank"},
        {"path": "/qa/report", "method": "GET", "capability": "qa.report"},
        {"path": "/submission/decision", "method": "POST", "capability": "submission.decision"},
        {"path": "/finance/forecast", "method": "POST", "capability": "finance.forecast"},
    ],
}


def main() -> None:
    API_MAP_PATH.write_text(
        json.dumps(API_MAP, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

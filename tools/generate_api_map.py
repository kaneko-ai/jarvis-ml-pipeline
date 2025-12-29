from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

PATH_KEY_MAP = {
    "/api/runs": "runs_list",
    "/api/runs/{run_id}": "run_detail",
    "/api/runs/{run_id}/files": "run_files",
    "/api/runs/{run_id}/files/{path}": "run_file_get",
    "/api/runs/{run_id}/manifest": "run_manifest",
    "/api/capabilities": "capabilities",
    "/api/health": "health",
    "/api/research/rank": "research_rank",
    "/api/research/paper/{paper_id}": "research_paper",
    "/api/qa/report": "qa_report",
    "/api/submission/build": "submission_build",
    "/api/submission/run/{run_id}/latest": "submission_latest",
    "/api/feedback/risk": "feedback_risk",
    "/api/decision/simulate": "decision_simulate",
    "/api/finance/optimize": "finance_optimize",
    "/api/finance/simulate": "finance_simulate",
    "/api/finance/download": "finance_download",
    "/api/jobs": "jobs",
    "/api/jobs/{job_id}": "job_detail",
    "/api/jobs/{job_id}/events": "job_events",
    "/api/search": "search",
    "/api/upload/pdf": "upload_pdf",
    "/api/upload/bibtex": "upload_bibtex",
    "/api/upload/zip": "upload_zip",
}

METHOD_MAP = {
    "get": "GET",
    "post": "POST",
}


def _load_contract(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _extract_query_params(path_item: Dict[str, Any]) -> List[str]:
    params: List[str] = []
    for param in path_item.get("parameters", []) or []:
        if param.get("in") == "query" and param.get("name"):
            params.append(param["name"])
    for method in METHOD_MAP:
        method_item = path_item.get(method, {}) or {}
        for param in method_item.get("parameters", []) or []:
            if param.get("in") == "query" and param.get("name"):
                params.append(param["name"])
    return sorted(set(params))


def generate_api_map(contract: Dict[str, Any]) -> Dict[str, Any]:
    paths = contract.get("paths", {}) or {}
    base_paths: Dict[str, str] = {}
    methods: Dict[str, str] = {}
    query_params: Dict[str, List[str]] = {}

    for path, key in PATH_KEY_MAP.items():
        if path not in paths:
            continue
        base_paths[key] = path
        path_item = paths.get(path, {}) or {}
        for method in METHOD_MAP:
            if method in path_item:
                methods[key] = METHOD_MAP[method]
                break
        params = _extract_query_params(path_item)
        if params:
            query_params[key] = params

    return {
        "version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_paths": base_paths,
        "methods": methods,
        "query_params": query_params,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate API map from OpenAPI contract")
    parser.add_argument(
        "--input",
        default="jarvis_web/contracts/api_contract_v1.yaml",
        type=Path,
    )
    parser.add_argument(
        "--output",
        default="jarvis_web/contracts/api_map_v1.json",
        type=Path,
    )
    args = parser.parse_args()

    contract = _load_contract(args.input)
    api_map = generate_api_map(contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(api_map, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()

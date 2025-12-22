#!/usr/bin/env python
"""HTTP Recorder.

Per PR-64, records HTTP responses for fixture generation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import requests


TARGETS = {
    "pubmed_esearch": {
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        "params": {"db": "pubmed", "retmode": "json", "retmax": 10},
    },
    "pubmed_esummary": {
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        "params": {"db": "pubmed", "retmode": "json"},
    },
    "unpaywall": {
        "url": "https://api.unpaywall.org/v2/{doi}",
        "params": {},
    },
}


def record_http(target: str, query: str = "", output_dir: str = "tests/fixtures/http") -> str:
    """Record an HTTP response to a fixture file."""
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}. Available: {list(TARGETS.keys())}")

    config = TARGETS[target]
    url = config["url"]
    params = dict(config["params"])

    # Add query-specific params
    if target == "pubmed_esearch" and query:
        params["term"] = query
    elif target == "pubmed_esummary" and query:
        params["id"] = query

    # Make request
    response = requests.get(url, params=params, timeout=30)

    # Build fixture
    fixture = {
        "url": url,
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.text,
    }

    # Save
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    safe_query = query.replace(" ", "_").replace("/", "_")[:30] if query else "default"
    filename = f"{target}_{safe_query}.json"

    with open(out_path / filename, "w", encoding="utf-8") as f:
        json.dump(fixture, f, indent=2, ensure_ascii=False)

    return str(out_path / filename)


def main():
    parser = argparse.ArgumentParser(description="Record HTTP fixtures")
    parser.add_argument("--target", type=str, required=True, choices=list(TARGETS.keys()))
    parser.add_argument("--query", type=str, default="", help="Query parameter")
    parser.add_argument("--out", type=str, default="tests/fixtures/http")

    args = parser.parse_args()

    try:
        output = record_http(args.target, args.query, args.out)
        print(f"Recorded to: {output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

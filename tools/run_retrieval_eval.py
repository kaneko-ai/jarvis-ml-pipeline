"""Run retrieval eval set and compute basic metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from jarvis_core.retrieval.hybrid_search import HybridSearchEngine


def load_eval_set(path: Path) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def match_expected(item, expected):
    if "doc_id" in expected and item.get("doc_id") == expected["doc_id"]:
        return True
    if "pmid" in expected and item.get("provenance", {}).get("pmid") == expected["pmid"]:
        return True
    return False


def evaluate(engine: HybridSearchEngine, eval_rows: List[Dict], top_k: int) -> Dict:
    hits = 0
    mrr_total = 0.0
    for row in eval_rows:
        result = engine.search(query=row["query"], top_k=top_k, mode="hybrid")
        expected_any = row.get("expected_any", [])
        rank = None
        for idx, item in enumerate(result.to_dict()["results"], start=1):
            if any(match_expected(item, exp) for exp in expected_any):
                rank = idx
                break
        if rank is not None:
            hits += 1
            mrr_total += 1.0 / rank
    recall = hits / len(eval_rows) if eval_rows else 0.0
    mrr = mrr_total / len(eval_rows) if eval_rows else 0.0
    return {"recall": recall, "mrr": mrr, "count": len(eval_rows)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", default="eval/retrieval_eval_set.jsonl")
    parser.add_argument("--index-dir", default="data/index/v2")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--min-recall", type=float, default=0.75)
    parser.add_argument("--min-mrr", type=float, default=0.35)
    args = parser.parse_args()

    eval_rows = load_eval_set(Path(args.eval_set))
    engine = HybridSearchEngine(index_dir=Path(args.index_dir))
    metrics = evaluate(engine, eval_rows, args.top_k)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    if metrics["recall"] < args.min_recall or metrics["mrr"] < args.min_mrr:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

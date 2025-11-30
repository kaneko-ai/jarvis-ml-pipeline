import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List

import numpy as np
from joblib import load
import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    path = pathlib.Path(config_path)
    if not path.exists():
        print(f"[load_config] Config not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_index(index_path: pathlib.Path) -> Dict[str, Any]:
    if not index_path.exists():
        print(f"[load_index] Index file not found: {index_path}", file=sys.stderr)
        sys.exit(1)

    index_obj = load(index_path)
    return index_obj


def load_chunks(chunks_path: pathlib.Path) -> List[Dict[str, Any]]:
    if not chunks_path.exists():
        print(f"[load_chunks] chunks file not found: {chunks_path}", file=sys.stderr)
        sys.exit(1)

    records: List[Dict[str, Any]] = []
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = str(rec.get("text", "")).strip()
            if not text:
                continue

            records.append(rec)

    if not records:
        print("[load_chunks] no valid chunks found in file.", file=sys.stderr)
        sys.exit(1)

    return records


def search(
    config_path: str,
    query: str,
    top_k: int = 5,
) -> None:
    config = load_config(config_path)
    index_path = pathlib.Path(config["paths"]["index_path"])
    processed_dir = pathlib.Path(config["paths"]["processed_dir"])
    chunks_path = processed_dir / "chunks.jsonl"

    index_obj = load_index(index_path)

    vectorizer = index_obj.get("vectorizer")
    matrix = index_obj.get("matrix")
    metadata = index_obj.get("metadata")

    if vectorizer is None or matrix is None or not metadata:
        print(
            "[search] Index is empty. "
            "おそらく PDF が無い環境で作ったインデックスです。",
            file=sys.stderr,
        )
        sys.exit(1)

    chunks = load_chunks(chunks_path)

    if len(chunks) != len(metadata):
        print(
            "[search] WARNING: chunks と metadata の件数が一致していません。"
            f" chunks={len(chunks)}, metadata={len(metadata)}",
            file=sys.stderr,
        )

    print(f"[search] query = {query!r}")
    q_vec = vectorizer.transform([query])
    scores = (matrix @ q_vec.T).toarray().ravel()

    if top_k > len(scores):
        top_k = len(scores)

    top_idx = np.argsort(scores)[::-1][:top_k]

    print(f"[search] top {top_k} results:\n")

    for rank, idx in enumerate(top_idx, start=1):
        score = float(scores[idx])
        meta = metadata[idx] if idx < len(metadata) else {}
        chunk = chunks[idx] if idx < len(chunks) else {}

        source = meta.get("source") or chunk.get("source")
        chunk_id = meta.get("chunk_id") or chunk.get("chunk_id")

        text = str(chunk.get("text", "")).strip().replace("\n", " ")
        if len(text) > 200:
            text_preview = text[:200] + "..."
        else:
            text_preview = text

        print(f"--- rank {rank} ---")
        print(f"score   : {score:.4f}")
        print(f"source  : {source} (chunk_id={chunk_id})")
        print(f"text    : {text_preview}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search CDH13 TF-IDF index built by run_pipeline.py",
    )
    parser.add_argument("config", help="YAML 設定ファイルへのパス")
    parser.add_argument("--query", "-q", required=True, help="検索クエリ文字列")
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="上位何件のチャンクを表示するか (default: 5)",
    )
    args = parser.parse_args()

    search(args.config, args.query, top_k=args.top_k)


if __name__ == "__main__":
    main()

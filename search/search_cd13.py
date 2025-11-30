import json
import pathlib
import argparse
from typing import List, Dict, Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ========== ロード系 ==========

def load_chunks(chunks_path: pathlib.Path) -> List[Dict[str, Any]]:
    """chunks.jsonl を読み込んで list[dict] にする"""
    chunks: List[Dict[str, Any]] = []

    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            chunks.append(data)

    return chunks


def load_metadata(meta_path: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    """
    pubmed_metadata.json を読み込んで
    paper_id(らしきもの) -> metadata の dict にする。

    フォーマットがいくつかあり得るので、かなりゆるめに対応する。
    """
    with meta_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # パターン1: list[dict]
    if isinstance(data, list):
        if not data:
            return {}

        first = data[0]

        # 1-1. dict のリスト
        if isinstance(first, dict):
            # paper_id の候補キー
            id_keys = ["paper_id", "pmid", "pmcid", "id"]
            id_key = None
            for k in id_keys:
                if k in first:
                    id_key = k
                    break

            if id_key is not None:
                return {str(d[id_key]): d for d in data if id_key in d}
            else:
                # ID キーが分からない場合は単純にインデックスで紐づける
                return {str(i): d for i, d in enumerate(data)}

        # 1-2. 文字列のリスト（おそらく pmid のみ）
        elif isinstance(first, str):
            meta = {}
            for s in data:
                s = str(s)
                meta[s] = {
                    "paper_id": s,
                    "title": "",
                    "journal": "",
                    "year": "",
                }
            return meta

        else:
            return {}

    # パターン2: dict（キーが pmid など）
    elif isinstance(data, dict):
        # そのまま ID -> メタとして扱う
        return {str(k): v for k, v in data.items()}

    # それ以外は諦めて空 dict
    return {}


# ========== 検索系 ==========

def build_tfidf_index(chunks: List[Dict[str, Any]]):
    """チャンクの text から TF-IDF ベクトルを作成"""

    if not chunks:
        raise ValueError("チャンクが 0 件です。先にパイプラインの出力を確認してください。")

    # 'text' というキー前提。違う場合はここを変える。
    texts = [str(c.get("text", "")) for c in chunks]

    vectorizer = TfidfVectorizer(
        max_features=50000,
        ngram_range=(1, 2),
        stop_words=None,
    )
    X = vectorizer.fit_transform(texts)
    return vectorizer, X


def search(
    query: str,
    vectorizer: TfidfVectorizer,
    X,
    chunks: List[Dict[str, Any]],
    meta_dict: Dict[str, Dict[str, Any]],
    top_k: int = 5,
):
    """クエリに対して上位 top_k 件のチャンクを表示"""

    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, X).ravel()

    if sims.size == 0:
        print("ベクトルが空です。")
        return

    top_idx = np.argsort(sims)[::-1][:top_k]

    for rank, idx in enumerate(top_idx, start=1):
        chunk = chunks[idx]
        score = sims[idx]

        # paper_id / pmid などを探す
        paper_id = (
            str(chunk.get("paper_id"))
            if "paper_id" in chunk
            else str(chunk.get("pmid"))
            if "pmid" in chunk
            else str(chunk.get("id"))
            if "id" in chunk
            else str(idx)
        )

        meta = meta_dict.get(paper_id, {})
        title = meta.get("title", "(タイトル不明)")
        journal = meta.get("journal", "")
        year = meta.get("year", "")

        print("=" * 80)
        print(f"[{rank}] score={score:.3f}")
        print(f"paper_id: {paper_id}")
        if title:
            print(f"title   : {title}")
        if journal or year:
            print(f"source  : {journal} ({year})")
        print("-" * 80)

        text = str(chunk.get("text", ""))
        # 長すぎるときは先頭 800 文字だけ
        print(text[:800])
        print()


# ========== main ==========

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="検索クエリ（例：'T-cadherin 動脈硬化'）")
    parser.add_argument(
        "--base-dir",
        type=str,
        required=True,
        help="cd13_2025_11_30_outputs など、outputs フォルダのパス",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        required=True,
        help="processed/raw 配下のサブフォルダ名（例：cd13_2025_11_30, cd73_light など）",
    )
    parser.add_argument("--top-k", type=int, default=5, help="表示する上位件数")
    args = parser.parse_args()

    base_dir = pathlib.Path(args.base_dir)
    dataset = args.dataset_name

    chunks_path = base_dir / "data" / "processed" / dataset / "chunks.jsonl"
    meta_path = base_dir / "data" / "raw" / dataset / "pubmed_metadata.json"

    if not chunks_path.exists():
        raise FileNotFoundError(f"chunks.jsonl が見つかりません: {chunks_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"pubmed_metadata.json が見つかりません: {meta_path}")

    print(f"Loading chunks from {chunks_path} ...")
    chunks = load_chunks(chunks_path)
    print(f"チャンク数: {len(chunks)}")

    if not chunks:
        print("チャンク数が 0 件です。このデータセットにはテキストが入っていません。")
        return

    print("Loading metadata ...")
    meta_dict = load_metadata(meta_path)
    print(f"メタデータ数: {len(meta_dict)}")

    print("Building TF-IDF index ...")
    vectorizer, X = build_tfidf_index(chunks)

    print()
    print(f"クエリ: {args.query}")
    print()
    search(args.query, vectorizer, X, chunks, meta_dict, top_k=args.top_k)


if __name__ == "__main__":
    main()

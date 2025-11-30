import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================================
# 1. パス設定（あなたの環境専用）
# =========================================

# このファイル（search_cd73.py）から見て、1個上がリポジトリのルート
ROOT_DIR = Path(__file__).resolve().parents[1]

# chunks.jsonl と pubmed_metadata.json へのパスを「固定」で指定
CHUNKS_PATH = ROOT_DIR / "data" / "processed" / "cd73_light" / "chunks.jsonl"
META_PATH = ROOT_DIR / "data" / "raw" / "cd73_light" / "pubmed_metadata.json"


# =========================================
# 2. ロード関数
# =========================================

def load_chunks(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"chunks.jsonl が見つかりません: {path}")

    chunks = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


def load_metadata(path: Path) -> Dict[str, Dict[str, Any]]:
    """メタデータは形式が色々ありうるので、かなり緩く扱う"""
    if not path.exists():
        # なくても検索自体はできるので、空で返す
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # list[dict]
    if isinstance(data, list):
        if not data:
            return {}
        first = data[0]
        if isinstance(first, dict):
            id_keys = ["paper_id", "pmid", "pmcid", "id"]
            id_key = None
            for k in id_keys:
                if k in first:
                    id_key = k
                    break
            if id_key is not None:
                return {str(d[id_key]): d for d in data if id_key in d}
            else:
                return {str(i): d for i, d in enumerate(data)}
        elif isinstance(first, str):
            return {s: {"paper_id": s} for s in data}
        else:
            return {}

    # dict ならそのまま
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items()}

    return {}


# =========================================
# 3. 検索本体
# =========================================

def build_index(chunks: List[Dict[str, Any]]):
    if not chunks:
        raise ValueError("チャンクが 0 件です。先にパイプラインの出力を確認してください。")

    texts = [str(c.get("text", "")) for c in chunks]
    vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)
    return vectorizer, X


def search(query: str, top_k: int = 5):
    print(f"chunks: {CHUNKS_PATH}")
    print(f"meta  : {META_PATH}")

    chunks = load_chunks(CHUNKS_PATH)
    print(f"チャンク数: {len(chunks)}")

    meta = load_metadata(META_PATH)
    print(f"メタデータ数: {len(meta)}")

    vectorizer, X = build_index(chunks)

    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, X).ravel()

    top_idx = np.argsort(sims)[::-1][:top_k]

    for rank, idx in enumerate(top_idx, start=1):
        chunk = chunks[idx]
        score = sims[idx]

        # paper_id / pmid / id のどれかを拾う
        paper_id = (
            str(chunk.get("paper_id"))
            if "paper_id" in chunk
            else str(chunk.get("pmid"))
            if "pmid" in chunk
            else str(chunk.get("id"))
            if "id" in chunk
            else str(idx)
        )

        m = meta.get(paper_id, {})
        title = m.get("title", "(タイトル不明)")
        journal = m.get("journal", "")
        year = m.get("year", "")

        print("=" * 80)
        print(f"[{rank}] score={score:.3f}")
        print(f"paper_id: {paper_id}")
        if title:
            print(f"title   : {title}")
        if journal or year:
            print(f"source  : {journal} ({year})")
        print("-" * 80)
        text = str(chunk.get("text", ""))
        print(text[:800])  # 長すぎるので先頭800文字だけ
        print()


# =========================================
# 4. エントリポイント
# =========================================

def main():
    if len(sys.argv) < 2:
        print("使い方: python search_cd73.py \"検索クエリ\"")
        sys.exit(1)

    query = sys.argv[1]
    print()
    print(f"クエリ: {query}")
    print()
    search(query, top_k=5)


if __name__ == "__main__":
    main()

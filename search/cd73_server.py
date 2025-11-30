from __future__ import annotations

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, List
import urllib.parse as urlparse

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ======================================================
# 1. CD73 コーパスのロード & インデックス作成
# ======================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT_DIR / "data" / "processed" / "cd73_light" / "chunks.jsonl"
META_PATH = ROOT_DIR / "data" / "raw" / "cd73_light" / "pubmed_metadata.json"

print(f"[init] chunks: {CHUNKS_PATH}")
print(f"[init] meta  : {META_PATH}")


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"chunks.jsonl が見つかりません: {path}")

    chunks: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


def load_metadata(path: Path) -> Dict[str, Dict[str, Any]]:
    """メタデータ形式が何パターンかありうるので緩く対応する"""
    if not path.exists():
        print("[init] pubmed_metadata.json が無いのでメタデータなしで続行します")
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
            id_key = next((k for k in id_keys if k in first), None)
            if id_key is not None:
                return {str(d[id_key]): d for d in data if id_key in d}
            else:
                return {str(i): d for i, d in enumerate(data)}
        elif isinstance(first, str):
            return {s: {"paper_id": s} for s in data}

    # dict
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items()}

    return {}


def build_index(chunks: List[Dict[str, Any]]):
    if not chunks:
        raise ValueError("チャンクが 0 件です。先にパイプラインの出力を確認してください。")

    texts = [str(c.get("text", "")) for c in chunks]
    vec = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
    mat = vec.fit_transform(texts)
    return vec, mat


print("[init] loading CD73 chunks ...")
CHUNKS = load_chunks(CHUNKS_PATH)
print(f"[init] チャンク数: {len(CHUNKS)}")

print("[init] loading metadata ...")
META = load_metadata(META_PATH)
print(f"[init] メタデータ数: {len(META)}")

print("[init] building TF-IDF index ...  (数秒かかることがあります)")
VECTORIZER, MATRIX = build_index(CHUNKS)
print("[init] index ready.")


def run_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """クエリに対する上位チャンクを返す（API 用）"""
    q_vec = VECTORIZER.transform([query])
    sims = cosine_similarity(q_vec, MATRIX).ravel()

    idxs = np.argsort(sims)[::-1][:top_k]
    results: List[Dict[str, Any]] = []

    for rank, idx in enumerate(idxs, start=1):
        c = CHUNKS[idx]
        score = float(sims[idx])

        paper_id = (
            str(c.get("paper_id"))
            if "paper_id" in c
            else str(c.get("pmid"))
            if "pmid" in c
            else str(c.get("id", idx))
        )

        m = META.get(paper_id, {})
        result = {
            "rank": rank,
            "score": score,
            "paper_id": paper_id,
            "title": m.get("title", "(タイトル不明)"),
            "journal": m.get("journal"),
            "year": m.get("year"),
            "text": str(c.get("text", "")),
        }
        results.append(result)

    return results


# ======================================================
# 2. HTTP サーバ
# ======================================================

class CD73Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse.urlparse(self.path)

        if parsed.path != "/search_cd73":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        params = urlparse.parse_qs(parsed.query)
        query = params.get("q", [""])[0]
        top_k_str = params.get("top_k", ["5"])[0]

        if not query:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing 'q' parameter")
            return

        try:
            top_k = int(top_k_str)
        except ValueError:
            top_k = 5

        try:
            results = run_search(query, top_k=top_k)
            payload = {
                "query": query,
                "results": results,
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            # 簡易エラーハンドリング
            msg = {"error": str(e)}
            body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    # ログがうるさいので抑制
    def log_message(self, format, *args):
        return


def run(server_port: int = 8000):
    server_address = ("0.0.0.0", server_port)
    httpd = HTTPServer(server_address, CD73Handler)
    print(f"[server] CD73 search server running at http://127.0.0.1:{server_port}")
    print("[server] Ctrl+C で停止します")
    httpd.serve_forever()


if __name__ == "__main__":
    run()

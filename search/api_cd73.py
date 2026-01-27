# search/api_cd73.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
from pathlib import Path
import json
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT_DIR = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT_DIR / "data" / "processed" / "cd73_light" / "chunks.jsonl"
META_PATH = ROOT_DIR / "data" / "raw" / "cd73_light" / "pubmed_metadata.json"

app = FastAPI(title="CD73 Search API")

# 起動時に一度だけロード＆インデックス構築
chunks: List[Dict[str, Any]] = []
meta: Dict[str, Dict[str, Any]] = {}
vectorizer: TfidfVectorizer
X = None


def load_chunks(path: Path):
    cs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cs.append(json.loads(line))
    return cs


def load_meta(path: Path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        if not data:
            return {}
        first = data[0]
        if isinstance(first, dict):
            key = next((k for k in ["paper_id", "pmid", "id"] if k in first), None)
            if key:
                return {str(d[key]): d for d in data if key in d}
            else:
                return {str(i): d for i, d in enumerate(data)}
        elif isinstance(first, str):
            return {s: {"paper_id": s} for s in data}
    elif isinstance(data, dict):
        return {str(k): v for k, v in data.items()}
    return {}


def build_index(cs: List[Dict[str, Any]]):
    texts = [str(c.get("text", "")) for c in cs]
    vec = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
    mat = vec.fit_transform(texts)
    return vec, mat


@app.on_event("startup")
def startup_event():
    global chunks, meta, vectorizer, X
    chunks = load_chunks(CHUNKS_PATH)
    meta = load_meta(META_PATH)
    vectorizer, X = build_index(chunks)


class SearchResult(BaseModel):
    rank: int
    score: float
    paper_id: str
    title: str
    journal: str | None = None
    year: str | None = None
    text: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]


@app.get("/search_cd73", response_model=SearchResponse)
def search_cd73(q: str = Query(..., description="検索クエリ"), top_k: int = Query(5, ge=1, le=20)):
    q_vec = vectorizer.transform([q])
    sims = cosine_similarity(q_vec, X).ravel()
    idxs = np.argsort(sims)[::-1][:top_k]

    results: List[SearchResult] = []
    for i, idx in enumerate(idxs, start=1):
        c = chunks[idx]
        score = float(sims[idx])
        paper_id = (
            str(c.get("paper_id"))
            if "paper_id" in c
            else str(c.get("pmid")) if "pmid" in c else str(c.get("id", idx))
        )
        m = meta.get(paper_id, {})
        results.append(
            SearchResult(
                rank=i,
                score=score,
                paper_id=paper_id,
                title=m.get("title", "(タイトル不明)"),
                journal=m.get("journal"),
                year=str(m.get("year", "")),
                text=str(c.get("text", "")),
            )
        )
    return SearchResponse(query=q, results=results)

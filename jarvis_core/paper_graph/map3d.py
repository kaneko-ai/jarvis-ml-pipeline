"""3D map generation with optional embedding backends."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Map3DResult:
    points: list[dict]
    config: dict
    warnings: list[dict]


def build_map_points(
    *,
    center_paper: dict,
    neighbor_papers: list[dict],
    k_neighbors: int,
    seed: int,
) -> Map3DResult:
    papers = [center_paper] + neighbor_papers[:k_neighbors]
    texts = [_paper_text(p) for p in papers]
    vectors, method, warnings = _embed_texts(texts, seed=seed)
    coords = _reduce_to_3d(vectors, seed=seed)
    if len(coords) > 0:
        coords = coords - coords[0]

    points: list[dict] = []
    for idx, (paper, coord) in enumerate(zip(papers, coords.tolist(), strict=False)):
        distance = float(np.linalg.norm(np.asarray(coord)))
        points.append(
            {
                "paper_id": _paper_id(paper),
                "title": paper.get("title", ""),
                "year": paper.get("year"),
                "x": float(coord[0]),
                "y": float(coord[1]),
                "z": float(coord[2]),
                "score": float(paper.get("citationCount", 0)),
                "cluster_id": 0,
                "distance_to_center": distance,
            }
        )

    return Map3DResult(
        points=points,
        config={"embedding_method": method, "seed": seed},
        warnings=warnings,
    )


def _paper_text(paper: dict) -> str:
    return " ".join(
        [
            str(paper.get("title", "")),
            str(paper.get("abstract", "")),
            str(paper.get("venue", "")),
        ]
    ).strip()


def _paper_id(paper: dict) -> str:
    ext = paper.get("externalIds") or {}
    if isinstance(ext, dict):
        if ext.get("DOI"):
            return f"doi:{ext['DOI']}"
        if ext.get("ArXiv"):
            return f"arxiv:{ext['ArXiv']}"
        if ext.get("PubMed"):
            return f"pmid:{ext['PubMed']}"
    return str(paper.get("paperId") or paper.get("title") or "unknown")


def _embed_texts(texts: list[str], *, seed: int) -> tuple[np.ndarray, str, list[dict]]:
    warnings: list[dict] = []
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

        model = SentenceTransformer("all-MiniLM-L6-v2")
        vectors = model.encode(texts, show_progress_bar=False)
        return np.asarray(vectors, dtype=float), "sentence-transformers", warnings
    except Exception as exc:
        warnings.append(
            {
                "code": "EMBEDDING_SENTENCE_TRANSFORMERS_UNAVAILABLE",
                "msg": f"sentence-transformers unavailable: {exc}",
                "severity": "warning",
            }
        )

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-not-found]

        vectorizer = TfidfVectorizer(max_features=512)
        matrix = vectorizer.fit_transform(texts)
        return matrix.toarray().astype(float), "tfidf", warnings
    except Exception as exc:
        warnings.append(
            {
                "code": "EMBEDDING_FALLBACK_LOW_CONFIDENCE",
                "msg": f"tfidf unavailable ({exc}). Using hash fallback.",
                "severity": "warning",
            }
        )

    dim = 64
    rows = []
    for text in texts:
        row = np.zeros(dim, dtype=float)
        for token in text.lower().split():
            row[hash(token) % dim] += 1.0
        rows.append(row)
    return np.vstack(rows), "hash-fallback", warnings


def _reduce_to_3d(vectors: np.ndarray, *, seed: int) -> np.ndarray:
    if vectors.size == 0:
        return np.zeros((0, 3), dtype=float)
    if vectors.shape[0] == 1:
        return np.zeros((1, 3), dtype=float)
    try:
        from sklearn.decomposition import PCA  # type: ignore[import-not-found]

        pca = PCA(n_components=3, random_state=seed)
        reduced = pca.fit_transform(vectors)
        return np.asarray(reduced, dtype=float)
    except Exception:
        centered = vectors - vectors.mean(axis=0, keepdims=True)
        u, s, _ = np.linalg.svd(centered, full_matrices=False)
        projected = u[:, :3] * s[:3]
        if projected.shape[1] < 3:
            projected = np.pad(projected, ((0, 0), (0, 3 - projected.shape[1])), mode="constant")
        return np.asarray(projected, dtype=float)

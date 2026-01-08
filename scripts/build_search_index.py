#!/usr/bin/env python3
import argparse
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "this",
    "these",
    "those",
    "we",
    "you",
    "your",
    "our",
    "or",
    "not",
    "can",
    "may",
    "might",
    "also",
    "into",
    "over",
    "under",
    "within",
}


def read_text(path: pathlib.Path) -> str:
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return ""
        parts = []
        for key in ("text", "content", "abstract", "summary"):
            value = data.get(key)
            if isinstance(value, str):
                parts.append(value)
        return "\n".join(parts)
    return path.read_text(encoding="utf-8")


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", "", text)
    return text


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^#\s+(.*)", stripped)
        if match:
            return match.group(1).strip()
        return stripped[:120]
    return fallback


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return [tok for tok in tokens if len(tok) > 2 and tok not in STOPWORDS]


def extract_keywords(text: str, top_k: int = 8) -> List[str]:
    counts: Dict[str, int] = {}
    for token in tokenize(text):
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _count in ranked[:top_k]]


def find_candidate_files(run_dir: pathlib.Path) -> List[pathlib.Path]:
    candidates = []
    preferred_names = {
        "report.md",
        "report.txt",
        "extracted_text.txt",
        "extracted_text.md",
        "abstract.txt",
        "extracted_text.json",
        "report.json",
    }
    for path in run_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name in preferred_names:
            candidates.append(path)
            continue
        if path.name.startswith("extracted_text") and path.suffix.lower() in {".txt", ".md", ".json"}:
            candidates.append(path)
    return candidates


def load_summary(run_dir: pathlib.Path) -> Dict[str, Any]:
    summary_path = run_dir / "summary.json"
    if summary_path.exists():
        try:
            return json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def build_docs(runs_dir: pathlib.Path) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        summary = load_summary(run_dir)
        run_id = summary.get("run_id") or run_id
        candidates = find_candidate_files(run_dir)
        if not candidates:
            continue

        combined_text_parts: List[str] = []
        source_files = []
        for path in candidates:
            content = read_text(path).strip()
            if not content:
                continue
            combined_text_parts.append(content)
            source_files.append(str(path.relative_to(run_dir)))

        if not combined_text_parts:
            continue

        combined_text = "\n\n".join(combined_text_parts)
        clean_text = strip_markdown(combined_text)
        title = extract_title(combined_text, fallback=f"Run {run_id}")
        snippet = " ".join(clean_text.split())
        abstract_snippet = snippet[:320] + ("..." if len(snippet) > 320 else "")
        keywords = extract_keywords(clean_text)
        tokens = tokenize(clean_text)
        doc_id = f"{run_id}:{len(docs)}"
        docs.append(
            {
                "doc_id": doc_id,
                "run_id": run_id,
                "title": title,
                "abstract_snippet": abstract_snippet,
                "keywords": keywords,
                "content": clean_text,
                "source_files": source_files,
                "score_features": {
                    "length_chars": len(clean_text),
                    "length_tokens": len(tokens),
                    "keyword_count": len(keywords),
                    "status": summary.get("status"),
                    "query": summary.get("query"),
                },
            }
        )
    return docs


def write_index(output_path: pathlib.Path, docs: Iterable[Dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc_list = list(docs)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doc_count": len(doc_list),
        "docs": doc_list,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a lightweight search index for serverless search.")
    parser.add_argument(
        "--runs-dir",
        type=pathlib.Path,
        default=pathlib.Path("public/runs"),
        help="Path to the runs directory (default: public/runs)",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("public/search/index.json"),
        help="Output path for the index JSON (default: public/search/index.json)",
    )
    args = parser.parse_args()

    docs = build_docs(args.runs_dir)
    write_index(args.output, docs)
    print(f"Wrote {len(docs)} docs to {args.output}")


if __name__ == "__main__":
    main()

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

from PyPDF2 import PdfReader
from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
import yaml




# ---- PubMed API ヘルパー ---------------------------------


PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def pubmed_esearch(
    query: str,
    date_from: Optional[str],
    date_to: Optional[str],
    max_results: int,
) -> List[str]:
    """PubMed の esearch を叩いて PMID のリストを取得する。"""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
    }

    if date_from or date_to:
        params["datetype"] = "pdat"
        if date_from:
            params["mindate"] = date_from
        if date_to:
            params["maxdate"] = date_to

    print(f"[pubmed_esearch] query={query}")
    resp = requests.get(PUBMED_ESEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    pmids: List[str] = data.get("esearchresult", {}).get("idlist", [])
    print(f"[pubmed_esearch] found {len(pmids)} PMIDs")
    return pmids


def pubmed_esummary(pmids: List[str]) -> List[Dict[str, Any]]:
    """PMID リストに対して esummary を叩き、論文メタデータを取得する。"""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    print(f"[pubmed_esummary] fetching metadata for {len(pmids)} PMIDs")
    resp = requests.get(PUBMED_ESUMMARY_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("result", {})

    records: List[Dict[str, Any]] = []
    for pmid in pmids:
        summary = result.get(pmid)
        if not summary:
            continue

        record = {
            "pmid": pmid,
            "title": summary.get("title"),
            "journal": summary.get("fulljournalname"),
            "pubdate": summary.get("pubdate"),
            "doi_or_elocation": summary.get("elocationid"),
            "authors": [a.get("name") for a in summary.get("authors", [])],
        }
        records.append(record)

    print(f"[pubmed_esummary] collected {len(records)} records")
    return records

# ---- PDF / テキスト抽出 & チャンク化 ----------------------


def pdf_to_text(pdf_path: pathlib.Path) -> str:
    """PDF 1 ファイルからテキストを抽出する（単純版）。"""
    text_parts: List[str] = []
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        print(f"[pdf_to_text] ERROR: failed to open {pdf_path}: {e}", file=sys.stderr)
        return ""

    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception as e:
            print(
                f"[pdf_to_text] WARNING: failed to extract page {i} of {pdf_path}: {e}",
                file=sys.stderr,
            )
            continue
        if page_text.strip():
            text_parts.append(page_text)

    return "\n\n".join(text_parts)


def split_into_chunks(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> List[str]:
    """シンプルな文字数ベースのチャンク分割."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # 次のスタート位置：オーバーラップを残してずらす
        start = end - overlap
        if start < 0:
            start = 0

    return chunks



# ---- 各ステージ -------------------------------------------


def fetch_papers(config: Dict[str, Any]) -> None:
    """PubMed から論文メタデータを取得し、JSON に保存する。"""
    search_conf = config["search"]
    raw_dir = pathlib.Path(config["paths"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    query: str = search_conf["query"]
    date_from: Optional[str] = search_conf.get("date_from")
    date_to: Optional[str] = search_conf.get("date_to")
    max_results: int = int(search_conf.get("max_results", 30))

    print(
        "[fetch_papers] start: "
        f"query={query}, date_from={date_from}, date_to={date_to}, max_results={max_results}"
    )

    try:
        pmids = pubmed_esearch(query, date_from, date_to, max_results)
        summaries = pubmed_esummary(pmids)
    except requests.RequestException as e:
        print(f"[fetch_papers] ERROR: PubMed API request failed: {e}", file=sys.stderr)
        sys.exit(1)

    output = {
        "query": query,
        "date_from": date_from,
        "date_to": date_to,
        "max_results": max_results,
        "num_hit": len(summaries),
        "records": summaries,
    }

    out_path = raw_dir / "pubmed_metadata.json"
    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[fetch_papers] wrote metadata JSON: {out_path}")


def extract_and_chunk(config: Dict[str, Any]) -> None:
    """
    data/raw/... 以下の PDF / TXT からテキストを抽出し、
    チャンクに分割して JSONL として保存する。
    """
    raw_dir = pathlib.Path(config["paths"]["raw_dir"])
    processed_dir = pathlib.Path(config["paths"]["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = processed_dir / "chunks.jsonl"

    all_chunks: List[Dict[str, Any]] = []

    if not raw_dir.exists():
        print(f"[extract_and_chunk] raw_dir not found: {raw_dir}", file=sys.stderr)
    else:
        # 1) PDF ファイル
        for pdf_path in raw_dir.rglob("*.pdf"):
            rel = pdf_path.relative_to(raw_dir)
            print(f"[extract_and_chunk] processing PDF: {rel}")
            text = pdf_to_text(pdf_path)
            if not text.strip():
                print(
                    f"[extract_and_chunk] WARNING: no text extracted from {rel}",
                    file=sys.stderr,
                )
                continue

            chunks = split_into_chunks(text)
            for i, ch in enumerate(chunks):
                all_chunks.append(
                    {
                        "source": str(rel),
                        "source_type": "pdf",
                        "chunk_id": i,
                        "text": ch,
                    }
                )

        # 2) すでにテキスト化された .txt ファイルがあれば、それも対象にする
        for txt_path in raw_dir.rglob("*.txt"):
            rel = txt_path.relative_to(raw_dir)
            # pubmed_metadata.json などは除外
            if rel.name == "pubmed_metadata.json":
                continue

            print(f"[extract_and_chunk] processing TXT: {rel}")
            try:
                text = txt_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = txt_path.read_text(encoding="cp932", errors="ignore")

            chunks = split_into_chunks(text)
            for i, ch in enumerate(chunks):
                all_chunks.append(
                    {
                        "source": str(rel),
                        "source_type": "txt",
                        "chunk_id": i,
                        "text": ch,
                    }
                )

    # 結果の保存
    with chunks_path.open("w", encoding="utf-8") as f:
        for rec in all_chunks:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(
        f"[extract_and_chunk] wrote {len(all_chunks)} chunks "
        f"to {chunks_path}"
    )



def build_index(config: Dict[str, Any]) -> None:
    """
    chunks.jsonl から TF-IDF ベースのインデックスを構築し、
    joblib ファイルとして保存する。
    チャンクが 0 件の場合でも「空インデックス」を保存する。
    """
    processed_dir = pathlib.Path(config["paths"]["processed_dir"])
    index_path = pathlib.Path(config["paths"]["index_path"])
    index_path.parent.mkdir(parents=True, exist_ok=True)

    chunks_path = processed_dir / "chunks.jsonl"
    texts: List[str] = []
    metadata: List[Dict[str, Any]] = []

    if chunks_path.exists():
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

                texts.append(text)
                metadata.append(
                    {
                        "source": rec.get("source"),
                        "source_type": rec.get("source_type"),
                        "chunk_id": rec.get("chunk_id"),
                    }
                )
    else:
        print(
            f"[build_index] WARNING: chunks file not found: {chunks_path}",
            file=sys.stderr,
        )

    if not texts:
        # 空インデックスを保存しておく
        print(
            "[build_index] WARNING: no chunks found to index. "
            "Saving empty index.",
            file=sys.stderr,
        )
        index_obj = {
            "vectorizer": None,
            "matrix": None,
            "metadata": [],
        }
        dump(index_obj, index_path)
        print(f"[build_index] wrote EMPTY index to {index_path}")
        return

    print(f"[build_index] building TF-IDF index for {len(texts)} chunks...")

    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
    )

    matrix = vectorizer.fit_transform(texts)

    index_obj = {
        "vectorizer": vectorizer,
        "matrix": matrix,
        "metadata": metadata,
    }

    dump(index_obj, index_path)
    print(
        f"[build_index] wrote TF-IDF index to {index_path} "
        f"shape={matrix.shape}"
    )




def _extract_year(pubdate: Optional[str]) -> str:
    """PubMed の pubdate 文字列から年だけを取り出す（簡易実装）。"""
    if not pubdate:
        return ""
    for token in str(pubdate).split():
        if token.isdigit() and len(token) == 4:
            return token
    return ""


def generate_report(config: Dict[str, Any]) -> None:
    """pubmed_metadata.json を読み込み、文献一覧の Markdown レポートを生成する。"""
    raw_dir = pathlib.Path(config["paths"]["raw_dir"])
    meta_path = raw_dir / "pubmed_metadata.json"

    report_path = pathlib.Path(config["paths"]["report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not meta_path.exists():
        # fetch_papers がまだ実行されていない場合など
        msg = f"[generate_report] WARNING: metadata JSON not found: {meta_path}"
        print(msg, file=sys.stderr)
        report_path.write_text(
            "# CDH13 文献レポート\n\n"
            f"{msg}\n",
            encoding="utf-8",
        )
        print(f"[generate_report] wrote warning report: {report_path}")
        return

    # メタデータ JSON の読み込み
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    records: List[Dict[str, Any]] = data.get("records", [])
    query = data.get("query")
    date_from = data.get("date_from")
    date_to = data.get("date_to")
    num_hit = data.get("num_hit", len(records))

    # Markdown を組み立てる
    lines: List[str] = []
    lines.append("# CDH13 文献サマリ（自動生成）\n")
    lines.append("## 概要\n")
    lines.append(f"- 検索クエリ: `{query}`")
    lines.append(f"- 期間: {date_from} 〜 {date_to}")
    lines.append(f"- 取得件数 (PubMed): {num_hit}")
    lines.append("")

    lines.append("## 文献一覧\n")
    lines.append("| # | 年 | PMID | タイトル | ジャーナル |")
    lines.append("|---|----|------|----------|------------|")

    for i, rec in enumerate(records, start=1):
        pmid = rec.get("pmid", "")
        title = (rec.get("title") or "").replace("|", "／")
        journal = (rec.get("journal") or "").replace("|", "／")
        year = _extract_year(rec.get("pubdate"))
        # Obsidian で PMID を検索しやすいようにリンク風にする余地もあるが、まずは素直に出す
        lines.append(f"| {i} | {year} | {pmid} | {title} | {journal} |")

    lines.append("")  # 最後に空行

    report_md = "\n".join(lines)
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[generate_report] wrote markdown report: {report_path}")



# ---- パイプライン制御 -----------------------------------


def run_pipeline(config_path: str, dry_run: bool = False) -> None:
    path = pathlib.Path(config_path)
    if not path.exists():
        print(f"Config not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print(f"[run_pipeline] job_name = {config.get('job_name')}")

    if dry_run or config.get("options", {}).get("dry_run", False):
        print("[run_pipeline] dry_run = True → 実処理は行いません。")
        print("loaded config:", config)
        return

    fetch_papers(config)
    extract_and_chunk(config)
    build_index(config)
    generate_report(config)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML 設定ファイルへのパス")
    parser.add_argument("--dry-run", action="store_true", help="実処理せず設定だけ確認する")
    args = parser.parse_args()

    run_pipeline(args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

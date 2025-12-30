import argparse
import json
import os
import pathlib
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from urllib.request import urlretrieve

from PyPDF2 import PdfReader
from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
import yaml

from scripts.source_snapshot import (
    SourceSnapshot,
    build_url,
    compute_file_hash,
    compute_text_hash,
)

# PyMuPDF（pymupdf）は任意。あれば優先的に使う。
try:
    import fitz  # type: ignore
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# ---- NCBI / PMC 関連定数 -----------------------------------

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
OA_SERVICE_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"

# 環境変数から NCBI API キーを読み取る（設定されていなければ None）
NCBI_API_KEY = os.environ.get("NCBI_API_KEY")


# ---- ユーティリティ ----------------------------------------


def load_config(config_path: str) -> Dict[str, Any]:
    path = pathlib.Path(config_path)
    if not path.exists():
        print(f"[load_config] config not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---- PubMed E-utilities ------------------------------------


def pubmed_esearch(
    query: str,
    date_from: Optional[str],
    date_to: Optional[str],
    max_results: int,
    snapshot: Optional[SourceSnapshot] = None,
) -> List[str]:
    """PubMed の esearch を叩いて PMID のリストを取得する。"""
    params: Dict[str, Any] = {
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

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = build_url(PUBMED_ESEARCH_URL, params)
    if snapshot:
        snapshot.start_request(
            url,
            "pubmed_esearch",
            metadata={
                "query": query,
                "date_from": date_from,
                "date_to": date_to,
                "max_results": max_results,
                "params": params,
            },
        )

    print(f"[pubmed_esearch] query={query}")
    try:
        resp = requests.get(PUBMED_ESEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        if snapshot:
            snapshot.finish_request(
                url,
                "pubmed_esearch",
                status="failed",
                http_status=getattr(e.response, "status_code", None),
                error=str(e),
            )
        raise
    data = resp.json()
    if snapshot:
        snapshot.finish_request(
            url,
            "pubmed_esearch",
            status="success",
            http_status=resp.status_code,
            hash_value=compute_text_hash(resp.text),
        )

    ids = data.get("esearchresult", {}).get("idlist", [])
    print(f"[pubmed_esearch] found {len(ids)} PMIDs")
    return ids


def pubmed_esummary(
    pmids: List[str],
    snapshot: Optional[SourceSnapshot] = None,
) -> List[Dict[str, Any]]:
    """PMID リストに対して esummary を叩き、論文メタデータを取得する。"""
    if not pmids:
        return []

    params: Dict[str, Any] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = build_url(PUBMED_ESUMMARY_URL, params)
    if snapshot:
        snapshot.start_request(
            url,
            "pubmed_esummary",
            metadata={"pmids": pmids, "params": params},
        )

    print(f"[pubmed_esummary] fetching metadata for {len(pmids)} PMIDs")
    try:
        resp = requests.get(PUBMED_ESUMMARY_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        if snapshot:
            snapshot.finish_request(
                url,
                "pubmed_esummary",
                status="failed",
                http_status=getattr(e.response, "status_code", None),
                error=str(e),
            )
        raise
    data = resp.json()
    if snapshot:
        snapshot.finish_request(
            url,
            "pubmed_esummary",
            status="success",
            http_status=resp.status_code,
            hash_value=compute_text_hash(resp.text),
        )
    result = data.get("result", {})

    records: List[Dict[str, Any]] = []
    for pmid in pmids:
        summary = result.get(pmid)
        if not summary:
            continue

        # articleids から PMCID を拾う
        pmcid: Optional[str] = None
        for aid in summary.get("articleids", []):
            if aid.get("idtype") == "pmc":
                pmcid = aid.get("value")
                break

        record = {
            "pmid": pmid,
            "pmcid": pmcid,
            "title": summary.get("title"),
            "journal": summary.get("fulljournalname"),
            "pubdate": summary.get("pubdate"),
            "doi_or_elocation": summary.get("elocationid"),
            "authors": [a.get("name") for a in summary.get("authors", [])],
        }
        records.append(record)

    print(f"[pubmed_esummary] collected {len(records)} records")
    return records


# ---- PMC OA PDF ダウンロード --------------------------------


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """ファイル名に使えない文字をざっくり置き換える簡易版。"""
    name = name.strip()
    if not name:
        return "untitled"

    name = name.replace("/", "_").replace("\\", "_")

    cleaned_chars: List[str] = []
    for ch in name:
        if ch.isalnum() or ch in (" ", ".", "_", "-"):
            cleaned_chars.append(ch)
        else:
            cleaned_chars.append("_")

    cleaned = "".join(cleaned_chars).strip()
    if not cleaned:
        cleaned = "untitled"

    return cleaned[:max_len]


def get_oa_pdf_url(
    pmcid: str,
    snapshot: Optional[SourceSnapshot] = None,
) -> Optional[str]:
    """
    PMC Open Access Web Service API を使って、
    指定 PMCID の OA PDF URL (ftp://...) を 1 本取得する。
    OA でない・PDF がない場合は None を返す。
    """
    pmcid_str = str(pmcid).strip()
    if not pmcid_str:
        return None

    params: Dict[str, Any] = {
        "id": pmcid_str,
        "format": "pdf",
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = build_url(OA_SERVICE_URL, params)
    if snapshot:
        snapshot.start_request(url, "pmc_oa_lookup", metadata={"pmcid": pmcid_str, "params": params})

    try:
        resp = requests.get(OA_SERVICE_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        if snapshot:
            snapshot.finish_request(
                url,
                "pmc_oa_lookup",
                status="failed",
                http_status=getattr(e.response, "status_code", None),
                error=str(e),
            )
        print(f"[get_oa_pdf_url] WARNING: request failed for {pmcid_str}: {e}", file=sys.stderr)
        return None

    text = resp.text
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        if snapshot:
            snapshot.finish_request(
                url,
                "pmc_oa_lookup",
                status="failed",
                http_status=resp.status_code,
                error=f"XML parse error: {e}",
            )
        print(f"[get_oa_pdf_url] WARNING: XML parse error for {pmcid_str}: {e}", file=sys.stderr)
        return None

    if snapshot:
        snapshot.finish_request(
            url,
            "pmc_oa_lookup",
            status="success",
            http_status=resp.status_code,
            hash_value=compute_text_hash(text),
        )

    for record in root.findall(".//record"):
        for link in record.findall("link"):
            if link.attrib.get("format") == "pdf":
                href = link.attrib.get("href")
                if href:
                    return href

    return None


def download_pmc_pdfs(
    records: List[Dict[str, Any]],
    raw_dir: pathlib.Path,
    overwrite: bool = False,
    snapshot: Optional[SourceSnapshot] = None,
) -> None:
    """
    esummary 由来の records から PMCID を持つものだけ選び、
    PMC Open Access Web Service API → FTP 経由で PDF を取得し、
    raw_dir/pmc/ に保存する。
    """
    pmc_dir = raw_dir / "pmc"
    pmc_dir.mkdir(parents=True, exist_ok=True)

    tried = 0
    downloaded = 0
    skipped_existing = 0
    skipped_no_oa_pdf = 0
    skipped_error = 0

    for rec in records:
        pmcid = rec.get("pmcid")
        title = rec.get("title") or ""
        if not pmcid:
            continue

        pmcid_str = str(pmcid).strip()
        if not pmcid_str:
            continue

        tried += 1

        pdf_url = get_oa_pdf_url(pmcid_str, snapshot=snapshot)
        if not pdf_url:
            skipped_no_oa_pdf += 1
            continue

        safe_title = sanitize_filename(title) if title else None
        base_name = safe_title or pmcid_str
        pdf_path = pmc_dir / f"{base_name}.pdf"

        if pdf_path.exists() and not overwrite:
            if snapshot:
                snapshot.finish_request(
                    pdf_url,
                    "pmc_pdf",
                    status="skipped",
                    output_path=str(pdf_path),
                    hash_value=compute_file_hash(pdf_path),
                    metadata={"reason": "already_exists"},
                )
            skipped_existing += 1
            continue

        if snapshot:
            snapshot.start_request(
                pdf_url,
                "pmc_pdf",
                metadata={"pmcid": pmcid_str, "title": title},
            )

        print(f"[download_pmc_pdfs] downloading {pmcid_str} → pmc/{pdf_path.name}")
        try:
            urlretrieve(pdf_url, pdf_path)
        except Exception as e:
            if snapshot:
                snapshot.finish_request(
                    pdf_url,
                    "pmc_pdf",
                    status="failed",
                    error=str(e),
                    output_path=str(pdf_path),
                )
            print(
                f"[download_pmc_pdfs] WARNING: failed to download {pmcid_str} "
                f"from {pdf_url}: {e}",
                file=sys.stderr,
            )
            skipped_error += 1
            continue

        if snapshot:
            snapshot.finish_request(
                pdf_url,
                "pmc_pdf",
                status="success",
                output_path=str(pdf_path),
                hash_value=compute_file_hash(pdf_path),
            )

        downloaded += 1

    print(
        "[download_pmc_pdfs] summary: "
        f"tried={tried}, downloaded={downloaded}, "
        f"skipped_existing={skipped_existing}, "
        f"skipped_no_oa_pdf={skipped_no_oa_pdf}, "
        f"skipped_error={skipped_error}"
    )


def fetch_papers(config: Dict[str, Any]) -> None:
    """PubMed から論文メタデータを取得し、JSON と PDF を保存する。"""
    search_conf = config["search"]
    raw_dir = pathlib.Path(config["paths"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    query: str = search_conf["query"]
    date_from: Optional[str] = search_conf.get("date_from")
    date_to: Optional[str] = search_conf.get("date_to")
    max_results: int = int(search_conf.get("max_results", 30))

    overwrite: bool = bool(config.get("options", {}).get("overwrite", False))

    snapshot_path = raw_dir.parent / "snapshot.json"
    snapshot = SourceSnapshot.load_or_create(
        snapshot_path,
        {
            "query": query,
            "date_from": date_from,
            "date_to": date_to,
            "max_results": max_results,
        },
    )

    print(
        "[fetch_papers] start: "
        f"query={query}, date_from={date_from}, date_to={date_to}, max_results={max_results}"
    )

    try:
        pmids = pubmed_esearch(query, date_from, date_to, max_results, snapshot=snapshot)
        records = pubmed_esummary(pmids, snapshot=snapshot)
    except requests.RequestException as e:
        print(f"[fetch_papers] ERROR: PubMed API request failed: {e}", file=sys.stderr)
        sys.exit(1)

    output = {
        "query": query,
        "date_from": date_from,
        "date_to": date_to,
        "max_results": max_results,
        "num_hit": len(records),
        "records": records,
    }

    meta_path = raw_dir / "pubmed_metadata.json"
    meta_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[fetch_papers] wrote metadata JSON: {meta_path}")

    download_pmc_pdfs(records, raw_dir, overwrite=overwrite, snapshot=snapshot)


# ---- PDF / テキスト → チャンク ------------------------------


def pdf_to_text(pdf_path: pathlib.Path) -> str:
    """
    PDF 1 ファイルからテキストを抽出する。
    PyMuPDF が入っていればそちらを優先し、無ければ PyPDF2 を使う。
    """
    # 1. PyMuPDF 優先（高速）
    if HAS_PYMUPDF:
        text_parts: List[str] = []
        try:
            with fitz.open(pdf_path) as doc:  # type: ignore
                for page in doc:
                    text_parts.append(page.get_text())
        except Exception as e:
            print(f"[pdf_to_text] ERROR (PyMuPDF) {pdf_path}: {e}", file=sys.stderr)
            return ""
        return "\n\n".join(text_parts)

    # 2. フォールバック: PyPDF2
    text_parts: List[str] = []
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        print(f"[pdf_to_text] ERROR (PyPDF2) failed to open {pdf_path}: {e}", file=sys.stderr)
        return ""

    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception as e:
            print(
                f"[pdf_to_text] WARNING (PyPDF2) failed to extract page {i} of {pdf_path}: {e}",
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
        start = end - overlap
        if start < 0:
            start = 0

    return chunks


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
        # PDF ファイル
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

        # すでにテキスト化された .txt ファイルも対象
        for txt_path in raw_dir.rglob("*.txt"):
            rel = txt_path.relative_to(raw_dir)
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

    with chunks_path.open("w", encoding="utf-8") as f:
        for rec in all_chunks:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(
        f"[extract_and_chunk] wrote {len(all_chunks)} chunks "
        f"to {chunks_path}"
    )


# ---- TF-IDF インデックス構築 -------------------------------


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


# ---- レポート生成 -------------------------------------------


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
        msg = f"[generate_report] WARNING: metadata JSON not found: {meta_path}"
        print(msg, file=sys.stderr)
        report_path.write_text(
            "# CDH13 文献レポート\n\n"
            f"{msg}\n",
            encoding="utf-8",
        )
        print(f"[generate_report] wrote warning report: {report_path}")
        return

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    records: List[Dict[str, Any]] = data.get("records", [])
    query = data.get("query")
    date_from = data.get("date_from")
    date_to = data.get("date_to")
    num_hit = data.get("num_hit", len(records))

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
        lines.append(f"| {i} | {year} | {pmid} | {title} | {journal} |")

    lines.append("")

    report_md = "\n".join(lines)
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[generate_report] wrote markdown report: {report_path}")


# ---- パイプライン本体 --------------------------------------


def run_pipeline(config_path: str, dry_run: bool = False) -> None:
    config = load_config(config_path)
    job_name = config.get("job_name", pathlib.Path(config_path).stem)
    print(f"[run_pipeline] job_name = {job_name}")

    effective_dry_run = dry_run or bool(config.get("options", {}).get("dry_run", False))
    if effective_dry_run:
        print("[run_pipeline] dry_run = True → 実処理は行いません。")
        print(f"loaded config: {config}")
        return

    fetch_papers(config)
    extract_and_chunk(config)
    build_index(config)
    generate_report(config)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="論文取得・チャンク・インデックス構築パイプライン",
    )
    parser.add_argument("config", help="YAML 設定ファイルへのパス")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="設定の読み込みとログ出力のみ行い、実処理は実行しない",
    )
    args = parser.parse_args()

    run_pipeline(args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

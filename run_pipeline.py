import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

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
    """PDF→テキスト→チャンク（今はダミー）。"""
    processed_dir = pathlib.Path(config["paths"]["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)
    print(f"[extract_and_chunk] would process PDFs into: {processed_dir}")


def build_index(config: Dict[str, Any]) -> None:
    """FAISS index 構築（今はダミー）。"""
    index_path = pathlib.Path(config["paths"]["index_path"])
    index_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[build_index] would build index at: {index_path}")


def generate_report(config: Dict[str, Any]) -> None:
    """レポート生成（今はダミー）。"""
    report_path = pathlib.Path(config["paths"]["report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("# Dummy report\n\nTODO: 実装\n", encoding="utf-8")
    print(f"[generate_report] wrote dummy report: {report_path}")


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

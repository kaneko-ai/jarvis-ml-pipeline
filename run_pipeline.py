import argparse
import pathlib
import sys
from typing import Any, Dict

import yaml


# ---- 各ステージのダミー実装 -----------------------------

def fetch_papers(config: Dict[str, Any]) -> None:
    """文献取得ステージ（今はダミー）。"""
    raw_dir = pathlib.Path(config["paths"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"[fetch_papers] would fetch papers into: {raw_dir}")


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

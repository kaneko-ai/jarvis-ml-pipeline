#!/usr/bin/env python
"""
JARVIS MVP Pipeline CLI

Phase B: 一本道MVP実行

使い方:
    python -m jarvis_core.pipelines.run_mvp --query "CD73 immunotherapy"
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jarvis_core.pipelines.mvp_pipeline import (
    Constraints,
    MVPPipeline,
    PipelineInput,
    Reproducibility,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def main():
    parser = argparse.ArgumentParser(description="JARVIS MVP Pipeline")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Search query (e.g., 'CD73 immunotherapy')",
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="Literature survey",
        help="Research goal",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=10,
        help="Maximum papers to retrieve",
    )
    parser.add_argument(
        "--runs-dir",
        type=str,
        default="runs",
        help="Output directory",
    )

    args = parser.parse_args()

    # 入力を構築
    input = PipelineInput(
        goal=args.goal,
        query=args.query,
        constraints=Constraints(
            oa_only=True,
            max_papers=args.max_papers,
        ),
        reproducibility=Reproducibility(
            seed=0,
            model="local",
            pipeline_version="mvp-v1",
        ),
    )

    # パイプライン実行
    pipeline = MVPPipeline(runs_dir=args.runs_dir)
    bundle = pipeline.run(input)

    # 結果表示
    print()
    print("=" * 60)
    print(f"Run ID: {bundle.run_id}")
    print(f"Output: {args.runs_dir}/{bundle.run_id}/")
    print("=" * 60)
    print(f"Papers: {len(bundle.papers)}")
    print(f"Claims: {len(bundle.claims)}")
    print(f"Evidence: {len(bundle.evidence)}")
    print(f"Warnings: {len(bundle.warnings)}")
    print()

    # Bundle内容確認
    output_dir = Path(args.runs_dir) / bundle.run_id
    print("Generated files:")
    for f in output_dir.iterdir():
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
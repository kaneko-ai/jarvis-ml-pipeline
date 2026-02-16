"""Runner for `jarvis market propose`."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.bundle import BundleAssembler

from .propose import generate_proposals, load_input_assets, proposals_deck_md


def run_market_propose(
    *,
    input_run: str,
    market_data_dir: str | None,
    out: str,
    out_run: str,
) -> dict:
    run_id = _resolve_run_id(out_run)
    run_dir = Path(out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    market_dir = run_dir / "market"
    market_dir.mkdir(parents=True, exist_ok=True)
    assembler = BundleAssembler(run_dir)

    fail_reasons: list[dict] = []
    input_run_dir = Path(out) / input_run
    if not input_run_dir.exists():
        fail_reasons.append(
            {
                "code": "INPUT_INVALID",
                "msg": f"input run does not exist: {input_run}",
                "severity": "error",
            }
        )
        assets = {"papers": [], "market_data": []}
        proposals = []
    else:
        assets = load_input_assets(
            run_dir=input_run_dir,
            market_data_dir=Path(market_data_dir) if market_data_dir else None,
        )
        proposals = generate_proposals(assets)
        if not proposals:
            fail_reasons.append(
                {
                    "code": "MARKET_PROPOSAL_EMPTY",
                    "msg": "No proposals generated.",
                    "severity": "warning",
                }
            )

    (market_dir / "proposals.json").write_text(
        json.dumps(proposals, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (market_dir / "proposals_deck.md").write_text(proposals_deck_md(proposals), encoding="utf-8")

    gate_passed = len(proposals) > 0 and not _has_fatal(fail_reasons)
    artifacts = {
        "papers": [],
        "claims": [],
        "evidence": [],
        "scores": {"features": {"proposal_count": len(proposals)}, "rankings": []},
        "answer": f"Generated {len(proposals)} market proposals.",
        "citations": [],
        "warnings": [],
    }
    assembler.build(
        _context(run_id=run_id, goal="market propose", pipeline="market.propose"),
        artifacts,
        quality_report={"gate_passed": gate_passed, "fail_reasons": fail_reasons},
    )
    return _load_result(run_dir, run_id)


def _resolve_run_id(out_run: str) -> str:
    if out_run and out_run != "auto":
        return out_run
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{now}_{uuid.uuid4().hex[:8]}"


def _context(*, run_id: str, goal: str, pipeline: str) -> dict:
    return {
        "run_id": run_id,
        "task_id": run_id,
        "goal": goal,
        "query": goal,
        "pipeline": pipeline,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": 42,
        "model": "feature-runner",
    }


def _has_fatal(fail_reasons: list[dict]) -> bool:
    return any(
        str(reason.get("code", "")).upper() in BundleAssembler.FATAL_FAIL_CODES
        for reason in fail_reasons
    )


def _load_result(run_dir: Path, run_id: str) -> dict:
    result_path = run_dir / "result.json"
    status = "needs_retry"
    if result_path.exists():
        try:
            status = str(
                json.loads(result_path.read_text(encoding="utf-8")).get("status", "needs_retry")
            )
        except Exception:
            status = "needs_retry"
    return {"run_id": run_id, "run_dir": str(run_dir), "status": status}

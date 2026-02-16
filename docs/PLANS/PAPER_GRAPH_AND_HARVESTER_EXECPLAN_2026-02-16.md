> Authority: SPEC (Level 2, Binding)
> Date: 2026-02-16
> Alignment: docs/MASTER_SPEC.md v1.2

# PAPER_GRAPH + MAP3D + HARVEST + RADAR + COLLECT+DRIVE + MARKET

## Scope
- Single entrypoint: `jarvis_cli.py`
- New command families:
  - `papers tree`
  - `papers map3d`
  - `harvest watch`
  - `harvest work`
  - `radar run`
  - `collect papers`
  - `collect drive-sync`
  - `market propose`
- All commands must generate bundle required files via `BundleAssembler.build(...)`.

## Contract Rules
- Required artifacts: same 10 files defined by bundle contract.
- Extra outputs must be placed under `logs/runs/{run_id}/<feature_dir>/`.
- Status vocabulary:
  - `success`
  - `failed`
  - `needs_retry`

## Harvest Queue Persistence
- Queue path: `logs/runs/{run_id}/harvest/queue.jsonl`
- Persistence scope: **run-scoped**
- `watch` and `work` should continue with the same `run_id`.

## Offline Policy
- `--offline` must not crash command execution.
- If outputs are incomplete under offline conditions:
  - mark `status` as `failed` or `needs_retry`
  - write detailed reasons to `warnings.jsonl`, `eval_summary.json`, `report.md`

## Deliverables by Feature

### papers tree
- `paper_graph/tree/graph.json`
- `paper_graph/tree/tree.md`
- `paper_graph/tree/tree.mermaid.md`
- `paper_graph/tree/summary.md`

### papers map3d
- `paper_graph/map3d/map_points.json`
- `paper_graph/map3d/map.md`
- `paper_graph/map3d/map.html` (optional if plotly is available)

### harvest
- `harvest/queue.jsonl`
- `harvest/items/`
- `harvest/stats.json`
- `harvest/report.md`

### radar
- `radar/radar_findings.json`
- `radar/upgrade_proposals.md`

### collect
- `collector/papers.json`
- `collector/pdfs/`
- `collector/bibtex/`
- `collector/report.md`

### market
- `market/proposals.json`
- `market/proposals_deck.md`

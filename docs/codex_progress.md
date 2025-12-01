# Codex Progress - Jarvis Core

## Vision Summary
- Jarvis Core turns open-ended research and career questions into structured tasks and orchestrates the right agents to execute them.
- It converts natural language goals into actionable subtasks with clear inputs, constraints, and priorities.
- It routes work to domain agents (literature, thesis writing, job hunting, news) via a registry and lightweight execution engine.
- It validates outputs, triggers retries when results are incomplete or malformed, and keeps decisions auditable.
- It centralizes logging and progress so humans can trace when, what, and which agent acted.
- It favors small, iterative improvements while preserving public interfaces and avoiding hardcoded secrets.

## Milestones (M1–M4) and Status
- **M1: Minimal Jarvis Core (CLI base)** — Status: 完了
- **M2: External Tool Integration Skeleton** — Status: 進行中
- **M3: Self-Evaluation & Retry** — Status: 進行中
- **M4: UI Layer Connectivity (antigravity/MyGPT)** — Status: 未着手

## Subtasks
### M1: Minimal Jarvis Core
- [x] Task model defined with id/category/goal/inputs/constraints/priority/status/history
- [x] Minimal planner that expands user goals into ordered subtasks (hardcoded per category acceptable)
- [x] Execution engine that sequences subtasks and invokes dummy agents
- [x] Simple CLI entry (e.g., `python -m jarvis_core.cli`) demonstrating end-to-end flow

### M2: Agent Registry / Router & Tool Interfaces
- [x] Config-driven agent registry (YAML/TOML) mapping categories to agents/tools
- [x] Router that selects agents based on task metadata and registry configuration
- [x] Interface stubs for literature tools (paper-fetcher, mygpt-paper-analyzer) and job-hunting utilities
- [x] Basic configuration loader with environment override support

### M3: Self-Evaluation & Retry Logic
- [x] Validation functions for common outputs (JSON schema, file existence checks, minimal sanity rules)
- [x] Retry policy with capped attempts and error-type differentiation
- [x] Mechanism to enqueue corrective subtasks when validation fails
- [x] Logging of evaluation outcomes and retry decisions

### M4: UI / API Connectivity
- [x] FastAPI ベースの `/jarvis` API を追加し、uvicorn で起動可能 (例: `uvicorn jarvis_core.api:app --reload`)
- [x] 文献サーベイエージェント API (`POST /literature-survey`) を追加
- [ ] HTTP or CLI wrapper callable from antigravity actions
- [ ] Task ID–based progress query endpoint or CLI command
- [ ] Auth/config plumbing separated from business logic (no hardcoded secrets)
- [ ] Documentation for integrating with MyGPT or future dashboard

FastAPI 起動例: `uvicorn jarvis_core.api:app --reload`  
文献サーベイ API 呼び出し例:

```bash
curl -X POST "http://localhost:8000/literature-survey" \
  -H "Content-Type: application/json" \
  -d '{"topic": "免疫チェックポイント阻害", "max_papers": 5, "language": "ja"}'

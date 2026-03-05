# HANDOVER_v15.md - JARVIS ML Pipeline

> Date: 2026-03-05 23:30 JST
> Authors: Claude Opus 4.6 + Codex GPT-5.3 + kaneko yu
> Previous: HANDOVER_v14.md

## Status Summary

All Phase 0, 1, 2, 3 tasks are COMPLETE.

### Phase 2 (Daily Digest) - COMPLETE
- P2-1: Daily Digest first run verified (5 keywords, 49 papers)
- P2-2: Windows Task Scheduler set (daily 07:00)
- P2-3: Digest-to-Obsidian export (digest-to-obsidian.js)

### Phase 3 (Data Management) - COMPLETE
- P3-1: SQLite papers table + CRUD (papers-repository.js) - 9 exported functions
- P3-2: Dedup enhancement (titleSimilarity in pipeline.js, existing)
- P3-3: PDF archiver (pdf-archiver.js) - Unpaywall + direct download
- P3-4: Zotero sync (zotero-sync.js) - Zotero Web API v3
- P3-5: ChromaDB bridge (chroma-bridge.js) - Python subprocess bridge
- Pipeline now saves papers to SQLite automatically
- Daily Digest now exports to Obsidian automatically

### Quality Improvements
- Gemini rate limit: concurrency 1, delay 4500ms (safe under 15 RPM)
- API 429 retry: PubMed 350ms delay + retry, S2 1500ms + retry
- Pipeline DB save: papers inserted after each pipeline run
- CI/CD: GitHub Actions workflow (.github/workflows/test.yml)
- Tests: 32+ passing (npm test)

### Code Quality (Reviewer Findings - All Addressed)
- critical: Gemini RPM risk - FIXED (concurrency 1, delay 4500ms)
- warning: pipeline not saving to DB - FIXED (insertPapers added)
- warning: PubMed/S2 rate limits - FIXED (delay + 429 retry)
- warning: GEMINI_API_KEY guard - addressed in summarizeBatch
- warning: SQLite BUSY - low risk with better-sqlite3 sync mode

## Architecture

### agent-web/src/db/
- database.js: sessions + messages tables
- papers-repository.js: papers table CRUD (9 functions)
- chroma-bridge.js: Python ChromaDB subprocess bridge
- create-papers-table.js: migration script

### agent-web/src/skills/
- daily-digest.js: automated literature digest
- digest-to-obsidian.js: Obsidian vault export
- pdf-archiver.js: PDF download + archive
- zotero-sync.js: Zotero library sync
- skill-registry.js: skill management

### agent-web/src/routes/
- pipeline.js: 7-step SSE pipeline + DB save + PDF archive
- digest.js: Daily Digest API endpoints
- chat.js, sessions.js, models.js, monitor.js, skills.js, mcp.js, usage.js

### agent-web/src/llm/
- paper-search.js: PubMed + Semantic Scholar + OpenAlex (with 429 retry)
- gemini-summarizer.js: Gemini 2.0 Flash (rate limited)
- parallel-runner.js, copilot-bridge.js, python-bridge.js

## Tests: 32+ passing
- database.test.js: 5 CRUD tests
- api.test.js: 5 endpoint tests
- digest.test.js: 11+ module + CRUD + integration tests
- pipeline.test.js: 2 tests
- monitor.test.js: 2 tests
- gemini-summarizer.test.js: 3 tests
- parallel-runner.test.js: 4 tests

## Next Steps (Future)
- P3-6: LightRAG integration
- Full E2E pipeline test via browser
- Multi-turn conversation memory (H-3)
- Text appearance animations (Phase 2 UI)
- Research compiler (auto-textbook generation)

## Environment
- Windows 11, Node v24.13.1, Python 3.11.9
- Project: C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline
- Ports: 3000 (Express), 4141 (Copilot API)
- LLM: gemini-2.0-flash (default), claude-sonnet-4.6 (chat)

## Smoke Test
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline\agent-web" npm test npm run dev

Open http://localhost:3000 -> Pipeline tab -> Run pipeline or Daily Digest

\# HANDOVER\_v10.md — JARVIS Research OS + Agent-Web Handover v10



\*\*Date\*\*: 2026-03-04

\*\*Previous\*\*: HANDOVER\_v9.md (2026-03-04, commit 43342c25)

\*\*Repository\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline

\*\*Branch\*\*: main

\*\*Latest pushed commit\*\*: 38587e79 — feat: Agent-Web v1.0.0 (Express+Copilot+JARVIS chat, 10 tests pass)

\*\*Related repo\*\*: https://github.com/kaneko-ai/zotero-doi-importer

\*\*Expansion plan\*\*: JARVIS\_EXPANSION\_PLAN\_v1.md (in repo root)



\*\*Purpose\*\*: Any AI or developer reading this document can continue implementation with zero additional questions. Covers both the Python CLI backend (v2.0.0) and the Node.js Agent-Web frontend (all categories complete, committed to Git).



---



\## 1. Project Overview



JARVIS Research OS automates Systematic Literature Reviews. The Python CLI backend (22 commands) handles: paper search, dedup, evidence grading, scoring, LLM Japanese summary, Obsidian notes, Zotero sync, PRISMA diagrams, BibTeX output, citation network visualization, ChromaDB semantic search, LangGraph orchestration, and deep research.



The Agent-Web is a Node.js/Express dark-theme SPA at `agent-web/` that provides a browser-based chat interface to all JARVIS capabilities. It connects to GitHub Copilot via copilot-api (localhost:4141) for multi-model LLM access and falls back to Gemini via LiteLLM Python bridge.



\*\*User\*\*: Graduate student (beginner programmer, Windows)

\*\*Use cases\*\*: PD-1 immunotherapy, spermidine, immunosenescence/autophagy research



---



\## 2. Development Environment (2026-03-04)



| Item | Value |

|------|-------|

| OS | Windows 11 |

| Shell | PowerShell 5.1 |

| Python | 3.11.9 (venv shows cp311) |

| Node.js | v24.13.1 |

| npm | (bundled with Node v24) |

| Project path | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| Agent-Web path | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web` |

| venv | `.venv` (project root) |

| venv activate | `.\\.venv\\Scripts\\Activate.ps1` |

| Python exe | `.venv\\Scripts\\python.exe` |

| Obsidian Vault | `H:\\マイドライブ\\obsidian-vault` |

| Logs/Exports | `H:\\マイドライブ\\jarvis-data\\` |

| C: free | ~45 GB / 460 GB |

| H: drive | Google Drive 2TB (personal, kanekiti1125@gmail.com) |

| G: drive | Google Drive 100GB (student, NOT used by JARVIS) |

| GPU | None (Intel Iris Plus Graphics) |

| RAM | 16 GB LPDDR4x |

| CPU | Intel i7-1065G7 (4C/8T) |



\### 2.1 Environment Variables (.env at project root, gitignored)



Copy

GEMINI\_API\_KEY=<39-char key> LLM\_PROVIDER=gemini ZOTERO\_API\_KEY=<issued 2026-03-02> ZOTERO\_USER\_ID=16956010 OPENAI\_API\_KEY= DEEPSEEK\_API\_KEY= LLM\_MODEL=gemini/gemini-2.0-flash DATALAB\_API\_KEY=<present but 403>





\### 2.2 Python Packages (.venv)



v1.0.0: jarvis-research-os, google-genai, python-dotenv, rank-bm25, sentence-transformers (MiniLM-L6-v2), pyzotero, requests, streamlit, rapidfuzz, scikit-learn, pyyaml, scrapling, beautifulsoup4. D1: litellm, openai, pydantic-ai, instructor, tiktoken, aiohttp. D3: chromadb, lightrag-hku, pymupdf4llm. D4: langgraph. D6: pytest, pytest-timeout.



\### 2.3 Node.js Packages (agent-web/package.json)



express (v5), better-sqlite3, dotenv, js-yaml, eventsource-parser, uuid, copilot-api. Total ~130+ packages installed via npm.



\### 2.4 AI CLI Tools



| Tool | Version | Auth | Plan | Models (usable) |

|------|---------|------|------|-----------------|

| Codex CLI | 0.106.0 | ChatGPT Plus | $20/mo | GPT-5.3-Codex, GPT-5-mini, GPT-4.1 |

| Copilot CLI | 0.0.420 | Education Pro | Free | See §2.5 |

| copilot-api (npm) | latest | Education Pro | Free | Same as Copilot CLI |



\### 2.5 GitHub Copilot Model Availability (Education Pro)



Usable (tier: "pro"): claude-sonnet-4.6, claude-sonnet-4.5, gpt-4.1, gpt-4.1-mini, gpt-4o, o4-mini, gemini-2.0-flash, gemini-2.5-pro.



Restricted (tier: "pro+", return 400): claude-opus-4.6, gpt-5.1, gpt-5.2-codex, gemini-3-pro-preview.



Default model for Agent-Web: \*\*claude-sonnet-4.6\*\* (confirmed working).



\### 2.6 NOT Installed / Unusable



| Component | Reason |

|-----------|--------|

| Ollama | Not installed, use\_llm=false workaround |

| Crawl4AI | Playwright+Chromium too heavy; Jina Reader instead |

| Datalab.to MinerU API | 403 (paid); PyMuPDF4LLM fallback works |

| GPT-Researcher | Requires paid OpenAI API key |

| openai-agents-python | Requires paid OpenAI API key |



Policy: \*\*Free tier only\*\* for all APIs.



---



\## 3. Commit History



38587e79 feat: Agent-Web v1.0.0 (Express+Copilot+JARVIS chat, 10 tests pass) ← LATEST 43342c25 docs: HANDOVER\_v9.md - Agent-Web integration complete through Cat 8 edd4d0cf (tag: v2.0.0) D7: v2.0.0 release - 22/22 smoke test passed, E2E pipeline verified d4fd4483 D6: pytest suite 50/50 passed, Streamlit 5-page dashboard, HANDOVER\_v8.md, README v1.3.0 0d5d7999 (tag: v1.3.0) D5: Obsidian/storage H: migration, citation network, 22 CLI commands 8b9781f3 docs: HANDOVER\_v7.md 6f9479ec D4: LangGraph orchestrator, deep-research CLI, skills execute 8da82646 (tag: v1.2.0) D3: ChromaDB PaperStore, LightRAG engine, PDF-to-Markdown 40fff89f (tag: v1.1.0) D2: browse.py Jina fallback + authors dedup, MCP handlers fb63f6fe D1: LiteLLM + Instructor + PydanticAI





---



\## 4. Task Completion Map



\### Python CLI Backend: ALL DONE



| Day | Phase | Status |

|-----|-------|--------|

| D1 | AI Tools + LLM Foundation | DONE |

| D2 | Scraping/Browse Enhancement | DONE |

| D3 | RAG/Vector DB/PDF | DONE |

| D4 | Agent/Orchestrator | DONE |

| D5 | Knowledge Management | DONE |

| D6 | Test/QA/Docs | DONE (50/50 pytest, Streamlit, README) |

| D7 | Final Smoke Test + v2.0.0 | DONE (tag: v2.0.0) |



\### Agent-Web: ALL CATEGORIES DONE, COMMITTED TO GIT



| Category | Content | Status |

|----------|---------|--------|

| Cat 1 | Foundation: Express v5, SQLite, dark-theme SPA | DONE |

| Cat 2 | Python LLM Bridge: llm\_caller.py → LiteLLM → Gemini | DONE |

| Cat 3 | JARVIS CLI Tools: search, semantic-search, browse, evidence | DONE |

| Cat 4 | Skills Migration: 8 built-in skills, /api/skills | DONE |

| Cat 5 | MCP Integration: 5 servers, 15 tools, /api/mcp/servers | DONE |

| Cat 6 | Copilot SDK: copilot-bridge.js via copilot-api proxy | DONE |

| Cat 7 | Model Tier + Usage: Pro/Pro+ display, usage bar | DONE |

| Cat 8 | browse\_url + Error Handling: URL detection → JARVIS browse → LLM | DONE |

| Cat 9 | Testing + README: 10 tests (database 5 + api 5), README.md | DONE |

| Cat 10 | Git Commit: agent-web/ committed and pushed | DONE |



\### v10 Session Work (AW-1 through AW-5)



| Task | Content | Status | Details |

|------|---------|--------|---------|

| AW-1 | browse\_url browser test | DONE | URL detection moved outside isResearchQuery block; arxiv paper summarized correctly |

| AW-2 | Error handling hardening | DONE | copilot-bridge.js: 60s/120s fetch timeout, system prompt UTF-8 fix; chat.js: browse failure → warning + LLM-only fallback, Copilot timeout → Japanese error message |

| AW-3 | agent-web/README.md | DONE | Architecture, API list, model table, file structure |

| AW-4 | Automated tests | DONE | database.test.js (5 CRUD tests) + api.test.js (5 endpoint tests), all pass via node --test |

| AW-5 | Git commit agent-web | DONE | 38587e79, 27 files, 5302 insertions |



---



\## 5. Agent-Web Architecture



\### 5.1 Overview



Browser (localhost:3000) ↓ HTTP/SSE Express v5 (agent-web/src/server.js) ├── /api/chat/stream → copilot-bridge.js → copilot-api (:4141) → GitHub Copilot │ → python-bridge.js → llm\_caller.py → LiteLLM → Gemini (fallback) ├── /api/sessions → better-sqlite3 (chat-history.db) ├── /api/models → copilot-api /v1/models + static fallback list ├── /api/usage → copilot-api /usage endpoint ├── /api/skills → skill-registry.js (8 skills) ├── /api/mcp/servers → mcp-status.js (5 servers, 15 tools) └── /api/health → {"status":"ok","version":"1.0.0"}





\### 5.2 File Structure (agent-web/) — committed at 38587e79



agent-web/ ├── .gitignore # node\_modules, chat-history.db\*, \*.log, .env ├── package.json # Express v5, better-sqlite3, copilot-api, etc. ├── package-lock.json ├── start.ps1 # Starts copilot-api (4141) + Express (3000) ├── README.md # Architecture, API list, model table ├── src/ │ ├── server.js # Express entry point, port 3000 │ ├── routes/ │ │ ├── chat.js # SSE streaming, URL detection (always), research mode, Copilot+LiteLLM │ │ ├── sessions.js # CRUD for chat sessions │ │ ├── models.js # Model list with pro/pro+/local tiers │ │ ├── skills.js # /api/skills endpoint │ │ ├── mcp.js # /api/mcp/servers endpoint │ │ └── usage.js # /api/usage (Copilot quota) │ ├── db/database.js # better-sqlite3 CRUD (sessions + messages tables) │ ├── llm/ │ │ ├── copilot-bridge.js # Copilot API client (60s timeout, 120s for streaming) │ │ ├── python-bridge.js # Spawns .venv Python for LiteLLM fallback │ │ ├── llm\_caller.py # Python: reads JSON stdin, calls litellm completion │ │ └── jarvis-tools.js # JARVIS CLI wrapper (search, browse, evidence, 120s timeout) │ ├── skills/skill-registry.js │ └── mcp-bridge/mcp-status.js ├── public/ │ ├── index.html # Dark-theme SPA shell │ ├── css/styles.css # RPG dark theme │ └── js/app.js # ES module: SSE, model selector, usage bar, sessions ├── tests/ │ ├── database.test.js # 5 SQLite CRUD tests (node --test) │ └── api.test.js # 5 API endpoint tests (node --test, requires running server) ├── chat-history.db # SQLite (gitignored) └── node\_modules/ # (gitignored)





\### 5.3 Key Behaviors (v10 updates marked with ★)



\*\*Chat flow\*\*: User types message → POST /api/chat/stream → SSE connection opened → ★ URL detection (always, regardless of research keywords) → if URL found, jarvis browse → content prepended to prompt → research keyword detection → if matched, semantic\_search → results prepended → model called via copilot-bridge.js (streaming SSE) → response streamed as delta events → conversation saved to SQLite → done event sent.



\*\*★ URL detection fix (AW-1)\*\*: Moved URL regex matching outside the `isResearchQuery()` block. Previously, browse\_url only fired when the message also contained research keywords. Now any message with a URL triggers browse automatically.



\*\*★ Browse failure handling (AW-2)\*\*: If browse\_url fails (timeout, empty result, network error), a `warning` SSE event is sent with a Japanese message ("URLの取得に失敗しました。LLMのみで回答します。"), and the LLM generates a response without the URL content.



\*\*★ Copilot timeout handling (AW-2)\*\*: copilot-bridge.js now uses AbortController with 60s timeout for non-streaming and 120s for streaming. Timeout produces a Japanese error message suggesting the user try a different model.



\*\*★ System prompt fix (AW-2)\*\*: copilot-bridge.js system prompt was Shift-JIS garbled text (縺ゅ↑縺溘...). Replaced with clean UTF-8 Japanese research assistant prompt.



\*\*Model selection\*\*: UI dropdown groups models by tier (Available / Restricted 🔒 / Local Fallback). Default: claude-sonnet-4.6.



\*\*Copilot connection\*\*: copilot-api runs as proxy on port 4141. If not running, UI shows "Copilot Offline" and uses LiteLLM/Gemini fallback.



\### 5.4 Startup Procedure



```powershell

\# Terminal 1: Start copilot-api proxy

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npx copilot-api@latest start --port 4141



\# Terminal 2: Start Express server

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npm run dev

\# → JARVIS Agent Web v1.0.0 running at http://localhost:3000

5.5 Test Suite (Agent-Web)

node --test tests/database.test.js  → 5/5 passed

node --test tests/api.test.js       → 5/5 passed (requires running Express server)

Total: 10/10 passed

6\. Python Backend Reference

6.1 CLI Commands (22, all working, v2.0.0)

\#	Command	Key function

1	run	Full pipeline with goal

2	search	Multi-source (PubMed, S2, OpenAlex, arXiv, Crossref)

3	merge	Deduplicate JSON results

4	note	LLM Japanese summary

5	citation	Fetch citation counts

6	citation-stance	Classify citation relationships

7	prisma	PRISMA 2020 flow diagram

8	evidence	CEBM evidence grading

9	score	Paper quality scoring

10	screen	Active learning screening

11	browse	URL metadata extraction

12	skills	Workflow management

13	mcp	MCP Hub (5 servers, 15 tools)

14	orchestrate	LangGraph 6-agent pipeline

15	obsidian-export	Export to Obsidian Vault

16	semantic-search	ChromaDB vector search (~36 papers indexed)

17	contradict	Contradiction detection

18	zotero-sync	Zotero library sync

19	pdf-extract	PDF to Markdown (PyMuPDF)

20	deep-research	Autonomous research (Codex/Copilot/Gemini)

21	citation-graph	Citation network visualization

22	pipeline	Full pipeline with all options

6.2 Test Suite (Python)

D6 tests: 50/50 passed (pytest 9.0.2, timeout=30s). Files: test\_imports.py (19), test\_citation\_graph.py (12), test\_storage\_utils.py (5), test\_paperstore\_d6.py (4), test\_evidence.py (4), test\_cli\_commands.py (6).



6.3 config.yaml

Copyobsidian:

&nbsp; vault\_path: "H:\\\\マイドライブ\\\\obsidian-vault"

&nbsp; papers\_folder: JARVIS/Papers

&nbsp; notes\_folder: JARVIS/Notes

zotero:

&nbsp; api\_key: ''

&nbsp; user\_id: ''

&nbsp; collection: JARVIS

search:

&nbsp; default\_sources: \[pubmed, semantic\_scholar, openalex]

&nbsp; max\_results: 20

llm:

&nbsp; default\_provider: gemini

&nbsp; default\_model: gemini/gemini-2.0-flash

&nbsp; fallback\_model: openai/gpt-4.1

&nbsp; models:

&nbsp;   gemini: gemini/gemini-2.0-flash

&nbsp;   openai: openai/gpt-5-mini

&nbsp;   deepseek: deepseek/deepseek-reasoner

&nbsp; cache\_enabled: true

&nbsp; max\_retries: 3

&nbsp; temperature: 0.3

evidence:

&nbsp; use\_llm: false

&nbsp; strategy: weighted\_average

storage:

&nbsp; logs\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\logs"

&nbsp; exports\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\exports"

&nbsp; pdf\_archive\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\pdf-archive"

&nbsp; local\_fallback: logs

Copy

7\. Remaining Tasks

7.1 Minor Polish (Optional)

\#	Task	Est.	Details

D6-4	README.md update	30min	Add Agent-Web section to project root README.md

HANDOVER	Update HANDOVER\_v9.md on GitHub	Done	v9 re-pushed with full content at 43342c25

7.2 Future Enhancements (Not Started)

\#	Idea	Priority

F-1	Chat history export (JSON/Markdown)	Low

F-2	Multi-turn conversation context in Copilot calls	Medium

F-3	File upload → PDF extract → chat about paper	Medium

F-4	Agent-Web dark/light theme toggle	Low

F-5	JARVIS pipeline trigger from Agent-Web UI	Medium

F-6	WebSocket upgrade for real-time streaming	Low

8\. Known Issues (MUST READ)

agents.py vs agents/ conflict: jarvis\_core/agents.py (file) and jarvis\_core/agents/ (dir) coexist. DO NOT import jarvis\_core.agents.orchestrator.

Scrapling: css\_first() does NOT exist. Use css("sel")\[0].

PowerShell JSON: Inline JSON breaks. Use --params-file for MCP invoke.

jarvis\_cli/init.py: MUST overwrite entirely. No partial edits.

Rate limits: Gemini 15 RPM / 1500 req/day. Semantic Scholar 100 req/5min. Add time.sleep(3).

OpenAlexClient.search(): Parameter is per\_page, NOT max\_results.

Datalab.to MinerU API: Returns 403 (paid). PyMuPDF4LLM fallback works.

LightRAG: asyncio.CancelledError prevents .graphml writing. LLM cache is saved.

Python version: 3.11.9 (NOT 3.12.3 as earlier docs stated).

copilot-api Pro+ models: Models like gpt-5.1, claude-opus-4.6 return 400. Use tier-filtered list.

copilot-bridge.js system prompt: Was Shift-JIS garbled in Cat 6. Fixed in AW-2 (v10) to clean UTF-8.

chat.js URL detection: Was inside isResearchQuery() block in Cat 8. Fixed in AW-1 (v10) to always trigger.

UTF-8 surrogates: llm\_caller.py and chat.js both strip \[\\uD800-\\uDFFF].

9\. Absolute Rules

Never use python -c "..." for complex code. Always create .py files.

jarvis\_cli/\_\_init\_\_.py: full overwrite only.

Package install: python -m pip install only.

DO NOT import jarvis\_core.agents.orchestrator.

Scrapling: no css\_first(). Use css("sel")\[0].

MCP JSON: use --params-file, not inline JSON.

Gemini 15 RPM limit: add time.sleep(3).

OpenAlexClient.search() uses per\_page, not max\_results.

Free tier only for all APIs.

User work style: copy-paste → Enter → verify.

Agent-Web: do NOT modify files outside agent-web/ directory (when working on Agent-Web tasks).

Agent-Web: ESM modules only, Express v5, Windows paths via path.join().

Port 3000 for Agent-Web, port 8501 for Streamlit, port 4141 for copilot-api. No conflicts.

10\. Smoke Test (run at session start)

Python Backend

Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1

python --version

\# Expected: Python 3.11.9

git log --oneline -5

python -m jarvis\_cli --help

\# Expected: 22 commands

python -c "from jarvis\_core.llm.litellm\_client import completion; print('LiteLLM OK')"

python -c "from jarvis\_core.embeddings.paper\_store import PaperStore; s=PaperStore(); print(f'ChromaDB OK, count={s.count()}')"

\# Expected: 36 papers

python -c "from jarvis\_core.rag.citation\_graph import CitationGraph; print('CitationGraph OK')"

python -c "from jarvis\_core.storage\_utils import get\_logs\_dir; print(f'Logs: {get\_logs\_dir()}')"

\# Expected: H:\\マイドライブ\\jarvis-data\\logs

python -m pytest tests/test\_imports.py -q --timeout=30

\# Expected: 19/19 passed

Agent-Web

Copy# Terminal 1:

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npx copilot-api@latest start --port 4141



\# Terminal 2:

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npm run dev

\# Expected: http://localhost:3000



\# Terminal 3 (or same as Terminal 2 after server starts):

node --test tests/database.test.js

\# Expected: 5/5 passed

Browser test: Open http://localhost:3000, send https://arxiv.org/abs/2005.12402 を要約して, confirm Activity shows Browse Url (done) + Generate Response (done).



11\. Storage Layout

C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\

├── .env                          # API keys (gitignored)

├── .gitignore

├── config.yaml

├── pyproject.toml                # v2.0.0

├── HANDOVER\_v8.md

├── HANDOVER\_v9.md

├── HANDOVER\_v10.md               # ★ This file

├── JARVIS\_EXPANSION\_PLAN\_v1.md

├── jarvis\_cli/                   # 22 CLI command handlers

├── jarvis\_core/                  # Core library

├── jarvis\_web/streamlit\_app.py   # 5-page Streamlit dashboard

├── tests/                        # 50 pytest tests

├── agent-web/                    # ★ Node.js Agent-Web (committed 38587e79)

│   ├── src/                      # Express routes, LLM bridges, DB

│   ├── public/                   # SPA frontend

│   ├── tests/                    # 10 node --test tests

│   ├── README.md

│   └── package.json

├── .chroma/                      # ChromaDB persist (gitignored)

└── .lightrag/                    # LightRAG persist (gitignored)



H:\\マイドライブ\\jarvis-data\\

├── logs\\{orchestrate,pipeline,deep\_research}\\

├── exports\\{json,bibtex,prisma}\\

└── pdf-archive\\



H:\\マイドライブ\\obsidian-vault\\

└── JARVIS\\{Papers,Notes}\\

12\. Next Action

Project is feature-complete. Optional remaining work:



D6-4: Add Agent-Web section to project root README.md

Future enhancements (§7.2): multi-turn context, file upload, pipeline trigger from UI

Next session start message

Paste the following as the first message in a new chat:



JARVIS Research OS プロジェクトの引き継ぎです。以下の引き継ぎ書を読み込んでから作業を開始してください。



\## 引き継ぎ書（必ず最初に全文を読むこと）

https://github.com/kaneko-ai/jarvis-ml-pipeline/blob/main/HANDOVER\_v10.md



\## 現在地

\- Python CLI backend: v2.0.0 (D1–D7 全完了、22コマンド、50 pytest)

\- Agent-Web (agent-web/): Cat 1–10 全完了、Git committed (38587e79)、10 node tests

\- 全機能完成。残りはオプション（README更新、将来拡張）



\## 環境サマリー

\- Windows 11 / PowerShell 5.1 / Python 3.11.9 / Node v24.13.1

\- パス: C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline

\- Agent-Web: agent-web/ (Express v5, port 3000)

\- Copilot API: copilot-api (port 4141, Education Pro)

\- 推奨モデル: claude-sonnet-4.6

\- LLMフォールバック: gemini/gemini-2.0-flash (LiteLLM)



\## 絶対ルール（抜粋）

\- agent-web/ の外のファイルを変更しない（Agent-Webタスク時）

\- Free tier のみ使用

\- python -c で複雑なコード実行禁止

\- jarvis\_cli/\_\_init\_\_.py は全上書きのみ

\- ユーザーの作業はコピペ → Enter → 結果確認のみ



\## 作業の進め方

1\. まず上記URLのHANDOVER\_v10.mdを全文読み込む

2\. セクション10のスモークテストを提示する

3\. スモークテスト結果を確認後、ユーザーの要望に応じて作業開始


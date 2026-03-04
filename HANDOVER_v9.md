HANDOVER\_v9.md — JARVIS Research OS + Agent-Web Handover v9

Date: 2026-03-04 Previous: HANDOVER\_v8.md (2026-03-04, commit 0d5d7999) Repository: https://github.com/kaneko-ai/jarvis-ml-pipeline Branch: main Latest pushed commit: 0d5d7999 D5: Obsidian/storage H: migration, citation network, storage\_utils, 22 CLI commands (tag: v1.3.0) Related repo: https://github.com/kaneko-ai/zotero-doi-importer (A-6 done) Expansion plan: JARVIS\_EXPANSION\_PLAN\_v1.md (in repo root) Purpose: Any AI or developer reading this document can continue implementation with zero additional questions. Covers both the Python CLI backend (v1.3.0) and the new Node.js Agent-Web frontend (Category 1–5 complete, Category 6–7 remaining).



1\. Project Overview

JARVIS Research OS automates Systematic Literature Reviews. The Python CLI backend (22 commands) handles: paper search, dedup, evidence grading, scoring, LLM Japanese summary, Obsidian notes, Zotero sync, PRISMA diagrams, BibTeX output, citation network visualization, ChromaDB semantic search, LangGraph orchestration, and deep research.



The Agent-Web is a new Node.js/Express dark-theme SPA at agent-web/ that provides a browser-based chat interface to all JARVIS capabilities. It connects to GitHub Copilot via copilot-api (localhost:4141) for multi-model LLM access and falls back to Gemini via LiteLLM Python bridge.



User: Graduate student (beginner programmer, Windows) Use cases: PD-1 immunotherapy, spermidine, immunosenescence/autophagy research



2\. Development Environment (2026-03-04)

Item	Value

OS	Windows 11

Shell	PowerShell 5.1

Python	3.11.9 (venv shows cp311)

Node.js	v24.13.1

npm	(bundled with Node v24)

Project path	C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline

Agent-Web path	C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web

venv	.venv (project root)

venv activate	.\\.venv\\Scripts\\Activate.ps1

Python exe	.venv\\Scripts\\python.exe

Obsidian Vault	H:\\\\obsidian-vault (migrated D5-1)

Logs/Exports	H:\\\\jarvis-data\\ (migrated D5-3)

C: free	~45 GB / 460 GB

H: drive	Google Drive 2TB (personal, kanekiti1125@gmail.com)

G: drive	Google Drive 100GB (student, kaneko.yu3@dc.tohoku.ac.jp, NOT used by JARVIS)

GPU	None (Intel Iris Plus Graphics)

RAM	16 GB LPDDR4x

CPU	Intel i7-1065G7 (4C/8T)

2.1 Environment Variables (.env at project root, gitignored)

GEMINI\_API\_KEY=<39-char key>

LLM\_PROVIDER=gemini

ZOTERO\_API\_KEY=<issued 2026-03-02>

ZOTERO\_USER\_ID=16956010

OPENAI\_API\_KEY=

DEEPSEEK\_API\_KEY=

LLM\_MODEL=gemini/gemini-2.0-flash

DATALAB\_API\_KEY=<present but 403>

2.2 Python Packages (.venv)

v1.0.0: jarvis-research-os 1.0.0, google-genai 1.65.0, python-dotenv, rank-bm25, sentence-transformers (MiniLM-L6-v2), pyzotero, requests, streamlit 1.54.0, rapidfuzz, scikit-learn, pyyaml, scrapling 0.4.1, beautifulsoup4. D1: litellm 1.82.0, openai 2.24.0, pydantic-ai 1.63.0, instructor 1.14.5, tiktoken, aiohttp. D3: chromadb, lightrag-hku, pymupdf4llm. D4: langgraph. D6: pytest, pytest-timeout.



2.3 Node.js Packages (agent-web/package.json)

express (v5), better-sqlite3, dotenv, js-yaml, eventsource-parser, uuid, copilot-api. Total ~130+ packages installed via npm.



2.4 AI CLI Tools

Tool	Version	Auth	Plan	Models (usable)

Codex CLI	0.106.0	ChatGPT Plus	$20/mo	GPT-5.3-Codex, GPT-5-mini, GPT-4.1

Copilot CLI	0.0.420	Education Pro	Free	See §2.5

copilot-api (npm)	latest	Education Pro	Free	Same as Copilot CLI

2.5 GitHub Copilot Model Availability (Education Pro = Copilot Pro equivalent)

Usable (tier: "pro"): claude-sonnet-4.6, claude-sonnet-4.5, gpt-4.1, gpt-4.1-mini, gpt-4o, o4-mini, gemini-2.0-flash, gemini-2.5-pro.



Restricted (tier: "pro+", return 400 model\_not\_supported): claude-opus-4.6-fast, claude-opus-4.6, claude-opus-4.5, gpt-5.1, gpt-5.1-codex, gpt-5.2-codex, gpt-5.3-codex, gemini-3-pro-preview, gemini-3-flash-preview, gemini-3.1-pro-preview.



Default model for Agent-Web chat: claude-sonnet-4.6 (confirmed working).



2.6 NOT Installed / Unusable

Component	Reason

Ollama	Not installed, use\_llm=false workaround

Crawl4AI	Playwright+Chromium too heavy; Jina Reader instead

Datalab.to MinerU API	403 (paid); PyMuPDF4LLM fallback works

GPT-Researcher	Requires paid OpenAI API key; self-built deep-research

openai-agents-python	Requires paid OpenAI API key

Policy: Free tier only for all APIs.



3\. Commit History (Python backend)

0d5d7999 D5: Obsidian/storage H: migration, citation network, 22 CLI (tag: v1.3.0) ← LATEST

6f9479ec D4: LangGraph orchestrator, deep-research CLI, skills execute

8da82646 D3: ChromaDB PaperStore, LightRAG engine, PDF-to-Markdown (tag: v1.2.0)

8e11f4ef docs: HANDOVER\_v6.md

40fff89f D2: browse.py Jina fallback + authors dedup, MCP handlers (tag: v1.1.0)

fb63f6fe D1: LiteLLM + Instructor + PydanticAI

Agent-Web files are NOT yet committed to Git. They exist only locally at agent-web/.



4\. Task Completion Map

D1–D5: ALL DONE (Python CLI backend)

Day	Phase	Status

D1	AI Tools + LLM Foundation (LiteLLM, PydanticAI, Instructor)	DONE

D2	Scraping/Browse Enhancement (Jina Reader, MCP handlers)	DONE

D3	RAG/Vector DB/PDF (ChromaDB, LightRAG, PyMuPDF)	DONE

D4	Agent/Orchestrator (LangGraph 6-agent, deep-research)	DONE

D5	Knowledge Management (Obsidian H:, CitationGraph, storage\_utils)	DONE

D6: Test/QA/Docs \[IN PROGRESS]

Task	Status	Notes

D6-1 pytest suite	DONE	7 files, 50/50 passed

D6-2 Streamlit Dashboard	DONE	5-page (Overview/Search/Citation/ChromaDB/Storage)

D6-3 HANDOVER\_v8.md	DONE	

D6-4 README.md update	TODO	

D7: Final/Smoke Test/v2.0.0 \[NOT STARTED]

Task	Est.

D7-1 All CLI commands smoke test	2h

D7-2 E2E pipeline test (2 queries)	1.5h

D7-3 Bug fix buffer	1.5h

D7-4 pyproject.toml version → v2.0.0	30min

D7-5 Final commit + push + git tag v2.0.0	30min

Agent-Web Categories \[Cat 1–5 DONE, Cat 6–7 TODO]

Category	Content	Status

Cat 1: Foundation	Express v5, SQLite chat-history.db, dark-theme SPA	DONE

Cat 2: Python LLM Bridge	llm\_caller.py → LiteLLM → Gemini API	DONE

Cat 3: JARVIS CLI Tools	jarvis-tools.js (search, semantic-search, browse, evidence)	DONE

Cat 4: Skills Migration	skill-registry.js (8 built-in skills), /api/skills	DONE

Cat 5: MCP Integration	mcp-status.js (5 servers, 15 tools), /api/mcp/servers	DONE

Cat 6: Copilot SDK Integration	copilot-bridge.js via copilot-api proxy	DONE

Cat 7: Model Tier + Usage	Pro/Pro+ tier display, usage bar, error handling	DONE

Cat 8: browse\_url + Error Handling	Auto URL detection → JARVIS browse → LLM summary	DONE (chat.js)

Cat 9: Testing + README	agent-web/README.md, automated tests	TODO

Cat 10: Git Commit	Add agent-web/ to repo, commit, push	TODO

5\. Agent-Web Architecture

5.1 Overview

Browser (localhost:3000)

&nbsp;   ↓ HTTP/SSE

Express v5 (agent-web/src/server.js)

&nbsp;   ├── /api/chat/stream  → copilot-bridge.js → copilot-api (localhost:4141) → GitHub Copilot

&nbsp;   │                     → python-bridge.js → llm\_caller.py → LiteLLM → Gemini (fallback)

&nbsp;   ├── /api/sessions     → better-sqlite3 (chat-history.db)

&nbsp;   ├── /api/models       → copilot-api /v1/models + static fallback list

&nbsp;   ├── /api/usage        → copilot-api /usage endpoint

&nbsp;   ├── /api/skills       → skill-registry.js (8 skills)

&nbsp;   ├── /api/mcp/servers  → mcp-status.js (5 servers, 15 tools)

&nbsp;   └── /api/health       → {"status":"ok","version":"1.0.0"}

5.2 File Structure (agent-web/)

agent-web/

├── package.json           # Express v5, better-sqlite3, copilot-api, etc.

├── package-lock.json      # Generated

├── start.ps1              # PowerShell: starts copilot-api (4141) + Express (3000)

├── src/

│   ├── server.js          # Express entry point, port 3000

│   ├── routes/

│   │   ├── chat.js        # SSE streaming, Copilot + LiteLLM fallback, research detection

│   │   ├── sessions.js    # CRUD for chat sessions

│   │   ├── models.js      # Model list with pro/pro+/local tiers

│   │   ├── skills.js      # /api/skills endpoint

│   │   ├── mcp.js         # /api/mcp/servers endpoint

│   │   └── usage.js       # /api/usage (Copilot quota)

│   ├── db/

│   │   └── database.js    # better-sqlite3 CRUD (sessions + messages tables)

│   ├── llm/

│   │   ├── copilot-bridge.js   # Calls copilot-api localhost:4141 (OpenAI-compatible)

│   │   ├── python-bridge.js    # Spawns .venv Python for LiteLLM fallback

│   │   ├── llm\_caller.py       # Python: reads JSON stdin, calls litellm completion

│   │   └── jarvis-tools.js     # Spawns JARVIS CLI: search, semantic-search, browse, evidence

│   ├── skills/

│   │   └── skill-registry.js   # 8 built-in skills + custom loader

│   ├── mcp-bridge/

│   │   └── mcp-status.js       # 5 MCP servers, 15 tools, invokeMCPTool

│   └── middleware/              # (placeholder)

├── public/

│   ├── index.html         # Dark-theme SPA shell

│   ├── css/

│   │   └── styles.css     # RPG dark theme, flex layout, scrollable chat

│   └── js/

│       └── app.js         # ES module: SSE parsing, model selector, usage bar, sessions

├── chat-history.db        # SQLite (gitignored)

└── node\_modules/          # (gitignored)

5.3 Key Behaviors

Chat flow: User types message → POST /api/chat/stream → SSE connection opened → research keyword detection (regex: 論文, 調べ, PD-1, immunotherapy, etc.) → if matched, semantic\_search via JARVIS CLI → results prepended to prompt → model called via copilot-bridge.js (streaming SSE) → response streamed as delta events → conversation saved to SQLite → done event sent.



URL detection: If message contains a URL, browse\_url is triggered via jarvis-tools.js, content is prepended to the LLM prompt.



Model selection: UI dropdown groups models by tier (Available / Restricted 🔒 / Local Fallback). Selecting a Pro+ model returns a friendly error suggesting a compatible alternative. Default: claude-sonnet-4.6.



Copilot connection: copilot-api (npm package) runs as a proxy on port 4141, authenticating via GitHub OAuth. Express reads from it via OpenAI-compatible /v1/chat/completions. If copilot-api is not running, the UI shows "Copilot Offline" and uses LiteLLM/Gemini fallback.



Usage tracking: /api/usage polls copilot-api /usage and shows premium\_interactions.percent\_remaining as a progress bar in the sidebar (green < 50%, yellow 50–80%, red > 80% used). Last observed: 99.33% remaining.



5.4 Startup Procedure

Copy# Terminal 1: Start copilot-api proxy (requires GitHub auth first time)

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npx copilot-api@latest start --port 4141



\# Terminal 2: Start Express server

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npm run dev

\# → JARVIS Agent Web v1.0.0 running at http://localhost:3000



\# OR use start.ps1 (starts both in sequence)

.\\start.ps1

5.5 Verified Functionality

Feature	Status	Evidence

Express server starts	OK	http://localhost:3000, health endpoint returns {"status":"ok"}

Dark-theme SPA loads	OK	Screenshot confirmed

Model dropdown with tiers	OK	Pro/Pro+/Local groups visible

Chat with claude-sonnet-4.6	OK	Real response received via Copilot

Chat with gemini-2.0-flash	OK	LiteLLM fallback works

Research Mode (semantic\_search)	OK	36 ChromaDB papers searched, results prepended

Activity Timeline	OK	Steps with elapsed time displayed

Session management (CRUD)	OK	Sidebar shows session list

Copilot usage bar	OK	99.33% remaining shown

Pro+ model error handling	OK	Friendly error message displayed

Scrollable chat area	OK	CSS flex layout fixed

Japanese text rendering	OK	UTF-8 surrogate sanitization in llm\_caller.py

5.6 Known Issues (Agent-Web)

browse\_url not yet browser-tested: chat.js has URL detection + jarvis-tools.js browsePage() but no screenshot confirmation of end-to-end flow in browser.

No automated tests: Agent-Web has no test suite yet (Cat 9 TODO).

Not committed to Git: All agent-web files are local only (Cat 10 TODO).

copilot-api authentication: First-time run requires browser-based GitHub OAuth. Token is cached thereafter.

copilot-api model list may change: The available/restricted model split is based on the current Education Pro plan. If GitHub changes tiers, models.js needs updating.

6\. Python Backend Reference

6.1 CLI Commands (22, all working)

\#	Command	Key function

1	run	Full pipeline with goal

2	search	Multi-source paper search (PubMed, S2, OpenAlex, arXiv, Crossref)

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

16	semantic-search	ChromaDB vector search (~28 papers indexed)

17	contradict	Contradiction detection

18	zotero-sync	Zotero library sync

19	pdf-extract	PDF to Markdown (PyMuPDF)

20	deep-research	Autonomous research (Codex/Copilot/Gemini)

21	citation-graph	Citation network visualization

22	pipeline	Full pipeline with all options

6.2 Important Import Paths

Copyfrom jarvis\_core.llm.litellm\_client import completion, completion\_structured

from jarvis\_core.llm.structured\_models import EvidenceGradeLLM, PaperSummaryLLM

from jarvis\_core.embeddings.paper\_store import PaperStore

from jarvis\_core.rag.lightrag\_engine import JarvisLightRAG

from jarvis\_core.rag.citation\_graph import CitationGraph

from jarvis\_core.pdf.mineru\_client import MinerUClient

from jarvis\_core.storage\_utils import get\_logs\_dir, get\_exports\_dir

from jarvis\_core.mcp.hub import MCPHub

from jarvis\_core.skills.engine import SkillsEngine

from jarvis\_core.sources.unified\_source\_client import UnifiedSourceClient

from jarvis\_core.evidence import grade\_evidence

\# DO NOT import jarvis\_core.agents.orchestrator (file/dir conflict)

6.3 Test Suite

D6 tests: 50/50 passed (pytest 9.0.2, timeout=30s). Files: test\_imports.py (19), test\_citation\_graph.py (12), test\_storage\_utils.py (5), test\_paperstore\_d6.py (4), test\_evidence.py (4), test\_cli\_commands.py (6).



6.4 config.yaml (current)

Copyobsidian:

&nbsp; vault\_path: "H:\\\\obsidian-vault"

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

&nbsp; logs\_dir: "H:\\\\jarvis-data\\\\logs"

&nbsp; exports\_dir: "H:\\\\jarvis-data\\\\exports"

&nbsp; pdf\_archive\_dir: "H:\\\\jarvis-data\\\\pdf-archive"

&nbsp; local\_fallback: logs

Copy

7\. Remaining Tasks (Priority Order)

7.1 Agent-Web Completion

\#	Task	Est.	Details

AW-1	browse\_url browser test	15min	Send https://arxiv.org/abs/2005.12402 を要約して in UI, confirm Activity shows browse\_url step

AW-2	Error handling hardening	30min	chat.js: browse failure → SSE error + LLM-only fallback; copilot-bridge timeout → clear error message

AW-3	agent-web/README.md	30min	Startup, architecture, API list, model table

AW-4	Automated tests	1h	database.test.js (CRUD), models.test.js (API response format) via node --test

AW-5	Git commit agent-web	15min	git add agent-web/ \&\& git commit -m "feat: Agent-Web v1.0.0 (Express+Copilot+JARVIS)"

7.2 Python Backend Completion

\#	Task	Est.	Details

D6-4	README.md update	30min	v1.3.0 features, Agent-Web section

D7-1	All 22 CLI smoke test	2h	Run each command, record pass/fail

D7-2	E2E pipeline test (2 queries)	1.5h	"PD-1 immunotherapy" and "spermidine autophagy aging"

D7-3	Bug fix buffer	1.5h	Fix any issues found in D7-1/D7-2

D7-4	pyproject.toml → v2.0.0	30min	Version bump

D7-5	Final commit + push + tag v2.0.0	30min	Includes agent-web/

8\. Known Issues (MUST READ)

agents.py vs agents/ conflict: jarvis\_core/agents.py (file) and jarvis\_core/agents/ (dir) coexist. DO NOT import jarvis\_core.agents.orchestrator.

Scrapling: css\_first() does NOT exist. Use css("sel")\[0].

PowerShell JSON: Inline JSON breaks. Use --params-file for MCP invoke.

jarvis\_cli/init.py: MUST overwrite entirely. No partial edits.

Rate limits: Gemini 15 RPM / 1500 req/day. Semantic Scholar 100 req/5min. Add time.sleep(3).

OpenAlexClient.search(): Parameter is per\_page, NOT max\_results.

Datalab.to MinerU API: Returns 403 (paid). PyMuPDF4LLM fallback works.

LightRAG graph persistence: asyncio.CancelledError prevents .graphml writing. LLM cache is saved.

Python version: 3.11.9 (NOT 3.12.3 as earlier docs state).

copilot-api Pro+ models: Models like gpt-5.1, claude-opus-4.6 return 400. Use tier-filtered list in models.js.

Agent-Web Gemini auto-fallback removed: chat.js no longer falls back to Gemini when Copilot model fails. Error is shown to user with suggestion to switch model.

UTF-8 surrogates: llm\_caller.py sanitizes surrogates before/after LiteLLM calls. chat.js also strips \[\\uD800-\\uDFFF] from semantic search results.

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

Agent-Web: do NOT modify files outside agent-web/ directory.

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

\# Expected: ~28 papers

python -c "from jarvis\_core.rag.citation\_graph import CitationGraph; print('CitationGraph OK')"

python -c "from jarvis\_core.storage\_utils import get\_logs\_dir; print(f'Logs: {get\_logs\_dir()}')"

\# Expected: H:\\jarvis-data\\logs

python -m pytest tests/test\_imports.py -q --timeout=30

\# Expected: 19/19 passed

Agent-Web

Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npm run dev

\# Expected: JARVIS Agent Web v1.0.0 running at http://localhost:3000



\# In another terminal (for Copilot models):

npx copilot-api@latest start --port 4141



\# Verify endpoints:

curl http://localhost:3000/api/health

\# Expected: {"status":"ok","version":"1.0.0","timestamp":"..."}

curl http://localhost:3000/api/models

\# Expected: JSON array with claude-sonnet-4.6, gpt-4.1, etc.

curl http://localhost:3000/api/skills

\# Expected: 8 skills

curl http://localhost:3000/api/mcp/servers

\# Expected: 5 servers

11\. Storage Layout

C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\

├── .env                          # API keys (gitignored)

├── .gitignore                    # .chroma/, .lightrag/, node\_modules/, chat-history.db

├── config.yaml                   # Project configuration

├── pyproject.toml                # Python package (v1.3.0)

├── HANDOVER\_v8.md                # Previous handover

├── JARVIS\_EXPANSION\_PLAN\_v1.md   # Master plan D1–D7

├── jarvis\_cli/                   # 22 CLI command handlers

├── jarvis\_core/                  # Core library

│   ├── embeddings/paper\_store.py # ChromaDB PaperStore

│   ├── llm/litellm\_client.py    # LiteLLM unified client

│   ├── llm/structured\_models.py  # Pydantic models

│   ├── mcp/hub.py               # MCP Hub (5 servers, 15 tools)

│   ├── pdf/mineru\_client.py     # PDF→Markdown

│   ├── rag/citation\_graph.py    # CitationGraph

│   ├── rag/lightrag\_engine.py   # LightRAG wrapper

│   ├── skills/engine.py         # Skills engine

│   ├── sources/                 # Multi-source search

│   └── storage\_utils.py         # H: drive paths

├── jarvis\_web/streamlit\_app.py   # 5-page Streamlit dashboard

├── tests/                        # 50+ pytest tests

├── .chroma/                      # ChromaDB persist (gitignored)

├── .lightrag/                    # LightRAG persist (gitignored)

├── agent-web/                    # ★ NEW: Node.js Agent-Web

│   ├── package.json

│   ├── start.ps1

│   ├── src/server.js

│   ├── src/routes/{chat,sessions,models,skills,mcp,usage}.js

│   ├── src/db/database.js

│   ├── src/llm/{copilot-bridge,python-bridge,jarvis-tools}.js

│   ├── src/llm/llm\_caller.py

│   ├── src/skills/skill-registry.js

│   ├── src/mcp-bridge/mcp-status.js

│   ├── public/{index.html,css/styles.css,js/app.js}

│   ├── chat-history.db          # SQLite (gitignored)

│   └── node\_modules/            # (gitignored)

└── logs/, scripts/

H:\\jarvis-data\\

├── logs\\{orchestrate,pipeline,deep\_research}\\

├── exports\\{json,bibtex,prisma}\\

└── pdf-archive\\



H:\\obsidian-vault\\

└── JARVIS\\{Papers,Notes}\\

12\. Next Action

Resume from AW-1 (browse\_url browser test), then proceed through AW-2 → AW-5 → D6-4 → D7-1 → D7-5. Total estimated remaining: ~8 hours.



次のチャットで使う開始メッセージ

以下のテキストを新しいチャットの最初のメッセージとしてそのまま貼り付けてください：



あなたはJARVIS Research OS プロジェクトの引き継ぎを受けるAIアシスタントです。



\## プロジェクト概要

JARVIS Research OSは、系統的文献レビューを自動化するPython CLIツール（22コマンド、v1.3.0）と、それをブラウザから操作するNode.js Agent-Web（Express v5 + GitHub Copilot連携）で構成されています。



\## 現在の状態

\- \*\*Python CLI backend\*\*: D1–D5完了、D6テスト50/50パス、D7（最終テスト・v2.0.0リリース）未着手

\- \*\*Agent-Web\*\*: Cat 1–8完了（Express, SQLite, Copilot連携, Skills, MCP, モデルTier管理, Research Mode）、Cat 9–10（テスト・README・Git commit）未着手

\- \*\*最新コミット\*\*: 0d5d7999 (tag: v1.3.0) — agent-webはまだGitに未コミット



\## 環境

\- Windows 11, PowerShell 5.1, Python 3.11.9, Node v24.13.1

\- パス: `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline`

\- AI: Codex CLI 0.106.0 (ChatGPT Plus), Copilot CLI 0.0.420 (Education Pro), Gemini API (free 15 RPM)

\- Agent-Web推奨モデル: claude-sonnet-4.6 (Copilot Pro)



\## 引き継ぎ書

以下のURLにある HANDOVER\_v9.md の全内容を読み込んでください。この文書にはPCスペック、環境変数、インストール済みパッケージ、全ファイル構成、完了/未完了タスク一覧、既知の問題、絶対ルール、スモークテスト手順がすべて記載されています。



\[ここに HANDOVER\_v9.md のURLまたは全文を貼り付ける]



\## 今回のタスク

引き継ぎ書のセクション7「Remaining Tasks」に従って、AW-1（browse\_url ブラウザテスト）から順に進めてください。タスクの実行手順は、ユーザーがコピペ→Enter→結果確認するだけで完了できるように、具体的なコマンドとファイル内容を提示してください。

この引き継ぎ書（HANDOVER\_v9.md）をプロジェクトルートに保存しておくことを推奨します。GitHubにプッシュすれば、次回のAIセッションでURLから直接読み込めます。



保存コマンド：



Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

\# HANDOVER\_v9.md の内容をクリップボードにコピーした状態で:

Set-Content -Path "HANDOVER\_v9.md" -Value (Get-Clipboard) -Encoding UTF8

git add HANDOVER\_v9.md

git commit -m "docs: HANDOVER\_v9.md - Agent-Web integration complete through Cat 8"

git push

次のセッションの初めのメッセージはどうすれば？

以下をそのまま新しいチャットの最初のメッセージとして貼り付けてください：



JARVIS Research OS プロジェクトの引き継ぎです。以下の引き継ぎ書を読み込んでから作業を開始してください。



\## 引き継ぎ書（必ず最初に全文を読むこと）

https://github.com/kaneko-ai/jarvis-ml-pipeline/blob/main/HANDOVER\_v9.md



\## 現在地

\- Python CLI backend: v1.3.0 (D1–D6完了、D7未着手)

\- Agent-Web (agent-web/): Cat 1–8完了、Cat 9–10未着手、Gitに未コミット

\- 次のタスク: HANDOVER\_v9.md セクション7「Remaining Tasks」の AW-1 から順に実行



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

1\. まず上記URLのHANDOVER\_v9.mdを全文読み込む

2\. セクション10のスモークテストを提示する

3\. スモークテスト結果を確認後、AW-1（browse\_urlブラウザテスト）から作業開始

4\. 各タスクはコピペ可能なコマンド・ファイル内容を提示すること


\# HANDOVER\_v7.md — JARVIS Research OS Handover v7



\*\*Date\*\*: 2026-03-03

\*\*Previous\*\*: HANDOVER\_v6.md (2026-03-03, commit 8e11f4ef)

\*\*Repository\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline

\*\*Branch\*\*: main

\*\*Latest pushed commit\*\*: 6f9479ec — D4: LangGraph orchestrator (6 agents, conditional retry), deep-research CLI (Codex/Copilot/Gemini fallback chain), skills execute verified

\*\*Related repo\*\*: https://github.com/kaneko-ai/zotero-doi-importer (A-6 done, commit 0cb2447)

\*\*Expansion plan\*\*: JARVIS\_EXPANSION\_PLAN\_v1.md (in repo root)



\*\*Purpose\*\*: Any AI or developer reading this can continue implementation with zero additional questions.



---



\## 1. Project Overview



JARVIS Research OS automates Systematic Literature Reviews. One CLI command runs: paper search, dedup, evidence grading, scoring, LLM Japanese summary, Obsidian notes, Zotero sync, PRISMA diagram, BibTeX output.



\*\*User\*\*: Graduate student (beginner programmer, Windows)

\*\*Use cases\*\*: PD-1 immunotherapy, spermidine, immunosenescence/autophagy research



---



\## 2. Development Environment (2026-03-03)



| Item | Value |

|------|-------|

| OS | Windows 11 |

| Shell | PowerShell 5.1 |

| Python | 3.11.9 (venv shows cp311) |

| Node.js | v24.13.1 |

| Project path | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| venv | `.venv` (project root) |

| venv activate | `.\\.venv\\Scripts\\Activate.ps1` |

| Python exe | `.venv\\Scripts\\python.exe` |

| Obsidian Vault | `C:\\Users\\kaneko yu\\Documents\\ObsidianVault` |

| C: free | ~45 GB / 460 GB |

| H: drive | Google Drive 2TB (personal, kanekiti1125@gmail.com) |

| G: drive | Google Drive 100GB (student, kaneko.yu3@dc.tohoku.ac.jp, not used by JARVIS) |

| GPU | None (Intel Iris Plus Graphics) |

| RAM | 16 GB LPDDR4x |

| CPU | Intel i7-1065G7 (4C/8T) |



\### 2.1 Environment Variables (.env)



.env is at project root, excluded from Git.



Copy

GEMINI\_API\_KEY=<39-char key> LLM\_PROVIDER=gemini ZOTERO\_API\_KEY=<issued 2026-03-02> ZOTERO\_USER\_ID=16956010 OPENAI\_API\_KEY= DEEPSEEK\_API\_KEY= LLM\_MODEL=gemini/gemini-2.0-flash DATALAB\_API\_KEY=ng2yRJcuRfpvc0mCRwENWwGucyfLq5eTOXMTBB7eeyY





\*\*Note\*\*: DATALAB\_API\_KEY is present but Datalab.to requires a paid subscription. The API returns 403 Forbidden. PyMuPDF fallback is used instead.



\### 2.2 Installed Packages (.venv)



\*\*v1.0.0\*\*: jarvis-research-os==1.0.0, google-genai==1.65.0, python-dotenv==1.2.2, rank-bm25==0.2.2, sentence-transformers (MiniLM-L6-v2), pyzotero, requests==2.32.5, streamlit==1.54.0, rapidfuzz==3.14.3, scikit-learn, pyyaml, scrapling==0.4.1, beautifulsoup4



\*\*D1 added\*\*: litellm==1.82.0, openai==2.24.0, pydantic-ai==1.63.0, instructor==1.14.5, tiktoken==0.12.0, aiohttp==3.13.3



\*\*D3 added\*\*: chromadb (persistent vector DB), lightrag-hku (graph RAG), pymupdf4llm (PDF→Markdown), datalab-python-sdk (MinerU API, unused due to 403)



\*\*D4 added\*\*: langgraph (StateGraph orchestrator)



\### 2.3 AI CLI Tools Installed



| Tool | Version | Auth | Models |

|------|---------|------|--------|

| Codex CLI | 0.106.0 | ChatGPT Plus authenticated | GPT-5.3-Codex (default), GPT-5-mini, GPT-4.1 |

| Copilot CLI | 0.0.420 | Education Pro authenticated | Claude Sonnet 4.6, GPT-5.3-Codex, Gemini 3 Pro etc. |



\*\*Codex CLI usage\*\*: `codex exec "prompt"` or `echo "prompt" | codex exec -` (stdin pipe for long prompts)

\*\*Copilot CLI usage\*\*: `copilot -p "prompt"` (programmatic mode), `--model` flag or `COPILOT\_MODEL` env var to select model



\### 2.4 NOT Installed / Unusable



| Component | Status | Reason |

|-----------|--------|--------|

| Ollama | Not installed | use\_llm=False workaround |

| Crawl4AI | Skipped (D2-3) | Playwright+Chromium too heavy; Jina Reader instead |

| pandas 3.0.0 | Install failed | Not needed |

| Datalab.to MinerU API | 403 Forbidden | Requires paid subscription; PyMuPDF4LLM fallback works |

| GPT-Researcher | Not installed | Requires OpenAI API key (paid); self-built deep-research instead |

| openai-agents-python | Not installed | Requires OpenAI API key (paid) |



\*\*Policy\*\*: 無料枠以外のAPIは使用しない（Free tier only for all APIs）



---



\## 3. Commit History



6f9479ec D4: LangGraph orchestrator, deep-research CLI, skills execute <- LATEST 8da82646 D3: ChromaDB PaperStore, LightRAG engine, PDF-to-Markdown (tag: v1.2.0) 8e11f4ef docs: HANDOVER\_v6.md - D1/D2 complete, D3-D7 remaining 40fff89f D2: browse.py Jina fallback + authors dedup, MCP handlers (tag: v1.1.0 implied) fb63f6fe D1: LiteLLM + Instructor + PydanticAI ea48d91d docs: JARVIS\_EXPANSION\_PLAN\_v1.md ab602b75 HANDOVER\_v5.md 9220dd5a C-4: Multi-Agent Orchestrator 7320bbe6 C-1: MCP Hub cf73f002 C-3: Skills System 5564623e C-2: Browser Agent f13ddbf4 C-6: pipeline zotero collection c7f24014 C-6: Zotero collection support 024a1a86 B-6: Streamlit + C-5: arXiv/Crossref 18941276 Phase B: B-5/B-3/B-1/B-2/B-4 5c043b02 Phase A: A-1/A-2/A-3/A-4/A-5





---



\## 4. Task Completion Map



\### v1.0.0 (Phase v2/A/B/C) — ALL 26 TASKS DONE



See HANDOVER\_v5.md section 3 for details.



\### v2.0.0 Expansion Tasks (D1–D7)



\#### Day 1: D1 — AI Tools + LLM Foundation \[DONE]



| Task | Content | Status | Commit |

|------|---------|--------|--------|

| D1-1 | Codex CLI 0.106.0 + Copilot CLI 0.0.420 install/auth | DONE | fb63f6fe |

| D1-2 | LiteLLM 1.82.0 + config.yaml llm.models section | DONE | fb63f6fe |

| D1-3 | PydanticAI 1.63.0 + Instructor 1.14.5 + 5 Pydantic models | DONE | fb63f6fe |

| D1-4 | LLM provider test: Structured Output PASS | DONE | fb63f6fe |

| D1-5 | Commit + push | DONE | fb63f6fe |



\#### Day 2: D2 — Scraping/Browse Enhancement \[DONE]



| Task | Content | Status | Commit |

|------|---------|--------|--------|

| D2-1 | browse.py: PubMed abstract 4-selector fallback, authors dedup | DONE | 40fff89f |

| D2-2 | Jina Reader API fallback for PubMed/Generic/fetch-fail | DONE | 40fff89f |

| D2-3 | Crawl4AI | SKIPPED | Playwright too heavy, Jina Reader instead |

| D2-4 | MCP: S2 4 tools + OpenAlex work + Crossref DOI + S2 429 retry | DONE | 40fff89f |

| D2-5 | Commit + push | DONE | 40fff89f |



\#### Day 3: D3 — RAG / Vector DB / PDF \[DONE]



| Task | Content | Status | Commit | Notes |

|------|---------|--------|--------|-------|

| D3-1 | ChromaDB + PaperStore + semantic-search永続化 | DONE | 8da82646 | 4/4テスト合格, PD-1 score=0.8293, persistence verified |

| D3-2 | LightRAG engine (Codex→Copilot→Gemini fallback) | DONE (partial) | 8da82646 | コード完成, Geminiで8エンティティ6リレーション抽出成功, グラフ永続化はasyncio CancelledErrorで未完了 |

| D3-3 | PDF→Markdown (MinerU API + PyMuPDF fallback) | DONE | 8da82646 | MinerU API=403(有料), PyMuPDF fallbackで25,890文字変換成功 |

| D3-4 | Commit + push → v1.2.0 | DONE | 8da82646 | tag v1.2.0 |



\*\*D3-2 LightRAG 詳細\*\*:

\- LightRAG (lightrag-hku) のエンティティ抽出は Gemini API 経由で動作確認済み

\- Codex CLI/Copilot CLI は LightRAG の長大プロンプト（数千文字のエンティティ抽出テンプレート）に対してタイムアウトまたはスキップされる

\- グラフ永続化（.graphml書き込み）は LightRAG 内部の asyncio.CancelledError で失敗。LLMキャッシュ（kv\_store\_llm\_response\_cache.json）は保存済みのため、再実行は高速化される見込み

\- Gemini 無料枠 15 RPM がボトルネック。1論文あたり4-6回のLLM呼び出しが必要

\- .lightrag/ と .chroma/ は .gitignore 済み



\#### Day 4: D4 — Agent/Orchestrator Enhancement \[DONE]



| Task | Content | Status | Commit | Notes |

|------|---------|--------|--------|-------|

| D4-1 | orchestrate.py → LangGraph StateGraph 再構築 | DONE | 6f9479ec | 6エージェント, 条件分岐(unknown率>50%→リトライ), ChromaDB自動保存 |

| D4-2 | deep-research CLI (GPT-Researcher代替) | DONE | 6f9479ec | Codex/Copilot/Geminiフォールバック, 自動クエリ分解→マルチ検索→レポート生成 |

| D4-3 | Skills execute アクション | DONE | 6f9479ec | 既存実装で動作確認(evidence-grading callable=true) |

| D4-4 | Commit + push | DONE | 6f9479ec | |



\*\*D4テスト結果\*\*:

\- `orchestrate run --goal "spermidine autophagy aging" --max 3`: 8論文, 2ラウンド検索(条件分岐動作), 43.5秒, ChromaDB 13件 ✅

\- `deep-research "PD-1 immunotherapy resistance mechanisms" --max-sources 9 --no-report`: Geminiでクエリ3分解, 15論文, 46.6秒, ChromaDB 28件 ✅

\- `skills execute --name evidence-grading`: callable=true ✅



\#### Day 5: D5 — Knowledge Management / Export \[NOT STARTED] ← RESUME HERE



| Task | Content | Est. |

|------|---------|------|

| D5-1 | Obsidian Vault → H: 移行 + config.yaml 更新 | 1h |

| D5-2 | GraphRAG 引用ネットワーク可視化 | 2h |

| D5-3 | ログ出力先を H:\\jarvis-data に変更 | 1h |

| D5-4 | openai-agents-python 統合 | 1.5h |

| D5-5 | Commit + push → v1.3.0 | 30min |



\*\*D5-4 注意\*\*: openai-agents-python は OpenAI API キー（有料）が必要。無料枠ポリシーに従い、代替実装またはスキップを検討すること。



\#### Day 6: D6 — Test / QA / Docs \[NOT STARTED]



| Task | Content | Est. |

|------|---------|------|

| D6-1 | pytest テストスイート一括作成 | 3h |

| D6-2 | Streamlit Dashboard 更新 | 1.5h |

| D6-3 | HANDOVER 更新 | 1h |

| D6-4 | README.md 更新 | 30min |



\#### Day 7: D7 — Final / Smoke Test / v2.0.0 \[NOT STARTED]



| Task | Content | Est. |

|------|---------|------|

| D7-1 | 全 CLI コマンド スモークテスト | 2h |

| D7-2 | E2E パイプラインテスト (2 クエリ) | 1.5h |

| D7-3 | バグ修正バッファ | 1.5h |

| D7-4 | pyproject.toml version → v2.0.0 | 30min |

| D7-5 | 最終コミット + プッシュ + git tag v2.0.0 | 30min |



---



\## 5. Files Created/Modified in D1–D4



\### New Files (D3–D4)



| File | Content |

|------|---------|

| jarvis\_core/embeddings/paper\_store.py | ChromaDB high-level PaperStore (text query, upsert, search, add\_from\_json) |

| jarvis\_core/rag/\_\_init\_\_.py | Empty init for rag package |

| jarvis\_core/rag/lightrag\_engine.py | LightRAG wrapper with Codex→Copilot→Gemini fallback, local embedding |

| jarvis\_core/pdf/\_\_init\_\_.py | Empty init for pdf package |

| jarvis\_core/pdf/mineru\_client.py | MinerU API + PyMuPDF4LLM fallback PDF→Markdown converter |

| jarvis\_cli/pdf\_extract.py | CLI handler for pdf-extract command |

| jarvis\_cli/deep\_research.py | Autonomous deep research with Codex/Copilot/Gemini fallback chain |

| jarvis\_cli/citation.py | CLI handler for citation command |

| scripts/test\_d3\_1\_chroma.py | ChromaDB PaperStore test (4/4 passed) |

| scripts/test\_d3\_2\_lightrag.py | LightRAG engine test |



\### New Files (D1–D2, from HANDOVER\_v6)



| File | Content |

|------|---------|

| jarvis\_core/llm/litellm\_client.py | LiteLLM unified client (completion + completion\_structured) |

| jarvis\_core/llm/structured\_models.py | 5 Pydantic models for LLM outputs |

| scripts/write\_d1\_\*.py, scripts/write\_d2\_\*.py | Build/test scripts |

| scripts/test\_d1\_\*.py, scripts/test\_d2\_\*.py | Test scripts |



\### Modified Files (D3–D4)



| File | Change |

|------|--------|

| jarvis\_cli/\_\_init\_\_.py | 20→21 commands (added pdf-extract, deep-research) |

| jarvis\_cli/orchestrate.py | Full rewrite: linear 5-agent → LangGraph StateGraph 6-agent with conditional edges |

| jarvis\_cli/semantic\_search.py | ChromaDB persistence added (--db, --index-only, --legacy flags) |

| .gitignore | Added .chroma/, .lightrag/, test\_paper.pdf, test\_paper.md |



---



\## 6. Current config.yaml



```yaml

obsidian:

&nbsp; vault\_path: C:\\Users\\kaneko yu\\Documents\\ObsidianVault

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

&nbsp; logs\_dir: logs

&nbsp; exports\_dir: exports

&nbsp; pdf\_archive\_dir: pdf-archive

&nbsp; local\_fallback: logs

7\. CLI Commands (21 commands, all working)

\#	Command	Example	Status

1	run	jarvis run --goal "..." --category generic	OK

2	search	jarvis search "PD-1" --max 5 --sources pubmed,s2	OK

3	merge	jarvis merge file1.json file2.json -o merged.json	OK

4	note	jarvis note input.json --provider gemini --obsidian	OK

5	citation	jarvis citation input.json	OK

6	citation-stance	jarvis citation-stance input.json \[--no-llm]	OK

7	prisma	jarvis prisma file1.json file2.json -o prisma.md	OK

8	evidence	jarvis evidence input.json \[--use-llm]	OK

9	score	jarvis score input.json	OK

10	screen	jarvis screen input.json \[--auto] \[--batch-size 5]	OK

11	browse	jarvis browse URL \[--json] \[--output file.json]	OK

12	skills	jarvis skills list/match/show/context/execute	OK

13	mcp	jarvis mcp servers/tools/invoke/status	OK

14	orchestrate	jarvis orchestrate run --goal "..." --max 5	OK (LangGraph)

15	obsidian-export	jarvis obsidian-export input.json	OK

16	semantic-search	jarvis semantic-search "query" \[--db file.json] --top 10	OK (ChromaDB)

17	contradict	jarvis contradict input.json \[--use-llm]	OK

18	zotero-sync	jarvis zotero-sync input.json	OK

19	pdf-extract	jarvis pdf-extract file.pdf \[--mode fast]	OK (PyMuPDF)

20	deep-research	jarvis deep-research "goal" --max-sources 20	OK (Codex/Copilot/Gemini)

21	pipeline	jarvis pipeline "query" --max 20 --obsidian --zotero	OK

8\. Important Import Paths

Copy# Sources

from jarvis\_core.sources.unified\_source\_client import UnifiedSourceClient, SourceType



\# Evidence (classify\_evidence does NOT exist)

from jarvis\_core.evidence import grade\_evidence



\# Paper Scoring

from jarvis\_cli.score import score\_papers



\# MCP Hub

from jarvis\_core.mcp.hub import MCPHub



\# Skills

from jarvis\_core.skills.engine import SkillsEngine



\# Browser Agent

from jarvis\_cli.browse import run\_browse, extract\_metadata



\# Orchestrate (DO NOT import jarvis\_core.agents.orchestrator)

from jarvis\_cli.orchestrate import run\_orchestrate



\# LLM (D1)

from jarvis\_core.llm.litellm\_client import completion, completion\_structured

from jarvis\_core.llm.structured\_models import (

&nbsp;   EvidenceGradeLLM, PaperSummaryLLM, ContradictionResultLLM, CitationStanceLLM

)



\# ChromaDB PaperStore (D3-1)

from jarvis\_core.embeddings.paper\_store import PaperStore



\# LightRAG (D3-2)

from jarvis\_core.rag.lightrag\_engine import JarvisLightRAG



\# PDF extraction (D3-3)

from jarvis\_core.pdf.mineru\_client import MinerUClient



\# Deep Research (D4-2)

from jarvis\_cli.deep\_research import run\_deep\_research



\# Obsidian / Zotero / PRISMA / BibTeX

from jarvis\_cli.obsidian\_export import export\_papers\_to\_obsidian

from jarvis\_cli.zotero\_sync import \_get\_zotero\_client, \_build\_zotero\_item

from jarvis\_cli.prisma import run\_prisma

from jarvis\_cli.bibtex import save\_bibtex

Copy

9\. ChromaDB Status

Persist directory: C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\.chroma

Collection: jarvis\_papers (cosine distance)

Current count: ~28 papers (5 from D3-1 test + 8 from orchestrate test + 15 from deep-research test)

Embedding: ChromaDB built-in all-MiniLM-L6-v2 (automatic, no manual embedding needed)

.chroma/ is in .gitignore

10\. LightRAG Status

Working directory: C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\.lightrag

LLM fallback chain: Codex CLI → Copilot CLI → Gemini API

Embedding: local sentence-transformers all-MiniLM-L6-v2

Entity extraction: WORKS (8 entities, 6 relations extracted via Gemini)

Graph persistence: FAILS (asyncio.CancelledError during merge phase)

LLM cache: kv\_store\_llm\_response\_cache.json is saved (rerun will skip API calls)

.lightrag/ is in .gitignore

11\. MCP Hub Tool Status (5 servers, 15 tools)

Server	Tool	Handler	Tested

pubmed	pubmed\_search	YES	PASS

pubmed	pubmed\_fetch	NO	—

pubmed	pubmed\_citations	NO	—

openalex	openalex\_search	YES (per\_page fixed)	PASS

openalex	openalex\_work	YES (D2-4 new)	untested

openalex	openalex\_author	NO	—

openalex	openalex\_institution	NO	—

semantic\_scholar	s2\_search	YES (429 retry)	PASS

semantic\_scholar	s2\_paper	YES (429 retry)	untested

semantic\_scholar	s2\_citations	YES (D2-4)	untested

semantic\_scholar	s2\_references	YES (D2-4)	untested

arxiv	arxiv\_search	YES	PASS

arxiv	arxiv\_fetch	NO	—

crossref	crossref\_search	YES	PASS

crossref	crossref\_doi	YES (D2-4 new)	untested

12\. Known Issues (MUST READ)

agents.py vs agents/ conflict: jarvis\_core/agents.py (file) and jarvis\_core/agents/ (dir) coexist. DO NOT import from jarvis\_core.agents.orchestrator. orchestrate.py uses modules directly.



Scrapling: css\_first() does NOT exist. Use css("selector")\[0]. Helper \_first(page, sel) wraps this in browse.py.



PowerShell 5.1 JSON: Inline JSON breaks. Use --params-file for MCP invoke.



init.py edits: jarvis\_cli/\_\_init\_\_.py MUST be overwritten entirely. No partial inserts.



PubMed browse abstract: JS-rendered, Scrapling cannot extract. Jina Reader fallback added but may return nav text. Pipeline uses API for abstracts, so low impact.



Rate limits:



Gemini: 15 RPM / 1500 req/day free tier. Add time.sleep(3) between API calls.

Semantic Scholar: 100 req/5min (retry implemented in hub.py).

LightRAG needs 4-6 LLM calls per paper → rate limit is bottleneck for bulk insertion.

Root init.py: Was accidentally overwritten once; restored with git restore. Do not modify.



OpenAlexClient.search(): Parameter is per\_page, NOT max\_results. Fixed in hub.py.



Legacy LLMClient: jarvis\_core.llm.llm\_utils may not be directly importable. Use litellm\_client.py instead.



Datalab.to MinerU API: Returns 403 Forbidden (requires paid subscription). Always falls back to PyMuPDF4LLM which works fine.



LightRAG graph persistence: asyncio.CancelledError prevents .graphml file writing. LLM cache is saved. Retry in a low-traffic Gemini window or when rate limits are relaxed.



Codex/Copilot CLI for LightRAG: Long LightRAG prompts (entity extraction templates, thousands of chars) cause Codex CLI to timeout and Copilot CLI to skip. Only Gemini API successfully handles these prompts.



Python version: HANDOVER\_v6.md says 3.12.3, actual is 3.11.9. Use 3.11.9.



13\. Absolute Rules for Implementation

Never use python -c "..." for complex code. Always create .py files.

jarvis\_cli/\_\_init\_\_.py: full overwrite only. No partial inserts.

Package install: python -m pip install only.

DO NOT import jarvis\_core.agents.orchestrator.

Scrapling: no css\_first(). Use css("sel")\[0].

MCP JSON: use --params-file, not inline JSON.

File creation: Notepad method (notepad path → paste → Ctrl+S → close → python path).

Avoid triple-quotes inside triple-quoted strings in write\_\*.py scripts.

Gemini 15 RPM limit: add time.sleep(3) between API calls.

OpenAlexClient.search() uses per\_page, not max\_results.

Free tier only: Do not use paid APIs (OpenAI API, Datalab.to, etc.).

User work style: copy-paste command → Enter → verify result. Minimize human error.

Limit ≤6 hours per day, aim to finish within one week total.

14\. LLM Fallback Chain Pattern

Used in deep\_research.py and lightrag\_engine.py:



1\. Codex CLI (codex exec - via stdin pipe, cwd=PROJECT\_DIR)

2\. Copilot CLI (copilot -p "prompt", --model for model selection)

3\. Gemini API (gemini/gemini-2.0-flash via LiteLLM, with 429 retry)

Codex/Copilot are free (ChatGPT Plus / Education Pro), no API key needed. Gemini is free tier (15 RPM, 1500 req/day).



15\. Smoke Test (run at session start)

Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1

python --version

git log --oneline -5

python -m jarvis\_cli --help

python -c "from jarvis\_core.llm.litellm\_client import completion; print('LiteLLM OK')"

python -c "from jarvis\_core.embeddings.paper\_store import PaperStore; s=PaperStore(); print(f'ChromaDB OK, count={s.count()}')"

python -m jarvis\_cli orchestrate status

python -m jarvis\_cli semantic-search "autophagy" --top 3

Expected: Python 3.11.9, 21 CLI commands, LiteLLM OK, ChromaDB ~28 papers, LangGraph status, semantic-search returns results.



16\. Directory Structure (key files only)

jarvis-ml-pipeline/

├── .env                          # API keys (gitignored)

├── .gitignore                    # includes .chroma/, .lightrag/

├── config.yaml                   # project configuration

├── pyproject.toml                # package definition

├── JARVIS\_EXPANSION\_PLAN\_v1.md   # full expansion plan D1-D7

├── HANDOVER\_v6.md                # previous handover (D1/D2)

├── HANDOVER\_v7.md                # THIS FILE (D1-D4)

├── jarvis\_cli/

│   ├── \_\_init\_\_.py               # CLI entry point (21 commands)

│   ├── browse.py                 # URL metadata extraction

│   ├── citation.py               # Citation count fetcher

│   ├── citation\_stance.py        # Citation stance classifier

│   ├── contradict.py             # Contradiction detector

│   ├── deep\_research.py          # D4-2: Autonomous deep research

│   ├── evidence.py               # Evidence grading

│   ├── mcp.py                    # MCP Hub CLI

│   ├── merge.py                  # JSON merger

│   ├── note.py                   # Research note generator

│   ├── obsidian\_export.py        # Obsidian vault exporter

│   ├── orchestrate.py            # D4-1: LangGraph orchestrator

│   ├── pdf\_extract.py            # D3-3: PDF→Markdown CLI

│   ├── pipeline.py               # Full pipeline

│   ├── prisma.py                 # PRISMA diagram generator

│   ├── score.py                  # Paper quality scorer

│   ├── screen.py                 # Active learning screening

│   ├── search.py                 # Paper search

│   ├── semantic\_search.py        # D3-1: ChromaDB semantic search

│   ├── skills.py                 # Skills management

│   └── zotero\_sync.py            # Zotero sync

├── jarvis\_core/

│   ├── embeddings/

│   │   ├── paper\_store.py        # D3-1: ChromaDB PaperStore

│   │   ├── chroma\_store.py       # v1.0 low-level ChromaVectorStore

│   │   ├── vector\_store.py       # Abstract VectorStore base

│   │   ├── bm25.py, hybrid.py, model.py, embedder.py

│   │   ├── sentence\_transformer.py, specter2.py

│   │   └── \_\_init\_\_.py

│   ├── llm/

│   │   ├── litellm\_client.py     # D1-2: LiteLLM unified client

│   │   ├── structured\_models.py  # D1-3: Pydantic models

│   │   └── (adapter.py, ensemble.py, model\_router.py, etc.)

│   ├── mcp/

│   │   └── hub.py                # MCP Hub (15 tools, 5 servers)

│   ├── pdf/

│   │   ├── mineru\_client.py      # D3-3: MinerU + PyMuPDF fallback

│   │   └── \_\_init\_\_.py

│   ├── rag/

│   │   ├── lightrag\_engine.py    # D3-2: LightRAG wrapper

│   │   └── \_\_init\_\_.py

│   ├── skills/

│   │   ├── engine.py             # Skills engine

│   │   └── schema.py

│   ├── sources/

│   │   └── unified\_source\_client.py  # Multi-source search

│   └── evidence.py               # CEBM evidence grading

├── scripts/

│   ├── test\_d3\_1\_chroma.py       # ChromaDB test

│   ├── test\_d3\_2\_lightrag.py     # LightRAG test

│   └── (other build/test scripts)

└── logs/

&nbsp;   ├── orchestrate/              # Orchestration results JSON

&nbsp;   └── deep\_research/            # Deep research results JSON + reports

17\. Available AI Tools

Tool	Plan	Model	Purpose

Gemini API	Google AI Pro (2TB Drive)	gemini-2.0-flash	Built-in LLM (free 15 RPM)

Codex CLI	ChatGPT Plus ($20/mo)	GPT-5.3-Codex	Code automation (free with Plus)

Copilot CLI	Education Pro (free)	Claude Sonnet 4.6 etc.	Code gen/review (free)

Claude (chat)	—	Claude Opus 4.6	Design/planning/handover

18\. Next Action: Resume from Day 5 (D5)

See JARVIS\_EXPANSION\_PLAN\_v1.md for full task specs.



Important considerations for D5:



D5-1: Verify H: drive is accessible before Obsidian migration

D5-2: GraphRAG can use networkx (already installed via LightRAG dependencies) for citation network

D5-3: Verify H:\\マイドライブ\\jarvis-data\\ path exists

D5-4: openai-agents-python requires OpenAI API key (paid) → skip or build alternative

D5-5: Tag as v1.3.0



---


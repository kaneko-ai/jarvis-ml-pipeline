\# HANDOVER\_v8.md — JARVIS Research OS Handover v8



\*\*Date\*\*: 2026-03-04

\*\*Previous\*\*: HANDOVER\_v7.md (2026-03-03, commit 6f9479ec)

\*\*Repository\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline

\*\*Branch\*\*: main

\*\*Latest pushed commit\*\*: 0d5d7999 — D5: Obsidian/storage H: migration, citation network, storage\_utils, 22 CLI commands (tag: v1.3.0)

\*\*Related repo\*\*: https://github.com/kaneko-ai/zotero-doi-importer

\*\*Expansion plan\*\*: JARVIS\_EXPANSION\_PLAN\_v1.md (in repo root)



\*\*Purpose\*\*: Any AI or developer reading this can continue implementation with zero additional questions.



---



\## 1. Project Overview



JARVIS Research OS automates Systematic Literature Reviews. One CLI command runs: paper search, dedup, evidence grading, scoring, LLM Japanese summary, Obsidian notes, Zotero sync, PRISMA diagram, BibTeX output, citation network visualization.



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

| Project path | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| venv | `.venv` (project root) |

| venv activate | `.\\.venv\\Scripts\\Activate.ps1` |

| Obsidian Vault | `H:\\マイドライブ\\obsidian-vault` (migrated D5-1) |

| Logs/Exports | `H:\\マイドライブ\\jarvis-data\\` (migrated D5-3) |

| C: free | ~45 GB / 460 GB |

| H: drive | Google Drive 2TB (personal, kanekiti1125@gmail.com) |

| GPU | None (Intel Iris Plus Graphics) |

| RAM | 16 GB LPDDR4x |

| CPU | Intel i7-1065G7 (4C/8T) |



\### 2.1 Environment Variables (.env)



.env is at project root, excluded from Git.



Copy

GEMINI\_API\_KEY=<39-char key> LLM\_PROVIDER=gemini ZOTERO\_API\_KEY=<issued 2026-03-02> ZOTERO\_USER\_ID=16956010 OPENAI\_API\_KEY= DEEPSEEK\_API\_KEY= LLM\_MODEL=gemini/gemini-2.0-flash DATALAB\_API\_KEY=<present but 403>





\### 2.2 Key Installed Packages



v1.0.0: jarvis-research-os, google-genai, python-dotenv, rank-bm25, sentence-transformers, pyzotero, streamlit, rapidfuzz, scikit-learn, pyyaml, scrapling, beautifulsoup4

D1: litellm, openai, pydantic-ai, instructor, tiktoken, aiohttp

D3: chromadb, lightrag-hku, pymupdf4llm

D4: langgraph

D6: pytest, pytest-timeout



---



\## 3. Commit History



0d5d7999 D5: Obsidian/storage H: migration, citation network, 22 CLI commands (tag: v1.3.0) <- LATEST 6f9479ec D4: LangGraph orchestrator, deep-research CLI, skills execute (tag: implied) 8da82646 D3: ChromaDB PaperStore, LightRAG engine, PDF-to-Markdown (tag: v1.2.0) 8e11f4ef docs: HANDOVER\_v6.md 40fff89f D2: browse.py Jina fallback + authors dedup, MCP handlers (tag: v1.1.0) fb63f6fe D1: LiteLLM + Instructor + PydanticAI





---



\## 4. Task Completion Map



\### D1–D4: ALL DONE (see HANDOVER\_v7.md)



\### D5 — Knowledge Management / Export \[DONE]



| Task | Content | Status | Notes |

|------|---------|--------|-------|

| D5-1 | Obsidian Vault → H: migration + config.yaml | DONE | 93 files migrated |

| D5-2 | CitationGraph + citation-graph CLI | DONE | networkx, Mermaid/GraphML/Obsidian MD output |

| D5-3 | Storage paths → H:\\jarvis-data | DONE | storage\_utils.py + 3 file patches |

| D5-4 | openai-agents-python | SKIPPED | Paid API; built citation\_enricher instead (S2 API, 89 nodes/75 edges) |

| D5-5 | Commit + push → v1.3.0 | DONE | 0d5d7999 |



\### D6 — Test / QA / Docs \[IN PROGRESS]



| Task | Content | Status | Notes |

|------|---------|--------|-------|

| D6-1 | pytest test suite | DONE | 7 test files, 50/50 passed |

| D6-2 | Streamlit Dashboard | DONE | 5-page dashboard (Overview/Search/Citation/ChromaDB/Storage) |

| D6-3 | HANDOVER\_v8.md | DONE | This file |

| D6-4 | README.md update | TODO | |



\### D7 — Final / Smoke Test / v2.0.0 \[NOT STARTED]



| Task | Content | Est. |

|------|---------|------|

| D7-1 | All CLI commands smoke test | 2h |

| D7-2 | E2E pipeline test (2 queries) | 1.5h |

| D7-3 | Bug fix buffer | 1.5h |

| D7-4 | pyproject.toml version → v2.0.0 | 30min |

| D7-5 | Final commit + push + git tag v2.0.0 | 30min |



---



\## 5. Files Created/Modified in D5–D6



\### New Files (D5)



| File | Content |

|------|---------|

| jarvis\_core/rag/citation\_graph.py | CitationGraph: build, analyze (PageRank/clusters), export (GraphML/Mermaid/Obsidian MD) |

| jarvis\_core/rag/citation\_enricher.py | S2 API citation/reference fetcher + auto graph builder |

| jarvis\_core/storage\_utils.py | get\_logs\_dir/get\_exports\_dir/get\_pdf\_archive\_dir with H: fallback |

| jarvis\_cli/citation\_graph.py | CLI handler for citation-graph command |

| scripts/patch\_d5\_3\_storage.py | Patch script for storage migration |



\### New Files (D6)



| File | Content |

|------|---------|

| jarvis\_web/streamlit\_app.py | 5-page Streamlit dashboard |

| tests/conftest.py | Shared fixtures (sample\_papers, sample\_papers\_json) |

| tests/test\_imports.py | 19 import tests (core + CLI) |

| tests/test\_citation\_graph.py | 12 CitationGraph tests |

| tests/test\_storage\_utils.py | 5 storage utils tests |

| tests/test\_paperstore\_d6.py | 4 PaperStore tests |

| tests/test\_evidence.py | 4 evidence grading tests |

| tests/test\_cli\_commands.py | 6 CLI command tests |



\### Modified Files (D5)



| File | Change |

|------|--------|

| config.yaml | obsidian.vault\_path → H:, storage.logs\_dir/exports\_dir/pdf\_archive\_dir → H: |

| jarvis\_cli/\_\_init\_\_.py | 21→22 commands (added citation-graph) |

| jarvis\_cli/pipeline.py | log\_dir → storage\_utils.get\_logs\_dir("pipeline") |

| jarvis\_cli/orchestrate.py | log\_dir → storage\_utils.get\_logs\_dir("orchestrate") |

| jarvis\_cli/deep\_research.py | log\_dir → storage\_utils.get\_logs\_dir("deep\_research") |



---



\## 6. CLI Commands (22 commands)



| # | Command | Status |

|---|---------|--------|

| 1 | run | OK |

| 2 | search | OK |

| 3 | merge | OK |

| 4 | note | OK |

| 5 | citation | OK |

| 6 | citation-stance | OK |

| 7 | prisma | OK |

| 8 | evidence | OK |

| 9 | score | OK |

| 10 | screen | OK |

| 11 | browse | OK |

| 12 | skills | OK |

| 13 | mcp | OK |

| 14 | orchestrate | OK (LangGraph) |

| 15 | obsidian-export | OK |

| 16 | semantic-search | OK (ChromaDB) |

| 17 | contradict | OK |

| 18 | zotero-sync | OK |

| 19 | pdf-extract | OK (PyMuPDF) |

| 20 | deep-research | OK (Codex/Copilot/Gemini) |

| 21 | citation-graph | OK (D5-2, networkx) |

| 22 | pipeline | OK |



---



\## 7. Test Suite Status



D6 new tests: 50/50 passed (pytest 9.0.2, timeout=30s) Existing tests: ~7037 collected (from prior development phases)





Test files:

\- tests/test\_imports.py (19 tests)

\- tests/test\_citation\_graph.py (12 tests)

\- tests/test\_storage\_utils.py (5 tests)

\- tests/test\_paperstore\_d6.py (4 tests)

\- tests/test\_evidence.py (4 tests)

\- tests/test\_cli\_commands.py (6 tests)



---



\## 8. Current config.yaml



```yaml

obsidian:

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

9\. Known Issues (MUST READ)

All issues from HANDOVER\_v7.md Section 12 remain valid. Additional:



Existing test tests/cli/test\_mcp\_skills\_cli.py: Deleted (imported non-existent cmd\_mcp).

Test file name collision: tests/embeddings/test\_chroma\_store.py exists; new PaperStore tests use test\_paperstore\_d6.py.

Rename-Item in PowerShell: New name must NOT contain path separators. Use just filename.

Streamlit ScriptRunContext warnings: Normal when importing outside streamlit run. Ignore.

pytest.ini vs pyproject.toml: pytest.ini takes precedence; pyproject.toml config is ignored.

10\. Absolute Rules (unchanged from v7, section 13)

Never use python -c "..." for complex code. Always create .py files.

jarvis\_cli/\_\_init\_\_.py: full overwrite only.

Package install: python -m pip install only.

DO NOT import jarvis\_core.agents.orchestrator.

Scrapling: no css\_first(). Use css("sel")\[0].

MCP JSON: use --params-file, not inline JSON.

File creation: Notepad method.

Gemini 15 RPM limit: add time.sleep(3).

OpenAlexClient.search() uses per\_page, not max\_results.

Free tier only.

User work style: copy-paste → Enter → verify.

11\. Smoke Test (run at session start)

Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1

python --version

git log --oneline -5

python -m jarvis\_cli --help

python -c "from jarvis\_core.llm.litellm\_client import completion; print('LiteLLM OK')"

python -c "from jarvis\_core.embeddings.paper\_store import PaperStore; s=PaperStore(); print(f'ChromaDB OK, count={s.count()}')"

python -c "from jarvis\_core.rag.citation\_graph import CitationGraph; print('CitationGraph OK')"

python -c "from jarvis\_core.storage\_utils import get\_logs\_dir; print(f'Logs: {get\_logs\_dir()}')"

python -m pytest tests/test\_imports.py -q --timeout=30

Expected: Python 3.11.9, 22 CLI commands, all imports OK, ChromaDB ~28 papers, logs → H: drive, 19/19 tests pass.



12\. Next Action: D6-4 (README update) then D7

D6-4: Update README.md with v1.3.0 features. D7: Full smoke test, E2E test, bug fixes, v2.0.0 release.






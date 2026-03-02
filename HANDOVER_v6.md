\# HANDOVER\_v6.md -- JARVIS Research OS Handover v6



\*\*Date\*\*: 2026-03-03

\*\*Previous\*\*: HANDOVER\_v5.md (2026-03-02, commit 9220dd5a)

\*\*Repository\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline

\*\*Branch\*\*: main

\*\*Latest pushed commit\*\*: 40fff89f -- D2: browse.py Jina fallback + authors dedup, MCP S2/OpenAlex/Crossref handlers

\*\*Related repo\*\*: https://github.com/kaneko-ai/zotero-doi-importer (A-6 done, commit 0cb2447)



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

| Python | 3.12.3 (venv shows cp311) |

| Node.js | v24.13.1 |

| Project path | C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline |

| venv | .venv (project root) |

| venv activate | .\\.venv\\Scripts\\Activate.ps1 |

| Python exe | .venv\\Scripts\\python.exe |

| Obsidian Vault | C:\\Users\\kaneko yu\\Documents\\ObsidianVault |

| C: free | ~45 GB / 460 GB |

| H: drive | Google Drive 2TB (personal) |

| G: drive | Google Drive 100GB (student, not used by JARVIS) |

| GPU | None (Intel Iris Plus) |

| RAM | 16 GB LPDDR4x |

| CPU | Intel i7-1065G7 (4C/8T) |



\### 2.1 Environment Variables (.env)



.env is at project root, excluded from Git.



GEMINI\_API\_KEY=<39-char key>

LLM\_PROVIDER=gemini

ZOTERO\_API\_KEY=<issued 2026-03-02>

ZOTERO\_USER\_ID=16956010

OPENAI\_API\_KEY=

DEEPSEEK\_API\_KEY=

LLM\_MODEL=gemini/gemini-2.0-flash



\### 2.2 Installed Packages (.venv)



\*\*v1.0.0\*\*: jarvis-research-os==1.0.0, google-genai==1.65.0, python-dotenv==1.2.2, rank-bm25==0.2.2, sentence-transformers (MiniLM-L6-v2), pyzotero, requests==2.32.5, streamlit==1.54.0, rapidfuzz==3.14.3, scikit-learn, pyyaml, scrapling==0.4.1, beautifulsoup4



\*\*D1 added\*\*: litellm==1.82.0, openai==2.24.0, pydantic-ai==1.63.0, instructor==1.14.5, tiktoken==0.12.0, aiohttp==3.13.3



\### 2.3 AI CLI Tools Installed



| Tool | Version | Auth | Purpose |

|------|---------|------|---------|

| Codex CLI | 0.106.0 | ChatGPT Plus authenticated | Code generation, GPT-5.3-Codex |

| Copilot CLI | 0.0.420 | Education Pro authenticated | Code gen/review, Claude Sonnet 4.6 etc |



\### 2.4 NOT Installed



| Component | Status | Note |

|-----------|--------|------|

| Ollama | Not installed | use\_llm=False workaround |

| Crawl4AI | Skipped (D2-3) | Playwright+Chromium too heavy; Jina Reader instead |

| pandas 3.0.0 | Install failed | Not needed |



---



\## 3. Commit History



40fff89f D2: browse.py Jina fallback + authors dedup, MCP handlers <- LATEST

fb63f6fe D1: LiteLLM + Instructor + PydanticAI

ea48d91d docs: JARVIS\_EXPANSION\_PLAN\_v1.md

ab602b75 HANDOVER\_v5.md

9220dd5a C-4: Multi-Agent Orchestrator

7320bbe6 C-1: MCP Hub

cf73f002 C-3: Skills System

5564623e C-2: Browser Agent

f13ddbf4 C-6: pipeline zotero collection

c7f24014 C-6: Zotero collection support

024a1a86 B-6: Streamlit + C-5: arXiv/Crossref

18941276 Phase B: B-5/B-3/B-1/B-2/B-4

5c043b02 Phase A: A-1/A-2/A-3/A-4/A-5



---



\## 4. Task Completion Map



\### v1.0.0 (Phase v2/A/B/C) -- ALL 26 TASKS DONE



All completed and pushed. See HANDOVER\_v5.md section 3 for details.



\### v2.0.0 Expansion Tasks (D1-D7)



\#### Day 1: D1 -- AI Tools + LLM Foundation \[DONE]



| Task | Content | Status | Commit |

|------|---------|--------|--------|

| D1-1 | Codex CLI 0.106.0 + Copilot CLI 0.0.420 install/auth | DONE | fb63f6fe |

| D1-2 | LiteLLM 1.82.0 + config.yaml llm.models section | DONE | fb63f6fe |

| D1-3 | PydanticAI 1.63.0 + Instructor 1.14.5 + 5 Pydantic models | DONE | fb63f6fe |

| D1-4 | LLM provider test: Structured Output PASS | DONE | fb63f6fe |

| D1-5 | Commit + push | DONE | fb63f6fe |



D1-4 test details:

\- Gemini via LiteLLM: 429 RateLimitError (temporary RPM limit, key is valid)

\- Structured Output (Instructor+Gemini): PASS (Japanese title/summary/score returned)

\- Legacy LLMClient: FAIL (module path issue, no impact since migrating to LiteLLM)



\#### Day 2: D2 -- Scraping/Browse Enhancement \[DONE]



| Task | Content | Status | Commit |

|------|---------|--------|--------|

| D2-1 | browse.py: PubMed abstract 4-selector fallback, authors dedup | DONE | 40fff89f |

| D2-2 | Jina Reader API fallback for PubMed/Generic/fetch-fail | DONE | 40fff89f |

| D2-3 | Crawl4AI | SKIPPED | Playwright too heavy, Jina Reader instead |

| D2-4 | MCP: S2 4 tools + OpenAlex work + Crossref DOI + S2 429 retry | DONE | 40fff89f |

| D2-5 | Commit + push | DONE | 40fff89f |



D2-4 test: openalex\_search OK (3020ms), s2\_search OK (1462ms), 2/2 PASS



\#### Day 3: D3 -- RAG / Vector DB / PDF \[NOT STARTED] <- RESUME HERE



| Task | Content | Est. |

|------|---------|------|

| D3-1 | ChromaDB + semantic-search persistence | 2h |

| D3-2 | LightRAG + graph construction | 2h |

| D3-3 | MinerU API (PDF to Markdown) | 1.5h |

| D3-4 | Commit + push -> v1.2.0 | 30min |



\#### Day 4: D4 -- Agent/Orchestrator Enhancement \[NOT STARTED]



| Task | Content | Est. |

|------|---------|------|

| D4-1 | orchestrate.py -> LangGraph-based rebuild | 3h |

| D4-2 | GPT-Researcher integration (Deep Research mode) | 2h |

| D4-3 | Skills execute action | 1h |

| D4-4 | Commit + push | -- |



\#### Day 5: D5 -- Knowledge Management / Export \[NOT STARTED]



| Task | Content | Est. |

|------|---------|------|

| D5-1 | Obsidian Vault -> H: migration + config.yaml | 1h |

| D5-2 | GraphRAG citation network visualization | 2h |

| D5-3 | Log output -> H:\\jarvis-data | 1h |

| D5-4 | openai-agents-python integration | 1.5h |

| D5-5 | Commit + push -> v1.3.0 | 30min |



\#### Day 6: D6 -- Test / QA / Docs \[NOT STARTED]



| Task | Content | Est. |

|------|---------|------|

| D6-1 | pytest test suite | 3h |

| D6-2 | Streamlit Dashboard update | 1.5h |

| D6-3 | HANDOVER\_v7.md | 1h |

| D6-4 | README.md update | 30min |



\#### Day 7: D7 -- Final / Smoke Test / v2.0.0 \[NOT STARTED]



| Task | Content | Est. |

|------|---------|------|

| D7-1 | All CLI smoke test | 2h |

| D7-2 | E2E pipeline test (2 queries) | 1.5h |

| D7-3 | Bug fix buffer | 1.5h |

| D7-4 | pyproject.toml version -> v2.0.0 | 30min |

| D7-5 | Final commit + push + git tag v2.0.0 | 30min |



---



\## 5. Files Created/Modified in D1-D2



\### New Files



| File | Size | Content |

|------|------|---------|

| jarvis\_core/llm/litellm\_client.py | 1,532 B | LiteLLM unified client (completion + completion\_structured) |

| jarvis\_core/llm/structured\_models.py | 1,296 B | 5 Pydantic models |

| scripts/write\_d1\_2\_litellm.py | -- | litellm\_client.py generator |

| scripts/write\_d1\_2\_config.py | -- | config.yaml updater |

| scripts/write\_d1\_2\_env.py | -- | .env updater |

| scripts/write\_d1\_3\_models.py | -- | structured\_models.py generator |

| scripts/test\_d1\_3\_imports.py | -- | D1-3 import test |

| scripts/test\_d1\_4\_providers.py | -- | D1-4 LLM provider test |

| scripts/write\_d1\_5\_gitignore.py | -- | .gitignore updater |

| scripts/write\_d2\_browse.py | -- | browse.py generator |

| scripts/write\_d2\_hub.py | -- | hub.py generator |

| scripts/write\_d2\_hub\_fix.py | -- | hub.py patch (OpenAlex arg fix + S2 retry) |

| scripts/test\_d2\_mcp.py | -- | D2-4 MCP handler test |



\### Modified Files



| File | Change |

|------|--------|

| jarvis\_cli/browse.py | 11441->13750 B. PubMed 4-selector, authors dedup, Jina fallback |

| jarvis\_core/mcp/hub.py | +s2 4 tools, +openalex\_work, +crossref\_doi, per\_page fix, S2 429 retry |

| config.yaml | +llm section (models dict), +storage section |

| .gitignore | +write\_\*.py, fix\_\*.py, check\_\*.py patterns |

| .env | +OPENAI\_API\_KEY, DEEPSEEK\_API\_KEY, LLM\_MODEL |



---



\## 6. Current config.yaml



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



---



\## 7. CLI Commands (20 commands, all working)



| Command | Example | Status |

|---------|---------|--------|

| search | jarvis search "PD-1" --max 5 --sources pubmed,s2,openalex,arxiv,crossref | OK |

| merge | jarvis merge file1.json file2.json -o merged.json | OK |

| note | jarvis note input.json --provider gemini --obsidian | OK |

| citation | jarvis citation input.json | OK |

| citation-stance | jarvis citation-stance input.json \[--no-llm] | OK |

| prisma | jarvis prisma file1.json file2.json -o prisma.md | OK |

| evidence | jarvis evidence input.json | OK |

| score | jarvis score input.json | OK |

| screen | jarvis screen input.json \[--auto] \[--batch-size 5] | OK |

| obsidian-export | jarvis obsidian-export input.json | OK |

| semantic-search | jarvis semantic-search "query" --db file.json --top 10 | OK |

| contradict | jarvis contradict input.json \[--use-llm] | OK |

| zotero-sync | jarvis zotero-sync input.json | OK |

| pipeline | jarvis pipeline "query" --max 50 --obsidian --zotero --prisma --bibtex --no-summary | OK |

| browse | jarvis browse URL \[--json] \[--output file.json] | OK |

| skills | jarvis skills list/match/show/context | OK |

| mcp | jarvis mcp servers/tools/invoke/status | OK |

| orchestrate | jarvis orchestrate agents/status/decompose/run | OK |

| run | jarvis run --goal "..." \[--category ...] | OK |

| (bibtex) | via --bibtex flag in search/merge/pipeline | OK |



---



\## 8. Important Import Paths



\# Sources

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



\# LLM -- NEW (D1)

from jarvis\_core.llm.litellm\_client import completion, completion\_structured

from jarvis\_core.llm.structured\_models import (

&nbsp;   EvidenceGradeLLM, PaperSummaryLLM, ContradictionResultLLM, CitationStanceLLM

)



\# Obsidian / Zotero / PRISMA / BibTeX

from jarvis\_cli.obsidian\_export import export\_papers\_to\_obsidian

from jarvis\_cli.zotero\_sync import \_get\_zotero\_client, \_build\_zotero\_item

from jarvis\_cli.prisma import run\_prisma

from jarvis\_cli.bibtex import save\_bibtex



---



\## 9. MCP Hub Tool Status (5 servers, 15 tools)



| Server | Tool | Handler | Tested |

|--------|------|---------|--------|

| pubmed | pubmed\_search | YES | PASS |

| pubmed | pubmed\_fetch | NO | -- |

| pubmed | pubmed\_citations | NO | -- |

| openalex | openalex\_search | YES (per\_page fixed) | PASS |

| openalex | openalex\_work | YES (D2-4 new) | untested |

| openalex | openalex\_author | NO | -- |

| openalex | openalex\_institution | NO | -- |

| semantic\_scholar | s2\_search | YES (429 retry) | PASS |

| semantic\_scholar | s2\_paper | YES (429 retry) | untested |

| semantic\_scholar | s2\_citations | YES (D2-4) | untested |

| semantic\_scholar | s2\_references | YES (D2-4) | untested |

| arxiv | arxiv\_search | YES | PASS |

| arxiv | arxiv\_fetch | NO | -- |

| crossref | crossref\_search | YES | PASS |

| crossref | crossref\_doi | YES (D2-4 new) | untested |



---



\## 10. Known Structural Issues (MUST READ)



1\. agents.py vs agents/ conflict: jarvis\_core/agents.py (file) and jarvis\_core/agents/ (dir) coexist. DO NOT import from jarvis\_core.agents.orchestrator. orchestrate.py uses modules directly.



2\. Scrapling: css\_first() does NOT exist. Use css("selector")\[0]. Helper \_first(page, sel) wraps this in browse.py.



3\. PowerShell 5.1 JSON: Inline JSON breaks. Use --params-file for MCP invoke.



4\. \_\_init\_\_.py edits: jarvis\_cli/\_\_init\_\_.py MUST be overwritten entirely. No partial inserts.



5\. PubMed browse abstract: JS-rendered, Scrapling cannot extract. Jina Reader fallback added but may return nav text. Pipeline uses API for abstracts, so low impact.



6\. Rate limits: Gemini 15 RPM / 1500 req/day. S2 100 req/5min (retry implemented). Add time.sleep(3) between tests.



7\. Root \_\_init\_\_.py: Was accidentally overwritten; restored with git restore (D1-5). Do not modify.



8\. OpenAlexClient.search(): Parameter is per\_page, NOT max\_results. Fixed in hub.py.



9\. Legacy LLMClient: jarvis\_core.llm.llm\_utils may not be directly importable. Use litellm\_client.py instead.



---



\## 11. jarvis\_core/llm/ Directory



jarvis\_core/llm/

&nbsp; \_\_init\_\_.py          (1,074 B)

&nbsp; adapter.py           (1,869 B)

&nbsp; ensemble.py          (8,646 B)

&nbsp; litellm\_client.py    (1,532 B)  \[D1-2]

&nbsp; llamacpp\_adapter.py  (6,033 B)  unused

&nbsp; model\_router.py      (9,589 B)

&nbsp; ollama\_adapter.py    (9,413 B)  unused

&nbsp; structured\_models.py (1,296 B)  \[D1-3]



---



\## 12. Smoke Test (run at session start)



cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1

python -c "import sys; print(sys.executable)"

git log --oneline -5

python -m jarvis\_cli --help

python scripts\\test\_d1\_3\_imports.py

python scripts\\test\_d2\_mcp.py

python -m jarvis\_cli browse https://arxiv.org/abs/2005.12402

python -m jarvis\_cli pipeline "autophagy" --max 3 --no-summary



---



\## 13. Absolute Rules for Implementation



1\. Never use python -c "..." for complex code. Always create .py files.

2\. jarvis\_cli/\_\_init\_\_.py: full overwrite only. No partial inserts.

3\. Package install: python -m pip install only.

4\. DO NOT import jarvis\_core.agents.orchestrator.

5\. Scrapling: no css\_first(). Use css("sel")\[0].

6\. MCP JSON: use --params-file, not inline.

7\. File creation: Notepad method (notepad path -> paste -> Ctrl+S -> close -> python path).

8\. Avoid triple-quotes inside triple-quoted strings in write\_\*.py scripts.

9\. Gemini 15 RPM limit: add time.sleep(3) between API calls.

10\. OpenAlexClient.search() uses per\_page, not max\_results.



---



\## 14. Next Action: Resume from Day 3 (D3)



See JARVIS\_EXPANSION\_PLAN\_v1.md for full task specs with code examples.



---



\## 15. Available AI Tools



| Tool | Plan | Model | Purpose |

|------|------|-------|---------|

| Gemini API | Google AI Pro (2TB Drive) | gemini-2.0-flash | Built-in LLM |

| Codex CLI | ChatGPT Plus ($20/mo) | GPT-5.3-Codex | Code automation |

| Copilot CLI | Education Pro (free) | Claude Sonnet 4.6 etc | Code gen/review |

| Claude (chat) | -- | Claude Opus 4.6 | Design/planning |



---



\## 16. Storage Layout



C: (460 GB / ~45 GB free)

&nbsp; Users\\kaneko yu\\

&nbsp;   Documents\\jarvis-work\\jarvis-ml-pipeline\\  <- project

&nbsp;     .venv\\ (~1.5 GB)

&nbsp;     jarvis\_cli\\

&nbsp;     jarvis\_core\\

&nbsp;     config.yaml

&nbsp;     .env

&nbsp;     scripts\\  <- D1/D2 build/test scripts

&nbsp;   .cache\\huggingface\\ (0.48 GB)

&nbsp;   Zotero\\ (0.47 GB)



H: (Google Drive 2TB / 57 GB used)

&nbsp; jarvis-data\\

&nbsp;   logs\\orchestrate\\

&nbsp;   logs\\pipeline\\

&nbsp;   pdf-archive\\

&nbsp;   exports\\json\\

&nbsp;   exports\\bibtex\\

&nbsp;   exports\\prisma\\

&nbsp;   backup\\



---



\## 17. Related Repositories



| Repository | Purpose | Status |

|-----------|---------|--------|

| https://github.com/kaneko-ai/jarvis-ml-pipeline | Main repo | D1/D2 done |

| https://github.com/kaneko-ai/zotero-doi-importer | Zotero DOI tool | A-6 done |


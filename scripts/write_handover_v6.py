import pathlib

target = pathlib.Path("HANDOVER_v6.md")

part1 = """# HANDOVER_v6.md -- JARVIS Research OS Handover v6

**Date**: 2026-03-03
**Previous**: HANDOVER_v5.md (2026-03-02, commit 9220dd5a)
**Repository**: https://github.com/kaneko-ai/jarvis-ml-pipeline
**Branch**: main
**Latest pushed commit**: 40fff89f -- D2: browse.py Jina fallback + authors dedup, MCP S2/OpenAlex/Crossref handlers
**Related repo**: https://github.com/kaneko-ai/zotero-doi-importer (A-6 done, commit 0cb2447)

**Purpose**: Any AI or developer reading this can continue implementation with zero additional questions.

---

## 1. Project Overview

JARVIS Research OS automates Systematic Literature Reviews. One CLI command runs: paper search, dedup, evidence grading, scoring, LLM Japanese summary, Obsidian notes, Zotero sync, PRISMA diagram, BibTeX output.

**User**: Graduate student (beginner programmer, Windows)
**Use cases**: PD-1 immunotherapy, spermidine, immunosenescence/autophagy research

---

## 2. Development Environment (2026-03-03)

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

### 2.1 Environment Variables (.env)

.env is at project root, excluded from Git.

Copy
GEMINI_API_KEY=<39-char key> LLM_PROVIDER=gemini ZOTERO_API_KEY=<issued 2026-03-02> ZOTERO_USER_ID=16956010 OPENAI_API_KEY= DEEPSEEK_API_KEY= LLM_MODEL=gemini/gemini-2.0-flash


### 2.2 Installed Packages (.venv)

**v1.0.0**: jarvis-research-os==1.0.0, google-genai==1.65.0, python-dotenv==1.2.2, rank-bm25==0.2.2, sentence-transformers (MiniLM-L6-v2), pyzotero, requests==2.32.5, streamlit==1.54.0, rapidfuzz==3.14.3, scikit-learn, pyyaml, scrapling==0.4.1, beautifulsoup4

**D1 added**: litellm==1.82.0, openai==2.24.0, pydantic-ai==1.63.0, instructor==1.14.5, tiktoken==0.12.0, aiohttp==3.13.3

### 2.3 AI CLI Tools Installed

| Tool | Version | Auth | Purpose |
|------|---------|------|---------|
| Codex CLI | 0.106.0 | ChatGPT Plus authenticated | Code generation, GPT-5.3-Codex |
| Copilot CLI | 0.0.420 | Education Pro authenticated | Code gen/review, Claude Sonnet 4.6 etc |

### 2.4 NOT Installed

| Component | Status | Note |
|-----------|--------|------|
| Ollama | Not installed | use_llm=False workaround |
| Crawl4AI | Skipped (D2-3) | Playwright+Chromium too heavy; Jina Reader instead |
| pandas 3.0.0 | Install failed | Not needed |

---

## 3. Commit History

40fff89f D2: browse.py Jina fallback + authors dedup, MCP handlers <- LATEST fb63f6fe D1: LiteLLM + Instructor + PydanticAI ea48d91d docs: JARVIS_EXPANSION_PLAN_v1.md ab602b75 HANDOVER_v5.md 9220dd5a C-4: Multi-Agent Orchestrator 7320bbe6 C-1: MCP Hub cf73f002 C-3: Skills System 5564623e C-2: Browser Agent f13ddbf4 C-6: pipeline zotero collection c7f24014 C-6: Zotero collection support 024a1a86 B-6: Streamlit + C-5: arXiv/Crossref 18941276 Phase B: B-5/B-3/B-1/B-2/B-4 5c043b02 Phase A: A-1/A-2/A-3/A-4/A-5


---

## 4. Task Completion Map

### v1.0.0 (Phase v2/A/B/C) -- ALL 26 TASKS DONE

All completed and pushed. See HANDOVER_v5.md section 3 for details.

### v2.0.0 Expansion Tasks (D1-D7)

#### Day 1: D1 -- AI Tools + LLM Foundation [DONE]

| Task | Content | Status | Commit |
|------|---------|--------|--------|
| D1-1 | Codex CLI 0.106.0 + Copilot CLI 0.0.420 install/auth | DONE | fb63f6fe |
| D1-2 | LiteLLM 1.82.0 + config.yaml llm.models section | DONE | fb63f6fe |
| D1-3 | PydanticAI 1.63.0 + Instructor 1.14.5 + 5 Pydantic models | DONE | fb63f6fe |
| D1-4 | LLM provider test: Structured Output PASS | DONE | fb63f6fe |
| D1-5 | Commit + push | DONE | fb63f6fe |

D1-4 test details:
- Gemini via LiteLLM: 429 RateLimitError (temporary RPM limit, key OK)
- Structured Output (Instructor+Gemini): PASS (Japanese title/summary/score)
- Legacy LLMClient: FAIL (module path issue, no impact since migrating to LiteLLM)

#### Day 2: D2 -- Scraping/Browse Enhancement [DONE]

| Task | Content | Status | Commit |
|------|---------|--------|--------|
| D2-1 | browse.py: PubMed abstract 4-selector fallback, authors dedup | DONE | 40fff89f |
| D2-2 | Jina Reader API fallback for PubMed/Generic/fetch-fail | DONE | 40fff89f |
| D2-3 | Crawl4AI | SKIPPED | -- Playwright too heavy, Jina Reader instead |
| D2-4 | MCP: S2 4 tools + OpenAlex work + Crossref DOI + S2 429 retry | DONE | 40fff89f |
| D2-5 | Commit + push | DONE | 40fff89f |

D2-4 test: openalex_search OK (3020ms), s2_search OK (1462ms), 2/2 PASS

#### Day 3: D3 -- RAG / Vector DB / PDF [NOT STARTED]

| Task | Content | Est. |
|------|---------|------|
| D3-1 | ChromaDB + semantic-search persistence | 2h |
| D3-2 | LightRAG + graph construction | 2h |
| D3-3 | MinerU API (PDF to Markdown) | 1.5h |
| D3-4 | Commit + push -> v1.2.0 | 30min |

#### Day 4: D4 -- Agent/Orchestrator Enhancement [NOT STARTED]

| Task | Content | Est. |
|------|---------|------|
| D4-1 | orchestrate.py -> LangGraph-based rebuild | 3h |
| D4-2 | GPT-Researcher integration (Deep Research mode) | 2h |
| D4-3 | Skills execute action | 1h |
| D4-4 | Commit + push | -- |

#### Day 5: D5 -- Knowledge Management / Export [NOT STARTED]

| Task | Content | Est. |
|------|---------|------|
| D5-1 | Obsidian Vault -> H: migration + config.yaml | 1h |
| D5-2 | GraphRAG citation network visualization | 2h |
| D5-3 | Log output -> H:\\jarvis-data | 1h |
| D5-4 | openai-agents-python integration | 1.5h |
| D5-5 | Commit + push -> v1.3.0 | 30min |

#### Day 6: D6 -- Test / QA / Docs [NOT STARTED]

| Task | Content | Est. |
|------|---------|------|
| D6-1 | pytest test suite | 3h |
| D6-2 | Streamlit Dashboard update | 1.5h |
| D6-3 | HANDOVER_v7.md | 1h |
| D6-4 | README.md update | 30min |

#### Day 7: D7 -- Final / Smoke Test / v2.0.0 [NOT STARTED]

| Task | Content | Est. |
|------|---------|------|
| D7-1 | All CLI smoke test | 2h |
| D7-2 | E2E pipeline test (2 queries) | 1.5h |
| D7-3 | Bug fix buffer | 1.5h |
| D7-4 | pyproject.toml version -> v2.0.0 | 30min |
| D7-5 | Final commit + push + git tag v2.0.0 | 30min |
"""

part2 = ""

## 5. Files Created/Modified in D1-D2

### New Files

 File | Size | Content |
|------|------|---------|
| jarvis_core/llm/litellm_client.py | 1,532 B | LiteLLM unified client (completion + completion_structured) |
| jarvis_core/llm/structured_models.py | 1,296 B | 5 Pydantic models |
| scripts/write_d1_2_litellm.py | -- | litellm_client.py generator |
| scripts/write_d1_2_config.py | -- | config.yaml updater |
| scripts/write_d1_2_env.py | -- | .env updater |
| scripts/write_d1_3_models.py | -- | structured_models.py generator |
| scripts/test_d1_3_imports.py | -- | D1-3 import test |
| scripts/test_d1_4_providers.py | -- | D1-4 LLM provider test |
| scripts/write_d1_5_gitignore.py | -- | .gitignore updater |
| scripts/write_d2_browse.py | -- | browse.py generator |
| scripts/write_d2_hub.py | -- | hub.py generator |
| scripts/write_d2_hub_fix.py | -- | hub.py patch (OpenAlex arg fix + S2 retry) |
| scripts/test_d2_mcp.py | -- | D2-4 MCP handler test |

### Modified Files

| File | Change |
|------|--------|
| jarvis_cli/browse.py | 11,441->13,750 B. PubMed 4-selector, authors dedup, Jina fallback |
| jarvis_core/mcp/hub.py | +s2_search/paper/citations/references, +openalex_work, +crossref_doi, OpenAlex per_page fix, S2 429 retry |
| config.yaml | +llm section (models dict), +storage section |
| .gitignore | +/write_*.py, /fix_*.py, /check_*.py patterns |
| .env | +OPENAI_API_KEY, DEEPSEEK_API_KEY, LLM_MODEL |

---

## 6. Current config.yaml

```yaml
obsidian:
  vault_path: C:\\Users\\kaneko yu\\Documents\\ObsidianVault
  papers_folder: JARVIS/Papers
  notes_folder: JARVIS/Notes
zotero:
  api_key: ''
  user_id: ''
  collection: JARVIS
search:
  default_sources: [pubmed, semantic_scholar, openalex]
  max_results: 20
llm:
  default_provider: gemini
  default_model: gemini/gemini-2.0-flash
  fallback_model: openai/gpt-4.1
  models:
    gemini: gemini/gemini-2.0-flash
    openai: openai/gpt-5-mini
    deepseek: deepseek/deepseek-reasoner
  cache_enabled: true
  max_retries: 3
  temperature: 0.3
evidence:
  use_llm: false
  strategy: weighted_average
storage:
  logs_dir: logs
  exports_dir: exports
  pdf_archive_dir: pdf-archive
  local_fallback: logs
7. CLI Commands (20 commands, all working)
Command	Example	Status
search	jarvis search "PD-1" --max 5 --sources pubmed,s2,openalex,arxiv,crossref	OK
merge	jarvis merge file1.json file2.json -o merged.json	OK
note	jarvis note input.json --provider gemini --obsidian	OK
citation	jarvis citation input.json	OK
citation-stance	jarvis citation-stance input.json [--no-llm]	OK
prisma	jarvis prisma file1.json file2.json -o prisma.md	OK
evidence	jarvis evidence input.json	OK
score	jarvis score input.json	OK
screen	jarvis screen input.json [--auto] [--batch-size 5]	OK
obsidian-export	jarvis obsidian-export input.json	OK
semantic-search	jarvis semantic-search "query" --db file.json --top 10	OK
contradict	jarvis contradict input.json [--use-llm]	OK
zotero-sync	jarvis zotero-sync input.json	OK
pipeline	jarvis pipeline "query" --max 50 --obsidian --zotero --prisma --bibtex --no-summary	OK
browse	jarvis browse URL [--json] [--output file.json]	OK
skills	jarvis skills list/match/show/context	OK
mcp	jarvis mcp servers/tools/invoke/status	OK
orchestrate	jarvis orchestrate agents/status/decompose/run	OK
run	jarvis run --goal "..." [--category ...]	OK
(bibtex)	via --bibtex flag in search/merge/pipeline	OK
8. Important Import Paths
Copy# Sources
from jarvis_core.sources.unified_source_client import UnifiedSourceClient, SourceType

# Evidence (classify_evidence does NOT exist)
from jarvis_core.evidence import grade_evidence

# Paper Scoring
from jarvis_cli.score import score_papers

# MCP Hub
from jarvis_core.mcp.hub import MCPHub

# Skills
from jarvis_core.skills.engine import SkillsEngine

# Browser Agent
from jarvis_cli.browse import run_browse, extract_metadata

# Orchestrate (DO NOT import jarvis_core.agents.orchestrator)
from jarvis_cli.orchestrate import run_orchestrate

# LLM -- NEW (D1)
from jarvis_core.llm.litellm_client import completion, completion_structured
from jarvis_core.llm.structured_models import (
    EvidenceGradeLLM, PaperSummaryLLM, ContradictionResultLLM, CitationStanceLLM
)

# Obsidian / Zotero / PRISMA / BibTeX
from jarvis_cli.obsidian_export import export_papers_to_obsidian
from jarvis_cli.zotero_sync import _get_zotero_client, _build_zotero_item
from jarvis_cli.prisma import run_prisma
from jarvis_cli.bibtex import save_bibtex
Copy
9. MCP Hub Tool Status (5 servers, 15 tools)
Server	Tool	Handler	Tested
pubmed	pubmed_search	YES	PASS
pubmed	pubmed_fetch	NO	--
pubmed	pubmed_citations	NO	--
openalex	openalex_search	YES (per_page fixed)	PASS
openalex	openalex_work	YES (D2-4 new)	untested
openalex	openalex_author	NO	--
openalex	openalex_institution	NO	--
semantic_scholar	s2_search	YES (429 retry)	PASS
semantic_scholar	s2_paper	YES (429 retry)	untested
semantic_scholar	s2_citations	YES (D2-4)	untested
semantic_scholar	s2_references	YES (D2-4)	untested
arxiv	arxiv_search	YES	PASS
arxiv	arxiv_fetch	NO	--
crossref	crossref_search	YES	PASS
crossref	crossref_doi	YES (D2-4 new)	untested
10. Known Structural Issues (MUST READ)
agents.py vs agents/ conflict: jarvis_core/agents.py (file) and jarvis_core/agents/ (dir) coexist. DO NOT import from jarvis_core.agents.orchestrator. orchestrate.py uses modules directly.

Scrapling: css_first() does NOT exist. Use css("selector")[0]. Helper _first(page, sel) wraps this in browse.py.

PowerShell 5.1 JSON: Inline JSON breaks. Use --params-file for MCP invoke.

init.py edits: jarvis_cli/init.py MUST be overwritten entirely. No partial inserts.

PubMed browse abstract: JS-rendered, Scrapling cannot extract. Jina Reader fallback added but may return nav text. Pipeline uses API for abstracts, so low impact.

Rate limits: Gemini 15 RPM / 1500 req/day. S2 100 req/5min (retry implemented). Add time.sleep(3) between tests.

Root init.py: Was accidentally overwritten; restored with git restore (D1-5). Do not modify.

OpenAlexClient.search(): Parameter is per_page, NOT max_results. Fixed in hub.py.

Legacy LLMClient: jarvis_core.llm.llm_utils may not be directly importable. Use litellm_client.py instead.

11. jarvis_core/llm/ Directory
jarvis_core/llm/
  __init__.py          (1,074 B)
  adapter.py           (1,869 B)
  ensemble.py          (8,646 B)
  litellm_client.py    (1,532 B)  [D1-2]
  llamacpp_adapter.py  (6,033 B)  unused
  model_router.py      (9,589 B)
  ollama_adapter.py    (9,413 B)  unused
  structured_models.py (1,296 B)  [D1-3]
12. Smoke Test (run at session start)
Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"
.\\.venv\\Scripts\\Activate.ps1
python -c "import sys; print(sys.executable)"
git log --oneline -5
python -m jarvis_cli --help
python scripts\\test_d1_3_imports.py
python scripts\\test_d2_mcp.py
python -m jarvis_cli browse https://arxiv.org/abs/2005.12402
python -m jarvis_cli pipeline "autophagy" --max 3 --no-summary
13. Absolute Rules for Implementation
Never use python -c "..." for complex code. Always create .py files.
jarvis_cli/init.py: full overwrite only. No partial inserts.
Package install: python -m pip install only.
DO NOT import jarvis_core.agents.orchestrator.
Scrapling: no css_first(). Use css("sel")[0].
MCP JSON: use --params-file, not inline.
File creation: Notepad method (notepad path -> paste -> Ctrl+S -> close -> python path).
Avoid triple-quotes inside triple-quoted strings in write_*.py.
Gemini 15 RPM limit: add time.sleep(3) between API calls.
OpenAlexClient.search() uses per_page, not max_results.
14. Next Action: Resume from Day 3 (D3)
See JARVIS_EXPANSION_PLAN_v1.md for full task specs with code examples.

15. Available AI Tools
Tool	Plan	Model	Purpose
Gemini API	Google AI Pro (2TB Drive)	gemini-2.0-flash	Built-in LLM
Codex CLI	ChatGPT Plus ($20/mo)	GPT-5.3-Codex	Code automation
Copilot CLI	Education Pro (free)	Claude Sonnet 4.6 etc	Code gen/review
Claude (chat)	--	Claude Opus 4.6	Design/planning
16. Storage Layout
C: (460 GB / ~45 GB free)
  Users\\kaneko yu\\
    Documents\\jarvis-work\\jarvis-ml-pipeline\\  <- project
      .venv\\ (~1.5 GB)
      jarvis_cli\\
      jarvis_core\\
      config.yaml
      .env
      scripts\\  <- D1/D2 build/test scripts
    .cache\\huggingface\\ (0.48 GB)
    Zotero\\ (0.47 GB)

H: (Google Drive 2TB / 57 GB used)
  jarvis-data\\
    logs\\orchestrate\\
    logs\\pipeline\\
    pdf-archive\\
    exports\\json\\
    exports\\bibtex\\
    exports\\prisma\\
    backup\\
17. Related Repositories
Repository	Purpose	Status
https://github.com/kaneko-ai/jarvis-ml-pipeline	Main repo	D1/D2 done
https://github.com/kaneko-ai/zotero-doi-importer	Zotero DOI tool	A-6 done

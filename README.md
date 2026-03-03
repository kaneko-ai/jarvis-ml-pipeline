# JARVIS Research OS

[![CI](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/eval.yml/badge.svg)](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-Powered Research Operating System for Systematic Literature Reviews**

JARVIS Research OS is a local-first, AI-powered research assistant that automates systematic literature reviews with evidence grading, citation network analysis, and multi-agent orchestration.

## Release Status

- **Current version**: `v1.3.0` (2026-03-04)
- **Target version**: `v2.0.0`
- **CLI Commands**: 22

## Features

### Core Pipeline
- **Multi-Source Search**: PubMed, Semantic Scholar, OpenAlex, arXiv, Crossref
- **Evidence Grading**: CEBM evidence level classification (1a-5)
- **Paper Scoring**: Comprehensive quality scoring with multiple signals
- **LLM Japanese Summary**: Gemini-powered structured summaries
- **Deduplication**: DOI/title fuzzy matching with RapidFuzz

### Analysis & Discovery
- **Citation Network**: PageRank hub detection, Mermaid/GraphML visualization (D5)
- **Citation Stance**: Support/Contrast/Mention classification
- **Contradiction Detection**: Negation, antonym, and quantitative analysis
- **Semantic Search**: ChromaDB persistent vector search (D3)
- **Deep Research**: Autonomous multi-query research with Codex/Copilot/Gemini fallback (D4)
- **Active Learning**: Efficient screening with uncertainty sampling

### AI Infrastructure
- **LiteLLM**: Unified multi-provider LLM access (Gemini/OpenAI/DeepSeek) (D1)
- **LangGraph Orchestrator**: 6-agent pipeline with conditional retry loops (D4)
- **PydanticAI + Instructor**: Structured LLM output validation (D1)
- **LightRAG**: Graph-based RAG with entity/relation extraction (D3)
- **PDF-to-Markdown**: PyMuPDF4LLM full-text extraction (D3)

### Export & Integration
- **Obsidian Notes**: Auto-generated research notes in Obsidian Vault
- **Zotero Sync**: Reference management integration
- **PRISMA Diagrams**: PRISMA 2020 flow diagram generation (Mermaid)
- **BibTeX Export**: Standard bibliography format
- **Google Drive**: H: drive storage with local fallback (D5)

### Ecosystem
- **MCP Hub**: 5 servers, 15 tools for external API access
- **Skills System**: Task-specific workflows via `SKILL.md`
- **Streamlit Dashboard**: 5-page web UI (Overview/Search/Citation/ChromaDB/Storage) (D6)

## Quick Start

```bash
# Clone
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# Setup (Windows)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .

# Verify
python -m jarvis_cli --help
Copy
CLI Commands (22)
#	Command	Description
1	run	Run full pipeline with goal
2	search	Search papers across multiple sources
3	merge	Merge and deduplicate JSON results
4	note	Generate LLM research note
5	citation	Fetch citation counts
6	citation-stance	Classify citation relationships
7	prisma	Generate PRISMA 2020 flow diagram
8	evidence	Grade CEBM evidence level
9	score	Calculate paper quality scores
10	screen	Active learning paper screening
11	browse	Fetch URL and extract metadata
12	skills	Manage task-specific workflows
13	mcp	MCP Hub server/tool management
14	orchestrate	LangGraph multi-agent orchestrator
15	obsidian-export	Export papers to Obsidian Vault
16	semantic-search	ChromaDB persistent semantic search
17	contradict	Detect contradictions between papers
18	zotero-sync	Sync papers to Zotero library
19	pdf-extract	Convert PDF to Markdown
20	deep-research	Autonomous deep research mode
21	citation-graph	Build citation network visualization
22	pipeline	Run full pipeline with all options
Usage Examples
Copy# Search papers
jarvis search "PD-1 immunotherapy" --max 10 --sources pubmed,s2

# Full pipeline with Obsidian export
jarvis pipeline "spermidine autophagy aging" --max 20 --obsidian --zotero --prisma

# Multi-agent orchestration
jarvis orchestrate run --goal "immunosenescence mechanisms" --max 5

# Deep research
jarvis deep-research "PD-1 resistance mechanisms" --max-sources 20

# Citation network
jarvis citation-graph results.json --obsidian

# Semantic search (ChromaDB)
jarvis semantic-search "autophagy aging" --top 10

# Evidence grading
jarvis evidence papers.json --use-llm

# Streamlit Dashboard
streamlit run jarvis_web/streamlit_app.py
Architecture
jarvis-ml-pipeline/
├── jarvis_cli/          # 22 CLI command handlers
├── jarvis_core/
│   ├── embeddings/      # ChromaDB PaperStore, sentence-transformers
│   ├── evidence.py      # CEBM evidence grading
│   ├── llm/             # LiteLLM client, Pydantic models
│   ├── mcp/             # MCP Hub (5 servers, 15 tools)
│   ├── pdf/             # PDF-to-Markdown (PyMuPDF4LLM)
│   ├── rag/             # LightRAG, CitationGraph, citation enricher
│   ├── skills/          # Skills engine
│   ├── sources/         # Unified multi-source search
│   └── storage_utils.py # H: drive / local fallback paths
├── jarvis_web/          # Streamlit dashboard
├── tests/               # pytest suite (50+ D6 tests)
├── config.yaml          # Project configuration
└── .env                 # API keys (gitignored)
Requirements
Python 3.11+
Windows 11 (primary), Linux/macOS (untested)
Gemini API key (free tier: 15 RPM)
Optional: Codex CLI (ChatGPT Plus), Copilot CLI (Education Pro)
Development
Copy# Run tests
python -m pytest tests/ -v --timeout=30

# Run D6 tests only
python -m pytest tests/test_imports.py tests/test_citation_graph.py tests/test_storage_utils.py -v

# Check CLI
python -m jarvis_cli --help
Version History
Version	Date	Highlights
v1.3.0	2026-03-04	D5: Obsidian/storage H: migration, citation network, 22 CLI commands
v1.2.0	2026-03-03	D3: ChromaDB, LightRAG, PDF-to-Markdown
v1.1.0	2026-03-03	D2: Jina Reader, MCP handlers, browse enhancement
v1.0.0	2026-03-02	Initial release: 21 CLI commands, full SLR pipeline
License
MIT License - see LICENSE for details.

Handover
See HANDOVER_v8.md for complete development context and continuation instructions.
# JARVIS Research OS

[![CI](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/eval.yml/badge.svg)](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-Powered Research Operating System for Systematic Literature Reviews**

JARVIS Research OS is a local-first, AI-powered research assistant that helps researchers conduct systematic literature reviews with evidence grading, citation analysis, and contradiction detection.

## Release Status

- Current release target: `v1.0.0`

## 笨ｨ Features

### Phase 1: Local-First Foundation
- **Hybrid Search**: Sentence Transformers + BM25 with RRF fusion
- **Offline Mode**: Network detection and graceful degradation
- **Free APIs**: arXiv, Crossref, Unpaywall integration

### Phase 2: Differentiation Features
- **Evidence Grading**: CEBM evidence level classification (1a-5)
- **Citation Analysis**: Support/Contrast/Mention stance classification
- **Contradiction Detection**: Negation, antonym, and quantitative contradiction detection
- **PRISMA Diagrams**: PRISMA 2020 flow diagram generation (Mermaid/SVG)
- **Paper Scoring**: Comprehensive quality scoring with multiple signals
- **Active Learning**: Efficient screening with uncertainty sampling

### Phase 3: Ecosystem
- **MCP Hub**: External search servers (PubMed/Semantic Scholar/OpenAlex)
- **Browser Agent**: Safe browser automation with security policy
- **Skills System**: Task-specific workflows via `SKILL.md`
- **Multi-Agent Orchestrator**: Parallel agents + approval flow
- **Plugin System**: Extensible architecture
- **Zotero Integration**: Reference management
- **Export Formats**: RIS, BibTeX, Markdown

## 噫 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Basic Usage

```python
from jarvis_core.evidence import grade_evidence
from jarvis_core.citation import extract_citation_contexts, classify_citation_stance
from jarvis_core.contradiction import Claim, ContradictionDetector

# Grade evidence level
grade = grade_evidence(
    title="A randomized controlled trial...",
    abstract="Methods: We conducted a double-blind RCT..."
)
print(f"Evidence Level: {grade.level.value} ({grade.level.description})")

# Analyze citations
contexts = extract_citation_contexts(text, paper_id="paper_A")
for ctx in contexts:
    stance = classify_citation_stance(ctx.get_full_context())
    print(f"Citation to {ctx.cited_paper_id}: {stance.stance.value}")

# Detect contradictions
detector = ContradictionDetector()
claim_a = Claim(claim_id="1", text="Drug X increases survival", paper_id="A")
claim_b = Claim(claim_id="2", text="Drug X decreases survival", paper_id="B")
result = detector.detect(claim_a, claim_b)
print(f"Contradiction: {result.is_contradictory}")
```

### CLI Usage

```bash
# Search papers
jarvis search "machine learning cancer diagnosis"

# Run full pipeline
jarvis run --config pipeline.yaml

# Generate PRISMA diagram
jarvis prisma --output prisma_flow.svg
```

### MCP Hub Example

```bash
# Register MCP servers and list tools
jarvis mcp list --config configs/mcp_config.json

# Invoke MCP tool
jarvis mcp invoke search_pubmed --params '{"query": "cancer immunotherapy"}'
```

### Browser Agent Example

```python
from jarvis_core.browser.subagent import BrowserSubagent
from jarvis_core.browser.schema import SecurityPolicy

policy = SecurityPolicy(url_allow_list=["pubmed.ncbi.nlm.nih.gov"])
agent = BrowserSubagent(security_policy=policy, headless=True)
```

### Skills System Example

```bash
# List skills and show details
jarvis skills list
jarvis skills show MCP
```

## 逃 Core Modules

| Module | Description |
|--------|-------------|
| `embeddings/` | Sentence Transformers, BM25, Hybrid search |
| `network/` | Network detection, offline mode |
| `sources/` | arXiv, Crossref, Unpaywall clients |
| `evidence/` | CEBM evidence grading |
| `citation/` | Citation context and stance analysis |
| `contradiction/` | Claim normalization and contradiction detection |
| `prisma/` | PRISMA 2020 flow diagram generation |
| `paper_scoring/` | Paper quality scoring |
| `active_learning/` | Active learning for efficient screening |

## ｧｪ Testing

```bash
# Run all tests
uv run pytest

# Run specific module tests
uv run pytest tests/test_evidence_grading.py -v

# Run with coverage
uv run pytest --cov=jarvis_core

開発実行は `uv run ...` を標準とし、`python -m pytest` は再現差が出るため非推奨です。
```

## 当 Documentation

- [Docs Hub](docs/README.md)
- [API Reference](docs/API_REFERENCE.md)
- [Quickstart](docs/QUICKSTART.md)
- [Contributing](CONTRIBUTING.md)

## 肌 Configuration

Create `config.yaml`:

```yaml
search:
  default_sources:
    - pubmed
    - arxiv
  max_results: 100

embeddings:
  model: all-MiniLM-L6-v2
  device: auto

evidence:
  use_llm: false
  ensemble_strategy: weighted_average

offline:
  enabled: true
  sync_on_connect: true
```

## 塘 License

MIT License - see [LICENSE](LICENSE) for details.

## 剌 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [arXiv](https://arxiv.org/)
- [PRISMA Statement](http://www.prisma-statement.org/)

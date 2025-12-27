# 🔬 JARVIS Research OS

[![CI](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/core_tests.yml/badge.svg)](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions)
[![Spec Lint](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/spec-lint.yml/badge.svg)](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI-powered scientific research assistant with reproducible pipelines.**

---

## 🚀 Quickstart (CLI only)

```bash
# 1. Clone & Setup
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline
cd jarvis-ml-pipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install
pip install -r requirements.lock
pip install -e .

# 3. Configure
cp .env.example .env
# Edit .env with your API keys

# 4. Run (CLI is the ONLY entry point)
python jarvis_cli.py run --goal "CD73 immunotherapy survey"

# 5. View results
python jarvis_cli.py show-run --run-id <run_id>
```

> ⚠️ **Note**: `main.py` is for demo only. Use `jarvis_cli.py` for all operations.

---

## 📁 Project Structure

```
jarvis-ml-pipeline/
├── jarvis_cli.py          # 🔑 ONLY entry point
├── jarvis_core/           # Core modules
│   ├── pipelines/         # MVP pipelines
│   ├── api/               # PubMed/arXiv clients
│   ├── extraction/        # PDF/Semantic/Claim
│   ├── analysis/          # Contradiction/Graph/Review
│   └── knowledge/         # Claim/Evidence store
├── logs/runs/{run_id}/    # Run outputs (Bundle)
├── configs/pipelines/     # Pipeline definitions
├── docs/                  # Documentation (Spec Authority)
└── tests/                 # Test suite
```

---

## 📋 Run Bundle (Output Contract)

Every run produces these files in `logs/runs/{run_id}/`:

| File | Description |
|------|-------------|
| `input.json` | Execution config |
| `result.json` | Final answer + citations |
| `eval_summary.json` | Quality gate results |
| `papers.jsonl` | Paper metadata |
| `claims.jsonl` | Extracted claims |
| `evidence.jsonl` | Evidence with locators |
| `scores.json` | Ranking features |
| `report.md` | Human-readable report |
| `warnings.jsonl` | Warnings & issues |

See [docs/BUNDLE_CONTRACT.md](docs/BUNDLE_CONTRACT.md) for schema.

---

## 🛠 Commands

| Command | Description |
|---------|-------------|
| `python jarvis_cli.py run --goal "..."` | Execute research task |
| `python jarvis_cli.py show-run --run-id ID` | View run results |
| `python jarvis_cli.py build-index --path DIR` | Build document index |

---

## 📖 Documentation

| Document | Authority | Description |
|----------|-----------|-------------|
| [SPEC_AUTHORITY.md](docs/SPEC_AUTHORITY.md) | Level 0 | Specification hierarchy |
| [BUNDLE_CONTRACT.md](docs/BUNDLE_CONTRACT.md) | Level 3 | Output contract |
| [ROADMAP_100.md](docs/ROADMAP_100.md) | Level 5 | 100-step roadmap |
| [DoD.md](docs/DoD.md) | Level 3 | Definition of Done |
| [DECISIONS.md](docs/DECISIONS.md) | Level 5 | Decision log |

---

## 🔒 Quality Gates

- **Citation required**: No answer without evidence
- **Locator required**: Evidence must have source location
- **No assertions**: Uncertain claims go to warnings

---

## 🧪 Testing

```bash
# Core tests (blocking)
pytest -m core -v

# Spec lint (doc authority check)
python tools/spec_lint.py

# All tests
pytest -v
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure all tests pass
4. Submit a pull request

See [docs/DoD.md](docs/DoD.md) for merge requirements.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

# 🔬 JARVIS Research OS

[![CI](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/core_tests.yml/badge.svg)](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Features](https://img.shields.io/badge/Features-300+-green.svg)](docs/FEATURES_300.md)

**AI-powered scientific research assistant with 300+ features.**

🚀 [Live Dashboard](https://kaneko-ai.github.io/jarvis-ml-pipeline/) | 📖 [Docs](docs/) | 🧪 [Features Guide](docs/FEATURES_300.md)

---

## ✨ Features

### 🧬 AI Co-Scientist (20 features)
- Hypothesis generation & validation
- Literature gap analysis
- Experiment design

### 🔬 Protein AI (20 features)
- AlphaFold integration (FREE)
- Binding affinity prediction
- Sequence design

### 🤖 Self-Driving Lab (60 features)
- Equipment control
- Sample tracking
- Protocol automation

### 📊 Advanced Analytics (100 features)
- Meta-analysis
- Bayesian statistics
- Visualization

### 🔒 Security & Compliance
- HIPAA/GDPR compliance
- Audit trail
- Data anonymization

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline
cd jarvis-ml-pipeline

# Install
pip install -r requirements.lock

# Try it
python -c "
from jarvis_core.scientist import HypothesisGenerator
hg = HypothesisGenerator()
for h in hg.generate_hypotheses('cancer treatment', n=3):
    print(f'💡 {h[\"text\"]}')
"
```

---

## 📁 Project Structure

```
jarvis-ml-pipeline/
├── jarvis_core/           # Core modules
│   ├── scientist/         # AI Co-Scientist (101-120)
│   ├── protein/           # Protein AI (121-140)
│   ├── lab/               # Lab Automation (141-200)
│   └── advanced/          # Analytics & More (201-300)
├── docs/                  # Documentation & Dashboard
├── tests/                 # Test suite
└── .github/workflows/     # CI/CD pipelines
```

---

## 🔄 Pipelines

Run research pipelines via GitHub Actions:

```bash
gh workflow run research-pipelines.yml \
  -f pipeline=hypothesis \
  -f topic="cancer immunotherapy"
```

Available pipelines:
- `hypothesis` - Hypothesis generation & experiment design
- `protein` - Structure prediction & sequence design
- `meta-analysis` - Literature meta-analysis
- `grant` - Funding opportunity matching
- `lab-automation` - Lab protocol automation

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](docs/QUICKSTART.md) | 5-minute getting started |
| [FEATURES_300.md](docs/FEATURES_300.md) | All 300 features guide |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## 🆓 Free Resources

All features use FREE resources:

| Feature | Free Resource |
|---------|---------------|
| AlphaFold | EBI AlphaFold DB |
| Literature | PubMed API |
| Protein | UniProt |
| Pathways | KEGG/Reactome |
| Clinical Trials | ClinicalTrials.gov |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ by JARVIS Team

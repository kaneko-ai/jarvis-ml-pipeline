# JARVIS Research OS Roadmap

> Authority: REFERENCE (Level 2, Non-binding)

## Current Version: 5.3.0

---

## ✅ Phase 1: Foundation (Complete)

### CI/CD Infrastructure
- [x] GitHub Actions workflow
- [x] Linting (Ruff, Black, mypy)
- [x] Test matrix (Python 3.10, 3.11, 3.12)
- [x] Coverage collection
- [x] Security scanning (Bandit, pip-audit)
- [x] Build & package verification

### Core Modules
- [x] Evidence grading (`jarvis_core/evidence/`)
- [x] Citation analysis (`jarvis_core/citation/`)
- [x] Contradiction detection (`jarvis_core/contradiction/`)
- [x] PRISMA diagrams (`jarvis_core/prisma/`)
- [x] Active learning (`jarvis_core/active_learning/`)
- [x] Hybrid search (`jarvis_core/embeddings/`)

### Infrastructure
- [x] Single entry point (`jarvis_cli.py`)
- [x] Offline mode support
- [x] Free API integration (arXiv, Crossref, Unpaywall, PubMed)
- [x] Network detection
- [x] Cache system

---

## 🔄 Phase 2: Differentiation (In Progress)

### Quality Targets
| Module | Current | Target |
|--------|---------|--------|
| Evidence Grading | TBD | 85% |
| Citation Stance | TBD | 80% |
| Contradiction Detection | TBD | 75% |

### Test Quality
- [ ] Resolve 727 failing tests
- [ ] Achieve 70% coverage threshold
- [ ] Enable coverage gate as required job

### Integration Tests
- [ ] Stabilize contract_and_unit
- [ ] Stabilize api_smoke
- [ ] Stabilize dashboard_e2e

---

## ❌ Phase 3: Ecosystem (Planned)

### Distribution
- [ ] PyPI publication (`pip install jarvis-research`)
- [ ] Docker image optimization
- [ ] One-liner installation script

### Integrations
- [ ] Complete Zotero sync
- [ ] Plugin system finalization
- [ ] Export formats (RIS, BibTeX, Markdown)

### Documentation
- [ ] Full API reference
- [ ] User tutorials
- [ ] Video guides

---

## 📅 Milestones

| Milestone | Description | Status |
|-----------|-------------|--------|
| M1 | CI/CD Green | ✅ Done |
| M1.5 | Phase 1 Complete | ✅ Done |
| M2 | Differentiation MVP | 🔄 In Progress |
| M2.5 | Phase 2 Complete | ❌ Planned |
| M3 | v1.0 Release | ❌ Planned |

---

## 📁 Historical Documents

Previous planning documents are archived in [archive/](archive/):
- JARVIS_COMPLETION_PLAN_v3.md
- JARVIS_INFRA_ROADMAP.md
- JARVIS_LOCALFIRST_ROADMAP.md

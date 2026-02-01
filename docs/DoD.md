# Definition of Done (DoD)

> Authority: GATE (Level 3, Binding)

## 🎯 Feature Completion Criteria

All new features MUST satisfy:

1. **Tests exist** - `tests/test_*.py` with meaningful coverage
2. **Documentation exists** - docstrings or docs/*.md
3. **Lint passes** - `uv run ruff check` returns 0
4. **Format passes** - `uv run black --check` returns 0
5. **CI passes** - GitHub Actions shows green

---

## ✅ Phase 1: Foundation (Complete)

### Infrastructure
- [x] Single entry point (`jarvis_cli.py`)
- [x] Unified contract (10-file bundle)
- [x] CI/CD pipeline (GitHub Actions)
- [x] Quality gates (spec_lint.py)

### Core Implementation
- [x] Evidence grading module
- [x] Citation analysis module
- [x] Contradiction detection module
- [x] PRISMA diagram generation
- [x] Active learning engine
- [x] Hybrid search (Sentence Transformers + BM25)

### APIs & Integration
- [x] Free API clients (arXiv, Crossref, Unpaywall, PubMed)
- [x] Offline mode support
- [x] Network detection

---

## 🔄 Phase 2: Differentiation (In Progress)

### Accuracy Targets
| Module | Target | Status |
|--------|--------|--------|
| Evidence Grading | 85% | 🔄 |
| Citation Stance | 80% | 🔄 |
| Contradiction | 75% | 🔄 |

### Test Quality
- [ ] Resolve failing tests (727 → 0)
- [ ] Coverage ≥ 70%
- [ ] Enable coverage_gate as required

### Integration Stability
- [ ] contract_and_unit stable
- [ ] api_smoke stable
- [ ] E2E tests stable

---

## ❌ Phase 3: Ecosystem (Planned)

- [ ] PyPI publication
- [ ] Docker optimization
- [ ] Plugin system completion
- [ ] Full Zotero integration
- [ ] Complete documentation

---

## 🔒 CI Requirements

| Check | Requirement | Status |
|-------|-------------|--------|
| lint | Must pass | ✅ Enforced |
| test | Must pass | ✅ Enforced |
| build | Must pass | ✅ Enforced |
| coverage_gate | Should pass | ⚠️ Optional |

---

## 📝 Merge Checklist

Before merging any PR:

- [ ] All required CI jobs pass
- [ ] No new warnings introduced
- [ ] Tests added for new code
- [ ] Documentation updated if needed
- [ ] Bundle contract compatible

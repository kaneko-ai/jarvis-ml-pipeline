# Quality Bar (Exit Criteria)

> Authority: SPECIFICATION (Level 2, Binding)


Per RP-182, this defines the exit criteria for v4.3 development.

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Core Test Pass Rate | 100% | ✅ |
| Success Rate | ≥ 80% | 🟡 Pending eval |
| Claim Precision | ≥ 70% | 🟡 Pending eval |
| Citation Precision | ≥ 60% | 🟡 Pending eval |
| Entity Hit Rate | ≥ 60% | 🟡 Pending eval |
| Avg Latency | < 120s | 🟡 Pending eval |

---

## Feature Completeness

### Must Have (P0) ✅
- [x] Core/Legacy test separation
- [x] Network isolation for tests
- [x] Deterministic time/seed
- [x] Telemetry redaction
- [x] Storage retention policy
- [x] Result type unification
- [x] Safe paths

### Should Have (P1) ✅
- [x] PDF extraction chain
- [x] Sectionizer/Sentence splitter
- [x] Hybrid retrieval
- [x] Claim classifier
- [x] Entity normalizer
- [x] Budget enforcement

### Nice to Have (P2) ✅
- [x] TraceContext
- [x] Run summarizer
- [x] Durable checkpoints
- [x] KPI reporter
- [x] Jarvis doctor

### Optional (P3) ✅
- [x] FastAPI web layer
- [x] Model router
- [x] NotebookLM exporter
- [x] Project contract check

---

## Exit Criteria Checklist

- [x] All core tests pass
- [x] No Hard Gate regressions
- [x] requirements.lock updated
- [x] STATE_BASELINE.md current
- [x] RELEASE_NOTES written
- [ ] Success rate measured
- [ ] Citation precision measured

---

## When to Stop

Development can transition to maintenance when:

1. **Core Tests**: 100% pass rate maintained for 1 week
2. **Success Rate**: ≥ 80% on frozen eval set
3. **No P0 Regressions**: All hard gates passing
4. **Documentation Complete**: All docs up to date

After criteria met:
- Focus shifts to research use cases
- PRs limited to bug fixes and P2+ improvements
- No new features until next version cycle

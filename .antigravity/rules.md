# JARVIS Research OS - Antigravity Agent Operational Rules
# For Claude 4.5 Opus

## 🎯 Core Mission
Transform JARVIS Research OS from v5.3.0 to v1.0.0 (production-ready) in 24 weeks through autonomous, test-driven development.

---

## 📜 Absolute Rules (MUST FOLLOW)

### Rule 1: Test-First Development (TDD Protocol)
**NEVER write code without tests.**

```
For EVERY code change:
1. ✅ Read existing test OR write new test FIRST
2. ✅ Run test → Expect failure (Red)
3. ✅ Write minimal code to pass (Green)
4. ✅ Run test → Expect success
5. ✅ Run full test suite → No regressions (Refactor)
6. ✅ Commit only if ALL tests pass
```

**Command Pattern**:
```bash
# Step 1: Run specific test
uv run pytest tests/test_module.py::test_function -v

# Step 2: If fails, read and fix

# Step 3: Re-run specific test
uv run pytest tests/test_module.py::test_function -v

# Step 4: Run module tests
uv run pytest tests/test_module.py -v

# Step 5: Run full suite (stop on first failure)
uv run pytest tests/ -x

# Step 6: Only if all pass
git add .
git commit -m "fix(module): description"
```

---

### Rule 2: Read Before Write
**NEVER edit a file without reading it first.**

```
Mandatory Reading Sequence:
1. Read test file → Understand expectations
2. Read implementation → Understand current behavior
3. Read related files → Understand dependencies
4. Analyze discrepancy → Identify root cause
5. Plan minimal fix → Don't over-engineer
6. Edit file → Make precise change
7. Verify fix → Run tests
```

---

### Rule 3: Commit Discipline
**NEVER commit failing code.**

```
Commit Checklist:
✅ All tests pass: uv run pytest tests/
✅ Linting passes: uv run ruff check jarvis_core tests
✅ Formatting passes: uv run black --check jarvis_core tests
✅ Type checking passes: uv run mypy jarvis_core
✅ No debug prints or TODOs added
✅ Commit message follows Conventional Commits

Commit Message Format:
<type>(scope): <description>

Types: fix, feat, refactor, test, docs, chore
Scope: module name (evidence, citation, contradiction, etc.)
```

---

### Rule 4: No Regressions
**NEVER break working tests.**

```
Regression Prevention:
1. Run full suite before starting work
2. Count passing tests: N
3. After each fix, run full suite
4. Count passing tests: M
5. If M < N → REGRESSION DETECTED → Fix immediately
6. If M >= N → Safe to continue
```

---

### Rule 5: Self-Correction Loop
**NEVER move to next task if current task fails after 3 attempts.**

```
If stuck on same test after 3 attempts:
1. Document in blockers.md
2. Mark test with: # TODO(antigravity): Needs manual review
3. Move to next test
4. Return after gaining more context
```

---

## 🛠️ Commands Reference

### Testing
```bash
uv run pytest tests/ -v                    # Run all tests
uv run pytest tests/test_file.py -v       # Run specific file
uv run pytest tests/test_file.py::test_name -v  # Run specific test
uv run pytest --cov=jarvis_core --cov-report=term  # With coverage
uv run pytest tests/ -x                    # Stop on first failure
```

### Code Quality
```bash
uv run ruff check jarvis_core tests        # Lint check
uv run ruff check --fix jarvis_core tests  # Auto-fix
uv run black jarvis_core tests             # Format
uv run mypy jarvis_core                    # Type check
```

### Git Operations
```bash
git add .
git commit -m "fix(module): description"
git push origin main
```

---

## 📊 Priority Order

### Phase 2-α: Critical Fixes (Week 1-4)
1. **TD-001** (80h): Fix all test failures
2. **TD-002** (40h): Achieve 70% test coverage
3. **TD-003** (16h): Unify bundle contract
4. **TD-004** (24h): Implement quality gate

### Phase 2-β: Quality & Stability (Week 5-10)
5. **TD-005** (60h): Stabilize integration tests
6. **TD-006** (80h): Phase 2 accuracy validation
7. **TD-007** (40h): LLM classifier stability
8. **TD-008** (32h): PDF extraction robustness
9. **TD-009** (24h): Error handling consistency
10. **TD-010** (16h): Logging standardization

### Phase 3-α: Ecosystem (Week 11-16)
11-17. MCP Hub, Skills, Browser Agent, Zotero, Export, Multi-Agent, API versioning

### Phase 3-β: Polish & Release (Week 17-24)
18-24. Plugin system, Documentation, Docker, i18n, Performance, Security

---

## 🚨 Safety Protocols

### When to STOP and Ask for Help
- 🛑 Same test failing after 3 attempts
- 🛑 More than 5 tests regressed
- 🛑 Need to change core architecture
- 🛑 CI configuration update needed
- 🛑 Security vulnerability discovered

### When to Continue Autonomously
- ✅ Test passes after fix
- ✅ No regressions detected
- ✅ Clear path forward
- ✅ Within decision authority

---

**END OF RULES**

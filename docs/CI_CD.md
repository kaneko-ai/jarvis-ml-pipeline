# CI/CD Guide

> Authority: REFERENCE (Level 2, Non-binding)

## Overview

All CI jobs are defined in `.github/workflows/ci.yml`.

---

## 🟢 Required Jobs (Must Pass)

| Job | Description | Tools |
|-----|-------------|-------|
| `lint` | Code quality | Ruff, Black, mypy |
| `garbage_check` | Dead code detection | detect_garbage_code.py |
| `test` | Unit tests (3.10, 3.11, 3.12) | pytest, coverage |
| `security` | Security scanning | Bandit, pip-audit |
| `build` | Package build | setuptools, twine |

---

## 🟡 Optional Jobs (Can Fail)

These jobs use `continue-on-error: true`:

| Job | Description | Why Optional |
|-----|-------------|--------------|
| `coverage_gate` | Coverage threshold check | Threshold not yet met |
| `contract_and_unit` | API contract tests | Dependencies unstable |
| `api_smoke` | API smoke tests | Server startup issues |
| `dashboard_e2e_mock` | E2E with mock server | Playwright flaky |
| `dashboard_e2e_real` | E2E with real API | Environment dependent |

---

## 🔧 Key Configuration

### Test Matrix
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
  fail-fast: false
```

### Coverage Collection
```yaml
# Using coverage run instead of pytest-cov
# Reason: Avoid SQLite lock issues
- run: |
    uv run coverage run --source=jarvis_core -m pytest tests/
    uv run coverage xml -o coverage.xml
```

### Codecov Integration
```yaml
- uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    fail_ci_if_error: false  # Don't fail CI on upload issues
```

---

## 💻 Local Development

### Run All Checks
```bash
# Lint
uv run ruff check jarvis_core tests
uv run black --check jarvis_core tests
uv run mypy jarvis_core

# Test
uv run pytest tests/ -q

# Coverage
uv run coverage run --source=jarvis_core -m pytest tests/
uv run coverage report
```

### Quick Test
```bash
# Run specific test file
uv run pytest tests/test_evidence_grading.py -v

# Run with markers
uv run pytest -m "not slow" tests/
```

---

## 🚨 Troubleshooting

### SQLite Lock Error
```
coverage.exceptions.DataError: Couldn't use data file
```
**Solution**: Use `coverage run` instead of `pytest --cov`. Ensure `-p no:cov` is passed to pytest.

### Codecov Upload Failure
```
Failed to properly upload report
```
**Solution**: This is a warning only. Check `CODECOV_TOKEN` secret exists.

### Test Timeout
**Solution**: Add `--timeout=300` to pytest command or mark slow tests with `@pytest.mark.slow`.

---

## 📊 Current Status

- **Required Jobs**: ✅ All passing
- **Optional Jobs**: ⚠️ May fail (acceptable)
- **Coverage**: Collected but threshold not enforced

#!/usr/bin/env bash
set -euo pipefail

echo "=== JARVIS Coverage Gate ==="

rm -f .coverage .coverage.* coverage.xml
rm -rf htmlcov/ .pytest_cache/

python -m pytest tests/ \
  --cov=jarvis_core \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --cov-report=term-missing \
  --cov-fail-under=70 \
  -q \
  --ignore=tests/e2e \
  --ignore=tests/integration \
  -p no:randomly \
  2>&1 || {
    EXIT_CODE=$?
    echo "Tests completed with exit code: $EXIT_CODE"
    if [[ -f coverage.xml ]]; then
      echo "coverage.xml generated"
    fi
    exit $EXIT_CODE
  }

echo "=== Coverage Gate PASSED ==="

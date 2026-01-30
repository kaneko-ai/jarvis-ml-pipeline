#!/usr/bin/env bash
# JARVIS Coverage Gate Script (Unified Phase Check)
set -euo pipefail

echo "=== JARVIS Coverage Gate ==="

# Clean up existing coverage files
rm -f .coverage .coverage.* coverage.xml

# Run pytest with coverage (Branch mode enabled for Phase 2)
# We run with branch coverage enabled so we can check both.
python -m pytest tests/ \
  --cov=jarvis_core \
  --cov-branch \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --cov-report=term-missing \
  -q \
  --ignore=tests/e2e \
  --ignore=tests/integration

echo "----------------------------------------"
echo "Checking Phase 1: Statement Coverage (Goal: 85%)"
python -m coverage report --rcfile=.coveragerc.phase1 --fail-under=85

echo "----------------------------------------"
echo "Checking Phase 2: Branch Coverage (Goal: 95%)"
# We need to ensure .coveragerc.phase2 has branch=True
python -m coverage report --rcfile=.coveragerc.phase2 --fail-under=95

echo "----------------------------------------"
echo "=== Coverage Gate PASSED ==="

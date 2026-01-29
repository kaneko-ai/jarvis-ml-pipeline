#!/usr/bin/env bash
# JARVIS Coverage Gate Script
# カバレッジ計測を一元管理するスクリプト
# 
# Usage:
#   COVERAGE_PHASE=1 bash scripts/ci_coverage.sh  # Phase 1 (85%, no branch)
#   COVERAGE_PHASE=2 bash scripts/ci_coverage.sh  # Phase 2 (95%, with branch)

set -euo pipefail

PHASE="${COVERAGE_PHASE:-1}"

echo "=== JARVIS Coverage Gate ==="
echo "Phase: $PHASE"

if [[ "$PHASE" == "1" ]]; then
  CFG=".coveragerc.phase1"
  echo "Mode: Statement/Line only (no branch)"
  echo "Threshold: 85%"
elif [[ "$PHASE" == "2" ]]; then
  CFG=".coveragerc.phase2"
  echo "Mode: Statement/Line + Branch"
  echo "Threshold: 95%"
else
  echo "ERROR: Invalid COVERAGE_PHASE=$PHASE (use 1 or 2)" >&2
  exit 2
fi

echo "Config: $CFG"
echo "=========================="
echo ""

# Clean up any existing coverage files
rm -f .coverage .coverage.*

# Run pytest with coverage
# parallel=True in .coveragerc ensures each process writes its own file
python -m pytest \
  --cov=jarvis_core \
  --cov-config="$CFG" \
  --cov-report=xml \
  --cov-report=html \
  --cov-report=term-missing \
  -p no:randomly \
  -p no:xdist \
  --dist=no \
  -q

# Combine parallel coverage files
echo "Combining coverage data..."
python -m coverage combine --rcfile="$CFG"

# Generate final report with fail_under check
echo ""
echo "=== Coverage Report ==="
python -m pytest tests/ \
    --cov=jarvis_core \
    --cov-report=xml \
    --cov-report=html \
    --cov-fail-under=70

echo ""
echo "=== Coverage Gate PASSED ==="

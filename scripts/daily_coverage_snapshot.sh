#!/usr/bin/env bash
# Daily Coverage Snapshot (non-gating)
# Purpose: 測定のみ行い、fail_underでブロックしない
# Usage: COVERAGE_PHASE=1 bash scripts/daily_coverage_snapshot.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PHASE="${COVERAGE_PHASE:-1}"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-artifacts}"

# Phase validation
if [[ "$PHASE" != "1" && "$PHASE" != "2" ]]; then
    echo "ERROR: Invalid COVERAGE_PHASE=$PHASE (use 1 or 2)" >&2
    exit 2
fi

# Config selection
if [[ "$PHASE" == "1" ]]; then
    CFG=".coveragerc.phase1"
else
    CFG=".coveragerc.phase2"
fi

# Config existence check
if [[ ! -f "$CFG" ]]; then
    echo "ERROR: Config file not found: $CFG" >&2
    exit 1
fi

echo "=== Daily Coverage Snapshot ==="
echo "Date: $(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S JST')"
echo "Phase: $PHASE"
echo "Config: $CFG"
echo "==============================="

# Prepare artifacts directory
mkdir -p "$ARTIFACTS_DIR"

# Clean up existing coverage files
rm -f .coverage .coverage.* 2>/dev/null || true

# Run pytest with coverage (ignore test failures for snapshot)
echo ""
echo "Running tests with coverage..."
set +e
python -m pytest \
    --cov=jarvis_core \
    --cov-config="$CFG" \
    --cov-report=xml \
    --cov-report=html \
    --cov-report=term-missing \
    -q \
    2>&1 | tee "$ARTIFACTS_DIR/pytest_output.txt"
PYTEST_EXIT=$?
set -e

echo ""
echo "Pytest exit code: $PYTEST_EXIT (ignored for snapshot)"

# Combine parallel coverage files if any
if ls .coverage.* 1>/dev/null 2>&1; then
    echo "Combining coverage data..."
    python -m coverage combine --rcfile="$CFG" 2>/dev/null || true
fi

echo ""
echo "=== Coverage Report (non-gating) ==="

# Create temporary config without fail_under
TEMP_CFG=$(mktemp)
grep -v "^fail_under" "$CFG" > "$TEMP_CFG" || cp "$CFG" "$TEMP_CFG"

# Generate report
python -m coverage report --rcfile="$TEMP_CFG" 2>&1 | tee "$ARTIFACTS_DIR/coverage_daily_term.txt"

# Cleanup temp config
rm -f "$TEMP_CFG"

# Move artifacts
mv coverage.xml "$ARTIFACTS_DIR/" 2>/dev/null || true
mv htmlcov "$ARTIFACTS_DIR/" 2>/dev/null || true

echo ""
echo "=== Snapshot Complete ==="
echo "Artifacts saved to: $ARTIFACTS_DIR/"

# Always exit 0 (this is snapshot, not gate)
exit 0

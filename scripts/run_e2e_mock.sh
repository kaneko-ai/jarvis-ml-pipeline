#!/usr/bin/env bash
set -euo pipefail

MOCK_PORT="${MOCK_PORT:-4010}"
DASHBOARD_PORT="${DASHBOARD_PORT:-4173}"

python -m uvicorn tests.mock_server.app:app --port "$MOCK_PORT" --log-level warning &
MOCK_PID=$!
python -m http.server "$DASHBOARD_PORT" -d dashboard &
DASHBOARD_PID=$!

cleanup() {
  kill "$MOCK_PID" "$DASHBOARD_PID" 2>/dev/null || true
}
trap cleanup EXIT

export MOCK_API_BASE="http://localhost:${MOCK_PORT}"
export DASHBOARD_BASE_URL="http://localhost:${DASHBOARD_PORT}"

npx playwright test -c tests/e2e/playwright.config.ts

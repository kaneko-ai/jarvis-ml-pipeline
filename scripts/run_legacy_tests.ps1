# Legacy Tests Runner (Windows)
# Per PR-59: Non-blocking legacy tests

Write-Host "=== JARVIS Legacy Tests (Non-blocking) ===" -ForegroundColor Yellow
Write-Host "Running: pytest -m legacy" -ForegroundColor Gray

if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
}

# Run legacy tests (failures expected, tracked in TECH_DEBT.md)
python -m pytest -m legacy -v --tb=short

Write-Host "`nNote: Legacy test failures are tracked in docs/TECH_DEBT.md" -ForegroundColor Yellow

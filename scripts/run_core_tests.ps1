# Core Tests Runner (Windows)
# Per PR-59/PR-61: Unified command for local and CI

Write-Host "=== JARVIS Core Tests ===" -ForegroundColor Cyan
Write-Host "Running: pytest -m core" -ForegroundColor Gray

# Activate venv if exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
}

# Run core tests only
python -m pytest -m core -v --tb=short

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n✓ Core tests passed" -ForegroundColor Green
} else {
    Write-Host "`n✗ Core tests failed" -ForegroundColor Red
}

exit $exitCode

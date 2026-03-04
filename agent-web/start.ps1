# JARVIS Agent Web - Start Script
# Starts copilot-api proxy (port 4141) and Express server (port 3000)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  JARVIS Agent Web - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$agentWebDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start copilot-api in background
Write-Host "[1/2] Starting copilot-api proxy on port 4141..." -ForegroundColor Yellow
$copilotJob = Start-Process -FilePath "npx" -ArgumentList "copilot-api@latest", "start", "--port", "4141" -WorkingDirectory $agentWebDir -PassThru -WindowStyle Normal
Write-Host "  copilot-api PID: $($copilotJob.Id)" -ForegroundColor Gray

# Wait for copilot-api to start
Write-Host "  Waiting 5 seconds for copilot-api to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Start Express server
Write-Host "[2/2] Starting Express server on port 3000..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  JARVIS Agent Web Ready!" -ForegroundColor Green
Write-Host "  UI:         http://localhost:3000" -ForegroundColor Green
Write-Host "  Copilot API: http://localhost:4141" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Set-Location $agentWebDir
npm run dev

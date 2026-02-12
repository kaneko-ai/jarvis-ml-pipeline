param(
    [string]$Workflow = "CI",
    [string]$Branch = "main",
    [int]$Target = 10,
    [int]$Limit = 50,
    [switch]$ShowRuns,
    [switch]$ShowFailedJobs,
    [switch]$ShowFailureSummary,
    [switch]$WaitLatest,
    [int]$PollSeconds = 30,
    [int]$TimeoutMinutes = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-CompletedRuns {
    param(
        [string]$WorkflowName,
        [string]$BranchName,
        [int]$MaxRuns
    )

    $runs = gh run list `
        --workflow $WorkflowName `
        --branch $BranchName `
        --limit $MaxRuns `
        --json databaseId,status,conclusion,createdAt,displayTitle | ConvertFrom-Json

    if (-not $runs) {
        return @()
    }

    return @($runs | Where-Object { $_.status -eq "completed" })
}

function Get-LatestRun {
    param(
        [string]$WorkflowName,
        [string]$BranchName
    )

    $runs = gh run list `
        --workflow $WorkflowName `
        --branch $BranchName `
        --limit 1 `
        --json databaseId,status,conclusion,createdAt,displayTitle | ConvertFrom-Json

    if (-not $runs) {
        return $null
    }
    return $runs[0]
}

function Wait-ForLatestRun {
    param(
        [string]$WorkflowName,
        [string]$BranchName,
        [int]$IntervalSeconds,
        [int]$MaxMinutes
    )

    $start = Get-Date
    while ($true) {
        $latest = Get-LatestRun -WorkflowName $WorkflowName -BranchName $BranchName
        if (-not $latest) {
            throw "No runs found while waiting for latest run."
        }

        if ($latest.status -eq "completed") {
            return $latest
        }

        $elapsed = (Get-Date) - $start
        if ($elapsed.TotalMinutes -ge $MaxMinutes) {
            throw "Timeout waiting for latest run completion (latest id: $($latest.databaseId), status: $($latest.status))."
        }

        Write-Host "Waiting latest run: id=$($latest.databaseId) status=$($latest.status) elapsed=$([int]$elapsed.TotalMinutes)m"
        Start-Sleep -Seconds $IntervalSeconds
    }
}

function Get-SuccessStreak {
    param([object[]]$Runs)

    $count = 0
    foreach ($run in $Runs) {
        if ($run.conclusion -eq "success") {
            $count++
            continue
        }
        break
    }
    return $count
}

function Get-BreakerRun {
    param(
        [object[]]$Runs,
        [int]$Streak
    )

    if ($Runs.Count -le $Streak) {
        return $null
    }
    return $Runs[$Streak]
}

function Show-FailedJobs {
    param([long]$RunId)

    $run = gh run view $RunId --json jobs | ConvertFrom-Json
    if (-not $run.jobs) {
        Write-Host "No jobs found for run $RunId"
        return
    }

    $failed = @($run.jobs | Where-Object { $_.conclusion -eq "failure" })
    if ($failed.Count -eq 0) {
        Write-Host "No failed jobs in run $RunId"
        return
    }

    Write-Host ""
    Write-Host "Failed jobs:"
    $failed | Select-Object databaseId, name, conclusion | Format-Table -AutoSize
    Write-Host ""
    Write-Host "Inspect logs:"
    foreach ($job in $failed) {
        Write-Host "  gh run view --job $($job.databaseId) --log"
    }
}

function Show-FailureSummary {
    param([long]$RunId)

    $logText = gh run view $RunId --log-failed 2>$null
    if (-not $logText) {
        Write-Host ""
        Write-Host "No failed log lines found for run $RunId."
        return
    }

    $lines = $logText -split "`r?`n"
    $failedTests = @($lines | Where-Object {
            $_ -match "FAILED\s+tests/.+::" -or
            $_ -match "ERROR\s+tests/.+::" -or
            $_ -match "AssertionError" -or
            $_ -match "Traceback \(most recent call last\)"
        } | Select-Object -First 20)

    Write-Host ""
    Write-Host "Failure summary:"
    if ($failedTests.Count -gt 0) {
        $failedTests | ForEach-Object { Write-Host "  $_" }
        return
    }

    $tail = $lines | Select-Object -Last 30
    $tail | ForEach-Object { Write-Host "  $_" }
}

if ($WaitLatest) {
    $null = Wait-ForLatestRun `
        -WorkflowName $Workflow `
        -BranchName $Branch `
        -IntervalSeconds $PollSeconds `
        -MaxMinutes $TimeoutMinutes
}

$completedRuns = Get-CompletedRuns -WorkflowName $Workflow -BranchName $Branch -MaxRuns $Limit
if ($completedRuns.Count -eq 0) {
    Write-Host "No completed runs found for workflow '$Workflow' on branch '$Branch'."
    exit 1
}

$streak = Get-SuccessStreak -Runs $completedRuns
$remaining = [Math]::Max(0, $Target - $streak)
$latest = $completedRuns[0]
$breaker = Get-BreakerRun -Runs $completedRuns -Streak $streak

Write-Host "Workflow : $Workflow"
Write-Host "Branch   : $Branch"
Write-Host "Target   : $Target"
Write-Host "Current  : $streak consecutive success(es)"
Write-Host "Remain   : $remaining"
Write-Host ""
Write-Host "Latest run:"
Write-Host "  id         : $($latest.databaseId)"
Write-Host "  conclusion : $($latest.conclusion)"
Write-Host "  createdAt  : $($latest.createdAt)"
Write-Host "  title      : $($latest.displayTitle)"

if ($breaker -and $breaker.conclusion -ne "success") {
    Write-Host ""
    Write-Host "Streak breaker:"
    Write-Host "  id         : $($breaker.databaseId)"
    Write-Host "  conclusion : $($breaker.conclusion)"
    Write-Host "  createdAt  : $($breaker.createdAt)"
    Write-Host "  title      : $($breaker.displayTitle)"
    Write-Host "  inspect    : gh run view $($breaker.databaseId) --log-failed"
}

if ($ShowRuns) {
    Write-Host ""
    Write-Host "Recent completed runs:"
    $completedRuns |
        Select-Object -First ([Math]::Min($Limit, 20)) databaseId, conclusion, createdAt, displayTitle |
        Format-Table -AutoSize
}

if ($ShowFailedJobs -and $breaker -and $breaker.conclusion -eq "failure") {
    Show-FailedJobs -RunId $breaker.databaseId
}

if ($ShowFailureSummary -and $breaker -and $breaker.conclusion -eq "failure") {
    Show-FailureSummary -RunId $breaker.databaseId
}

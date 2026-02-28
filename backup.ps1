# backup.ps1 - JARVIS データバックアップスクリプト
#
# 使い方:
#   PowerShell で以下を実行（プロジェクトルートで）:
#     .\backup.ps1
#
# 何をするか:
#   1. logs/ フォルダを日付付き ZIP に圧縮して D:\Backup\jarvis に保存
#   2. .env ファイルも一緒にバックアップ（API キーを失わないため）
#   3. 30日以上前の古いバックアップを自動削除
#
# 推奨頻度: 週に1回、または大きな検索・分析を行った後

# --- 設定 ---
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$logsDir = Join-Path $projectRoot "logs"
$envFile = Join-Path $projectRoot ".env"

# バックアップ先（別ドライブが望ましいが、なければ同じドライブでも可）
# ★ 自分の環境に合わせて変更してください
$backupRoot = "D:\Backup\jarvis"

# 古いバックアップを何日間保持するか
$retentionDays = 30

# --- バックアップ先フォルダの作成 ---
if (-not (Test-Path $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Write-Host "[INFO] Created backup directory: $backupRoot"
}

# --- バックアップ対象の確認 ---
if (-not (Test-Path $logsDir)) {
    Write-Host "[WARN] logs/ directory not found: $logsDir"
    Write-Host "[WARN] Nothing to backup. Run some searches first."
    exit 0
}

# --- バックアップ対象をリストアップ ---
$itemsToBackup = @()

# logs/ フォルダ（論文データ、ノート、被引用数データ等）
$itemsToBackup += $logsDir

# .env ファイル（API キー）
if (Test-Path $envFile) {
    $itemsToBackup += $envFile
}

# --- ZIP 圧縮 ---
$zipFileName = "jarvis_backup_$timestamp.zip"
$zipPath = Join-Path $backupRoot $zipFileName

Write-Host ""
Write-Host "=========================================="
Write-Host "  JARVIS Backup"
Write-Host "=========================================="
Write-Host "  Date     : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "  Source   : $logsDir"
Write-Host "  Dest     : $zipPath"
Write-Host ""

try {
    Compress-Archive -Path $itemsToBackup -DestinationPath $zipPath -Force
    $zipSize = (Get-Item $zipPath).Length
    $zipSizeMB = [math]::Round($zipSize / 1MB, 2)
    Write-Host "[OK] Backup created: $zipPath ($zipSizeMB MB)"
}
catch {
    Write-Host "[ERROR] Backup failed: $_" -ForegroundColor Red
    exit 1
}

# --- 古いバックアップの削除 ---
$cutoffDate = (Get-Date).AddDays(-$retentionDays)
$oldBackups = Get-ChildItem $backupRoot -Filter "jarvis_backup_*.zip" |
    Where-Object { $_.LastWriteTime -lt $cutoffDate }

if ($oldBackups.Count -gt 0) {
    Write-Host ""
    Write-Host "[INFO] Removing $($oldBackups.Count) old backup(s) (older than $retentionDays days):"
    foreach ($old in $oldBackups) {
        Write-Host "  - $($old.Name)"
        Remove-Item $old.FullName -Force
    }
}

# --- 完了レポート ---
$allBackups = Get-ChildItem $backupRoot -Filter "jarvis_backup_*.zip"
$totalSizeMB = [math]::Round(($allBackups | Measure-Object -Property Length -Sum).Sum / 1MB, 2)

Write-Host ""
Write-Host "=========================================="
Write-Host "  Backup Complete"
Write-Host "  Total backups : $($allBackups.Count)"
Write-Host "  Total size    : $totalSizeMB MB"
Write-Host "=========================================="
Write-Host ""

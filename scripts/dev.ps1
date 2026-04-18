$workspaceRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
$managePath = Join-Path $workspaceRoot "manage.py"

if (-not (Test-Path $pythonPath)) {
    Write-Error "Python environment not found at $pythonPath"
    exit 1
}

if (-not (Test-Path $managePath)) {
    Write-Error "Django manage.py not found at $managePath"
    exit 1
}

Set-Location $workspaceRoot
Write-Host "Cleaning up legacy quiz attempts..." -ForegroundColor Cyan
& $pythonPath $managePath cleanup_zero_scores

$backendCommand = "Set-Location '$workspaceRoot'; & '$pythonPath' '$managePath' runserver"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null

Set-Location $workspaceRoot
npm --prefix frontend run dev
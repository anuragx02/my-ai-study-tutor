$workspaceRoot = Split-Path -Parent $PSScriptRoot
$pythonCommand = "python"
$managePath = Join-Path $workspaceRoot "manage.py"

if (-not (Get-Command $pythonCommand -ErrorAction SilentlyContinue)) {
    Write-Error "Python was not found on PATH"
    exit 1
}

if (-not (Test-Path $managePath)) {
    Write-Error "Django manage.py not found at $managePath"
    exit 1
}

Set-Location $workspaceRoot
Write-Host "Cleaning up legacy quiz attempts..." -ForegroundColor Cyan
& $pythonCommand $managePath cleanup_zero_scores

$backendCommand = "Set-Location '$workspaceRoot'; & $pythonCommand '$managePath' runserver"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null

Set-Location $workspaceRoot
npm.cmd --prefix frontend run dev

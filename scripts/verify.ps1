param(
    [switch]$E2E,
    [switch]$QueryPlans
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot 'backend/.venv/Scripts/python.exe'
$npmExe = (Get-Command npm.cmd -ErrorAction Stop).Source

function Invoke-Check {
    param([string]$Name, [string]$Executable, [string[]]$Arguments)
    Write-Host "Running: $Name"
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Push-Location $projectRoot
try {
    Invoke-Check 'Backend tests' $pythonExe @('-m', 'pytest', '-q')
    Invoke-Check 'Python lint' $pythonExe @('-m', 'ruff', 'check', '--config', 'backend/pyproject.toml', 'backend/app', 'db', 'tests')
    Invoke-Check 'Frontend formatting' $npmExe @('--prefix', 'frontend', 'run', 'format:check')
    Invoke-Check 'Frontend tests' $npmExe @('--prefix', 'frontend', 'test')
    Invoke-Check 'Frontend build' $npmExe @('--prefix', 'frontend', 'run', 'build')
    if ($E2E) {
        $null = Invoke-WebRequest 'http://127.0.0.1:8000/openapi.json' -UseBasicParsing -TimeoutSec 10
        Invoke-Check 'Browser integration' $npmExe @('--prefix', 'frontend', 'run', 'test:e2e')
    }
    if ($QueryPlans) {
        Invoke-Check 'Read-only application query plans' $pythonExe @('-m', 'db.query_plan', '--database', 'application')
    }
}
finally {
    Pop-Location
}

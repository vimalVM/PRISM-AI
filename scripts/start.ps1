# scripts/start.ps1 — One-command offline startup for Sovereign AI Workbench
# Implements Phase 14 Task 1: sets offline env, verifies Ollama, warms models, launches workbench

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " SOVEREIGN AI WORKBENCH -- OFFLINE STARTUP                       " -ForegroundColor Cyan
Write-Host " Air-Gapped Confidential Industrial Knowledge System             " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Enforce strict offline and air-gap environment variables
Write-Host ""
Write-Host "[1/6] Enforcing strict offline environment policies..." -ForegroundColor Yellow
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:ANONYMIZED_TELEMETRY = "False"
$env:DO_NOT_TRACK = "1"
$env:OMP_NUM_THREADS = "1"
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:PYTHONPATH = "$RepoRoot"
Write-Host "      Offline environment flags configured (telemetry disabled)." -ForegroundColor Green

# 2. Verify Python environment
Write-Host ""
Write-Host "[2/6] Verifying local Python environment..." -ForegroundColor Yellow
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[FAIL] Python virtualenv not found at $PythonExe" -ForegroundColor Red
    Write-Host "       Please initialize the environment with: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}
Write-Host "      Python binary: $PythonExe" -ForegroundColor Green

# 3. Verify Ollama local service
Write-Host ""
Write-Host "[3/6] Verifying local Ollama service at http://127.0.0.1:11434..." -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    $installedModels = $resp.models | ForEach-Object { $_.name }
    Write-Host "      Ollama is online! Installed models: $($installedModels -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Ollama service not reachable on 127.0.0.1:11434." -ForegroundColor Red
    Write-Host "       Please start the Ollama daemon: ollama serve" -ForegroundColor Yellow
    exit 1
}

# 4. Pre-warm local models (one at a time to honor workstation VRAM limits)
Write-Host ""
Write-Host "[4/6] Pre-warming local models..." -ForegroundColor Yellow
& $PythonExe -c @"
import urllib.request, json
def warm_model(name):
    print(f'      Warming {name}...')
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:11434/api/generate',
            data=json.dumps({'model': name, 'prompt': 'ping', 'stream': False, 'options': {'num_predict': 1}}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            pass
        print(f'      -> {name} warmed successfully.')
    except Exception as e:
        print(f'      -> Warning warming {name}: {e}')

warm_model('qwen3.5:4b')
warm_model('gemma4:e4b')
"@

# 5. Verify database and seed standard demo credentials if needed
Write-Host ""
Write-Host "[5/6] Ensuring demo data and database are initialized..." -ForegroundColor Yellow
& $PythonExe -c @"
import os
os.environ['SEED_DEFAULT_PASSWORD'] = 'Sovereign2026!'
from scripts.seed_users import seed_users
seed_users()
"@
Write-Host "      Standard demo credentials: admin, engineer, reviewer, auditor (Password: Sovereign2026!)" -ForegroundColor Green

# 6. Verify built frontend
$DistIndex = Join-Path $RepoRoot "frontend\dist\index.html"
if (-not (Test-Path $DistIndex)) {
    Write-Host "      Building frontend production bundle..." -ForegroundColor Yellow
    Push-Location frontend
    try {
        npm.cmd run build
    } finally {
        Pop-Location
    }
}
Write-Host "      Frontend bundle ready at frontend/dist" -ForegroundColor Green

# 7. Start FastAPI server and open browser
Write-Host ""
Write-Host "[6/6] Launching Sovereign AI Workbench on http://127.0.0.1:8000..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Green
Write-Host " Sovereign AI Workbench running locally." -ForegroundColor Green
Write-Host " Press Ctrl+C in this terminal to stop the application." -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

# Open default browser after a brief delay
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:8000"
} | Out-Null

& $PythonExe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

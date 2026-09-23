# scripts/check_all.ps1 — Full CI/Verification Suite for Sovereign AI Workbench
# Implements Phase 13 Acceptance Criteria (check_all CI runner)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " SOVEREIGN AI WORKBENCH -- FULL CI VERIFICATION SUITE            " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Egress & Sovereignty Security Scan
Write-Host ""
Write-Host "[1/5] Running zero-egress scanner across all code and configs..." -ForegroundColor Yellow
& .venv\Scripts\python.exe scripts\scan_egress.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Egress scanner reported forbidden endpoints or telemetry." -ForegroundColor Red
    exit 1
}
Write-Host '[PASS] Egress scan clean: 0 cloud endpoints, 0 telemetry.' -ForegroundColor Green

# 2. Frontend Production Build Check
Write-Host ""
Write-Host "[2/5] Verifying frontend production build (TypeScript + Vite)..." -ForegroundColor Yellow
Push-Location frontend
try {
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Frontend build failed." -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}
Write-Host '[PASS] Frontend built cleanly into frontend/dist.' -ForegroundColor Green

# 3. Backend Unit & Integration Tests
Write-Host ""
Write-Host "[3/5] Executing full Pytest test suite..." -ForegroundColor Yellow
$env:OMP_NUM_THREADS = "1"
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
& .venv\Scripts\python.exe -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Pytest test suite encountered failures." -ForegroundColor Red
    exit 1
}
Write-Host '[PASS] All unit and integration tests passed.' -ForegroundColor Green

# 4. Evaluation Suite (EV-01 through EV-16)
Write-Host ""
Write-Host "[4/5] Executing Evaluation Suite (EV-01 through EV-16)..." -ForegroundColor Yellow
& .venv\Scripts\python.exe scripts\eval_run.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Evaluation suite failed one or more checks." -ForegroundColor Red
    exit 1
}
Write-Host '[PASS] All 16 evaluation checks passed (100 percent).' -ForegroundColor Green

# 5. Performance & Hardware Benchmarks
Write-Host ""
Write-Host "[5/5] Running benchmark harness..." -ForegroundColor Yellow
& .venv\Scripts\python.exe scripts\benchmark.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Benchmark suite failed." -ForegroundColor Red
    exit 1
}
Write-Host '[PASS] Benchmarks recorded to docs/evidence/benchmark.md.' -ForegroundColor Green

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host " ALL CHECKS PASSED: Sovereign AI Workbench is fully verified!     " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
exit 0

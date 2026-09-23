# Sovereign AI Workbench - Automated Sovereignty & Offline Evidence Collector
# Implements Phase 12 of docs/04_ANTIGRAVITY_BUILD_PLAN.md

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "    SOVEREIGN AI WORKBENCH - OFFLINE SOVEREIGNTY AUDITOR        " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$EvidenceDir = Join-Path $RepoRoot "docs\evidence"
$LogsDir = Join-Path $RepoRoot "logs"

if (-not (Test-Path $EvidenceDir)) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
}

# 1. Check Listening Ports
Write-Host ""
Write-Host "[1/5] Checking Loopback Listener Bindings (Evidence E2)..." -ForegroundColor Yellow
$ListenersFile = Join-Path $EvidenceDir "e2_listeners.txt"
$NetstatOutput = netstat -ano | Select-String "8000", "11434"

if ($NetstatOutput) {
    $NetstatOutput | Out-File -FilePath $ListenersFile -Encoding utf8
    Write-Host "Listeners found:" -ForegroundColor Green
    $NetstatOutput | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    Write-Host "Saved to: $ListenersFile" -ForegroundColor Green
} else {
    Write-Host "WARNING: Neither port 8000 nor 11434 is currently listening." -ForegroundColor Magenta
    Write-Host "Start FastAPI and Ollama to inspect live listener bindings." -ForegroundColor Gray
}

# 2. Run Static Egress Scan
Write-Host ""
Write-Host "[2/5] Running Static Egress Scanner (Evidence E6)..." -ForegroundColor Yellow
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$ScanScript = Join-Path $RepoRoot "scripts\scan_egress.py"

if (Test-Path $PythonExe) {
    & $PythonExe $ScanScript
    $ScanJson = Join-Path $LogsDir "egress_scan.json"
    $TargetJson = Join-Path $EvidenceDir "e6_egress_scan.json"
    if (Test-Path $ScanJson) {
        Copy-Item -Path $ScanJson -Destination $TargetJson -Force
        Write-Host "Egress scan output copied to: $TargetJson" -ForegroundColor Green
    }
} else {
    Write-Host "ERROR: Python virtual environment not found at $PythonExe" -ForegroundColor Red
}

# 3. Query Local Ollama Models (Evidence E1)
Write-Host ""
Write-Host "[3/5] Querying Local Ollama Models (Evidence E1)..." -ForegroundColor Yellow
$ModelsFile = Join-Path $EvidenceDir "models.txt"
try {
    $OllamaList = ollama list 2>&1
    $OllamaList | Out-File -FilePath $ModelsFile -Encoding utf8
    Write-Host "Local Models:" -ForegroundColor Green
    $OllamaList | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    Write-Host "Saved to: $ModelsFile" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Could not execute 'ollama list': $_" -ForegroundColor Magenta
}

# 4. Passive Non-Loopback Socket Audit
Write-Host ""
Write-Host "[4/5] Passive Non-Loopback Socket Audit (Evidence E5)..." -ForegroundColor Yellow
$AuditScript = Join-Path $RepoRoot "scripts\audit_sockets.py"

try {
    $AuditJson = & $PythonExe $AuditScript 2>&1
    Write-Host "Socket Audit Result:" -ForegroundColor Green
    Write-Host $AuditJson -ForegroundColor Gray
} catch {
    Write-Host "WARNING: Failed to run passive socket audit: $_" -ForegroundColor Magenta
}

# 5. Summary & Firewall Guidance
Write-Host ""
Write-Host "[5/5] Firewall Isolation Command Recipes (Evidence E3)..." -ForegroundColor Yellow
Write-Host "To apply defense-in-depth outbound blocking rules on Windows, run as Administrator:" -ForegroundColor Cyan
Write-Host "  netsh advfirewall firewall add rule name='SAW block python' dir=out action=block program='$PythonExe' enable=yes" -ForegroundColor Gray
Write-Host '  netsh advfirewall firewall add rule name="SAW block ollama" dir=out action=block program="%LOCALAPPDATA%\Programs\Ollama\ollama.exe" enable=yes' -ForegroundColor Gray
Write-Host "To remove rules after demonstration:" -ForegroundColor Cyan
Write-Host '  netsh advfirewall firewall delete rule name="SAW block python"' -ForegroundColor Gray
Write-Host '  netsh advfirewall firewall delete rule name="SAW block ollama"' -ForegroundColor Gray

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Sovereignty audit checklist complete. See docs\evidence\README.md" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

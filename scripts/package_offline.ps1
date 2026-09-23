# scripts/package_offline.ps1 — Offline Distribution Packaging & Checksum Generator
# Implements Phase 14 Task 2: Wheelhouse, Docker save, model bundle manifest, and SHA256 checksums

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " SOVEREIGN AI WORKBENCH -- OFFLINE PACKAGE GENERATOR             " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$DistDir = Join-Path $RepoRoot "dist\offline_package"
if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
}

$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

# 1. Generate Python Wheelhouse
Write-Host ""
Write-Host "[1/5] Checking Python offline wheelhouse..." -ForegroundColor Yellow
$WheelhouseDir = Join-Path $DistDir "wheelhouse"
if (-not (Test-Path $WheelhouseDir)) {
    New-Item -ItemType Directory -Path $WheelhouseDir -Force | Out-Null
}
Write-Host "      Wheelhouse path: $WheelhouseDir"
Write-Host "      (To download full wheels while connected, run: pip wheel -r requirements.txt -w $WheelhouseDir)"

# 2. Docker Sandbox Image Export
Write-Host ""
Write-Host "[2/5] Checking Docker sandbox image export..." -ForegroundColor Yellow
$DockerTar = Join-Path $DistDir "sovereign-sandbox.tar"
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        $img = docker images -q sovereign-sandbox:latest
        if ($img) {
            Write-Host "      Exporting Docker sandbox image to $DockerTar..."
            docker save sovereign-sandbox:latest -o $DockerTar
            Write-Host "      [OK] Docker image exported: $(Get-Item $DockerTar | ForEach-Object { [math]::Round($_.Length / 1MB, 2) }) MB" -ForegroundColor Green
        } else {
            Write-Host "      [INFO] sovereign-sandbox:latest image not yet built. Dockerfile is in docker/sandbox/Dockerfile"
        }
    } catch {
        Write-Host "      [WARNING] Docker daemon not reachable. Skipping docker save."
    }
} else {
    Write-Host "      [INFO] Docker CLI not installed or not in PATH."
}

# 3. Model Weights & Offline Assets Verification
Write-Host ""
Write-Host "[3/5] Cataloging local model weights and embedding stores..." -ForegroundColor Yellow
$EmbeddingsDir = Join-Path $RepoRoot "data\models\Qwen3-Embedding-0.6B"
if (Test-Path $EmbeddingsDir) {
    Write-Host "      [OK] Local embedding weights: $EmbeddingsDir" -ForegroundColor Green
} else {
    Write-Host "      [INFO] Embedding weights directory: $EmbeddingsDir"
}

# 4. Generate SHA256 Manifest
Write-Host ""
Write-Host "[4/5] Computing SHA-256 integrity checksum manifest..." -ForegroundColor Yellow
$ChecksumFile = Join-Path $DistDir "SHA256SUMS.txt"
$ItemsToHash = @(
    "models\registry.yaml",
    "templates\approval_note.docx",
    "templates\report.docx",
    "templates\presentation.pptx",
    "requirements.txt",
    "docker\sandbox\Dockerfile"
)

$Lines = @()
foreach ($relPath in $ItemsToHash) {
    $fullPath = Join-Path $RepoRoot $relPath
    if (Test-Path $fullPath) {
        $hash = (Get-FileHash -Path $fullPath -Algorithm SHA256).Hash.ToLower()
        $Lines += "$hash  $relPath"
    }
}

Set-Content -Path $ChecksumFile -Value $Lines -Encoding UTF8
Write-Host "      Generated checksum manifest: $ChecksumFile" -ForegroundColor Green

# 5. Generate Offline Package Manifest Document
Write-Host ""
Write-Host "[5/5] Generating OFFLINE_PACKAGE_MANIFEST.md..." -ForegroundColor Yellow
$ManifestPath = Join-Path $DistDir "OFFLINE_PACKAGE_MANIFEST.md"

$ManifestContent = @"
# Sovereign AI Workbench — Offline Air-Gap Delivery Package Manifest

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC")  
**Compliance Standard:** AGENTS.md §2 (Hard Constraints: Zero Runtime Internet, Localhost Only)

---

## 1. Package Inventory & Checksums

The following core artifacts must match the checksums recorded in `SHA256SUMS.txt`:

$(($Lines | ForEach-Object { "- ``$_``" }) -join "`n")

---

## 2. Model Requirements (Ollama Air-Gapped Store)

Transfer the following models into the air-gapped host's local Ollama library:

| Model Role | Model Name | Format / Size | Minimum VRAM / RAM |
|---|---|---|---|
| **Primary (Reasoning/Coding)** | `qwen3.5:4b` | GGUF / ~3.4 GB | 4 GB VRAM / 8 GB RAM |
| **Vision (Multimodal)** | `gemma4:e4b` | GGUF / ~9.6 GB | 6 GB VRAM / 16 GB RAM |
| **Local Embeddings** | `Qwen3-Embedding-0.6B` | SafeTensors / ~1.2 GB | CPU / 2 GB RAM |

### Ollama Air-Gapped Model Transfer Procedure:
1. On an internet-connected staging machine:
   ```bash
   ollama pull qwen3.5:4b
   ollama pull gemma4:e4b
   ```
2. Copy the Ollama manifest and blob storage:
   - Windows: `%USERPROFILE%\.ollama\models`
   - Linux: `~/.ollama/models` or `/usr/share/ollama/.ollama/models`
3. Paste into the target workstation's `.ollama\models` directory.
4. Verify on target host:
   ```bash
   ollama list
   ```

---

## 3. Python Wheelhouse Offline Installation

To install dependencies on a machine with no internet connection:
```bash
pip install --no-index --find-links=./wheelhouse -r requirements.txt
```

---

## 4. Docker Sandbox Image Import

```bash
docker load -i sovereign-sandbox.tar
docker tag sovereign-sandbox:latest sovereign-sandbox:latest
```

---

## 5. Verification Checklist

- [ ] All SHA256 checksums match `SHA256SUMS.txt`
- [ ] Network adapter disabled (`ipconfig /all` or physical cable unplugged)
- [ ] `./scripts/check_all.ps1` runs with 100% pass rate
"@

Set-Content -Path $ManifestPath -Value $ManifestContent -Encoding UTF8
Write-Host "      Generated package manifest: $ManifestPath" -ForegroundColor Green

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host " Offline packaging manifest complete: dist/offline_package/      " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

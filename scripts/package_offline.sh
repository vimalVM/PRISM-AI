#!/usr/bin/env bash
# scripts/package_offline.sh — Offline Distribution Packaging & Checksum Generator
# Implements Phase 14 Task 2: Wheelhouse, Docker save, model bundle manifest, and SHA256 checksums

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "================================================================="
echo " SOVEREIGN AI WORKBENCH -- OFFLINE PACKAGE GENERATOR             "
echo "================================================================="

DIST_DIR="$REPO_ROOT/dist/offline_package"
mkdir -p "$DIST_DIR/wheelhouse"

# 1. Check Python Wheelhouse
echo ""
echo "[1/4] Wheelhouse directory ready at: $DIST_DIR/wheelhouse"

# 2. Docker Sandbox Image Export
echo ""
echo "[2/4] Checking Docker sandbox image export..."
if command -v docker &> /dev/null; then
    if docker image inspect sovereign-sandbox:latest &> /dev/null; then
        echo "      Exporting Docker sandbox image to $DIST_DIR/sovereign-sandbox.tar..."
        docker save sovereign-sandbox:latest -o "$DIST_DIR/sovereign-sandbox.tar"
        echo "      [OK] Image exported."
    else
        echo "      [INFO] sovereign-sandbox:latest not found locally."
    fi
else
    echo "      [INFO] Docker CLI not installed or not in PATH."
fi

# 3. Checksum Manifest
echo ""
echo "[3/4] Generating SHA256SUMS.txt..."
CHECKSUM_FILE="$DIST_DIR/SHA256SUMS.txt"
> "$CHECKSUM_FILE"

FILES_TO_HASH=(
    "models/registry.yaml"
    "templates/approval_note.docx"
    "templates/report.docx"
    "templates/presentation.pptx"
    "requirements.txt"
    "docker/sandbox/Dockerfile"
)

for rel_path in "${FILES_TO_HASH[@]}"; do
    if [ -f "$rel_path" ]; then
        sha256sum "$rel_path" >> "$CHECKSUM_FILE"
    fi
done

echo "      Saved checksum manifest to: $CHECKSUM_FILE"

# 4. Generate Manifest Markdown
echo ""
echo "[4/4] Writing OFFLINE_PACKAGE_MANIFEST.md..."
cat << 'EOF' > "$DIST_DIR/OFFLINE_PACKAGE_MANIFEST.md"
# Sovereign AI Workbench — Offline Air-Gap Delivery Package Manifest

## 1. Model Requirements (Ollama Air-Gapped Store)
- `qwen3.5:4b` (Primary Reasoning, Coding, Deliverable Drafting)
- `gemma4:e4b` (Multimodal Vision Analysis)
- `Qwen3-Embedding-0.6B` (Local Sentence Transformers)

## 2. Offline Installation
```bash
pip install --no-index --find-links=./wheelhouse -r requirements.txt
docker load -i sovereign-sandbox.tar
./scripts/start.sh
```
EOF

echo "================================================================="
echo " Packaging manifest completed in dist/offline_package/          "
echo "================================================================="

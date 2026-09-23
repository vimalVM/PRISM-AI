#!/usr/bin/env bash
# scripts/start.sh — One-command offline startup for Sovereign AI Workbench
# Implements Phase 14 Task 1: sets offline env, verifies Ollama, warms models, launches workbench

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "================================================================="
echo " SOVEREIGN AI WORKBENCH -- OFFLINE STARTUP                       "
echo " Air-Gapped Confidential Industrial Knowledge System             "
echo "================================================================="

# 1. Enforce strict offline and air-gap environment variables
echo ""
echo "[1/6] Enforcing strict offline environment policies..."
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export ANONYMIZED_TELEMETRY=False
export DO_NOT_TRACK=1
export OMP_NUM_THREADS=1
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH="$REPO_ROOT"
echo "      Offline environment flags configured (telemetry disabled)."

# 2. Verify Python environment
echo ""
echo "[2/6] Verifying local Python environment..."
PYTHON_BIN="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_BIN=".venv/Scripts/python.exe"
fi
echo "      Using Python: $PYTHON_BIN"

# 3. Verify Ollama local service
echo ""
echo "[3/6] Verifying local Ollama service at http://127.0.0.1:11434..."
if ! curl -s --max-time 3 http://127.0.0.1:11434/api/tags > /dev/null; then
    echo "[FAIL] Ollama service not reachable on 127.0.0.1:11434."
    echo "       Please start the Ollama daemon: ollama serve"
    exit 1
fi
echo "      Ollama service is reachable."

# 4. Pre-warm local models (one at a time)
echo ""
echo "[4/6] Pre-warming local models..."
$PYTHON_BIN -c "
import urllib.request, json
def warm(name):
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
        print(f'      -> {name} warmed.')
    except Exception as e:
        print(f'      -> Warning warming {name}: {e}')

warm('qwen3.5:4b')
warm('gemma4:e4b')
"

# 5. Verify database and seed standard demo credentials
echo ""
echo "[5/6] Ensuring demo data and database are initialized..."
SEED_DEFAULT_PASSWORD="Sovereign2026!" $PYTHON_BIN -c "
from scripts.seed_users import seed_users
seed_users()
"

# 6. Verify built frontend
if [ ! -f "frontend/dist/index.html" ]; then
    echo "      Building frontend production bundle..."
    (cd frontend && npm run build)
fi
echo "      Frontend bundle ready at frontend/dist"

# 7. Start FastAPI server
echo ""
echo "[6/6] Launching Sovereign AI Workbench on http://127.0.0.1:8000..."
echo "================================================================="
echo " Sovereign AI Workbench running locally."
echo " Press Ctrl+C to stop."
echo "================================================================="

# Attempt to open browser in background
if command -v xdg-open &> /dev/null; then
    (sleep 2 && xdg-open "http://127.0.0.1:8000") &
elif command -v open &> /dev/null; then
    (sleep 2 && open "http://127.0.0.1:8000") &
fi

exec $PYTHON_BIN -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

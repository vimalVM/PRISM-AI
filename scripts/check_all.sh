#!/usr/bin/env bash
# scripts/check_all.sh — Full CI/Verification Suite for Sovereign AI Workbench
# Implements Phase 13 Acceptance Criteria (check_all CI runner)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "================================================================="
echo " SOVEREIGN AI WORKBENCH — FULL CI VERIFICATION SUITE            "
echo "================================================================="

# 1. Egress & Sovereignty Security Scan
echo ""
echo "[1/5] Running zero-egress scanner across all code and configs..."
python3 scripts/scan_egress.py
echo "[PASS] Egress scan clean (0 cloud endpoints / 0 telemetry)."

# 2. Frontend Production Build Check
echo ""
echo "[2/5] Verifying frontend production build (TypeScript + Vite)..."
(cd frontend && npm run build)
echo "[PASS] Frontend built cleanly into frontend/dist."

# 3. Backend Unit & Integration Tests
echo ""
echo "[3/5] Executing full Pytest test suite..."
export OMP_NUM_THREADS=1
export KMP_DUPLICATE_LIB_OK=TRUE
python3 -m pytest tests -q
echo "[PASS] All unit and integration tests passed."

# 4. Evaluation Suite (EV-01 through EV-16)
echo ""
echo "[4/5] Executing Evaluation Suite (EV-01 through EV-16)..."
python3 scripts/eval_run.py
echo "[PASS] All 16 evaluation checks passed (100%)."

# 5. Performance & Hardware Benchmarks
echo ""
echo "[5/5] Running benchmark harness..."
python3 scripts/benchmark.py
echo "[PASS] Benchmarks recorded to docs/evidence/benchmark.md."

echo ""
echo "================================================================="
echo " ALL CHECKS PASSED: Sovereign AI Workbench is fully verified!     "
echo "================================================================="

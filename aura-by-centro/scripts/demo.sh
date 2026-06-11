#!/usr/bin/env bash
# Aura (by Centro) — one-command demo launcher.
# Embedded mode (default): no Docker needed. Starts backend (which auto-seeds
# the sample docs), runs the smoke test, then launches the frontend.
# Ctrl-C stops everything (Ollama/Msty are left running).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

QDRANT_NAME="aura-qdrant"
BACKEND_PID=""

say() { printf "\n\033[1;36m▶ %s\033[0m\n" "$1"; }

# Auto-create .env from the template the first time — no manual step needed.
if [[ ! -f .env ]]; then
  cp .env.local.example .env
  echo "📝 Created .env from .env.local.example (edit it if your model/endpoint differs)."
fi

# Server mode only if the user explicitly set QDRANT_LOCAL=false in .env.
USE_SERVER_QDRANT=false
grep -qiE '^[[:space:]]*QDRANT_LOCAL[[:space:]]*=[[:space:]]*false' .env && USE_SERVER_QDRANT=true

cleanup() {
  printf "\n\033[1;33mShutting down the Aura demo…\033[0m\n"
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ "$USE_SERVER_QDRANT" == true ]] && docker rm -f "$QDRANT_NAME" >/dev/null 2>&1 || true
  echo "Stopped backend (+ Qdrant if used). (Your LLM engine is left running.)"
}
trap cleanup EXIT INT TERM

# ---- preflight ----
[[ -d backend/.venv ]] || { echo "❌ Backend venv missing — run:  make setup"; exit 1; }
[[ -d frontend/node_modules ]] || { echo "❌ Frontend deps missing — run:  make setup"; exit 1; }

# ---- 1. Vector store ----
if [[ "$USE_SERVER_QDRANT" == true ]]; then
  command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found (QDRANT_LOCAL=false). Install/launch Docker Desktop."; exit 1; }
  docker info >/dev/null 2>&1 || { echo "❌ Docker daemon not running. Open Docker Desktop and retry."; exit 1; }
  say "Starting Qdrant vector DB (Docker)"
  docker rm -f "$QDRANT_NAME" >/dev/null 2>&1 || true
  docker run --rm -d --name "$QDRANT_NAME" -p 6333:6333 \
    -v "$ROOT/qdrant_storage:/qdrant/storage" qdrant/qdrant >/dev/null
  printf "  waiting for Qdrant"
  until curl -sf http://localhost:6333/collections >/dev/null 2>&1; do printf "."; sleep 1; done
  echo " ready."
else
  say "Using embedded vector store (no Docker needed)"
fi

# ---- 2. Backend (auto-seeds sample docs on first run) ----
say "Starting FastAPI backend (http://localhost:8000)"
( cd backend && source .venv/bin/activate && exec uvicorn main:app --port 8000 --log-level warning ) &
BACKEND_PID=$!
printf "  waiting for backend"
until curl -sf http://localhost:8000/healthz >/dev/null 2>&1; do printf "."; sleep 1; done
echo " ready."

# ---- 3. Smoke test ----
say "Running pre-demo smoke test"
( cd backend && source .venv/bin/activate && python -m scripts.smoke_test ) || \
  echo "  (smoke test reported issues — fix before presenting; see START_HERE.md)"

# ---- 4. Frontend (foreground) ----
say "Starting frontend → open http://localhost:3000"
echo "  Admin dashboard: http://localhost:3000/admin"
echo "  Press Ctrl-C to stop everything."
cd frontend && npm run dev

#!/usr/bin/env bash
# Aura (by Centro) — one-command demo launcher.
# Starts Qdrant + backend, seeds RAG, runs the smoke test, then launches the
# frontend. Ctrl-C stops everything (Ollama/Msty are left running).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

QDRANT_NAME="aura-qdrant"
BACKEND_PID=""

say() { printf "\n\033[1;36m▶ %s\033[0m\n" "$1"; }

cleanup() {
  printf "\n\033[1;33mShutting down the Aura demo…\033[0m\n"
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  docker rm -f "$QDRANT_NAME" >/dev/null 2>&1 || true
  echo "Stopped backend + Qdrant. (Your LLM engine is left running.)"
}
trap cleanup EXIT INT TERM

# ---- preflight ----
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install/launch Docker Desktop."; exit 1; }
docker info >/dev/null 2>&1 || { echo "❌ Docker daemon not running. Open Docker Desktop and retry."; exit 1; }
# Auto-create .env from the template the first time — no manual step needed.
if [[ ! -f .env ]]; then
  cp .env.local.example .env
  echo "📝 Created .env from .env.local.example (edit it if your model/endpoint differs)."
fi
[[ -d backend/.venv ]] || { echo "❌ Backend venv missing — run:  make setup"; exit 1; }
[[ -d frontend/node_modules ]] || { echo "❌ Frontend deps missing — run:  make setup"; exit 1; }

# ---- 1. Qdrant ----
say "Starting Qdrant vector DB"
docker rm -f "$QDRANT_NAME" >/dev/null 2>&1 || true
docker run --rm -d --name "$QDRANT_NAME" -p 6333:6333 \
  -v "$ROOT/qdrant_storage:/qdrant/storage" qdrant/qdrant >/dev/null
printf "  waiting for Qdrant"
until curl -sf http://localhost:6333/collections >/dev/null 2>&1; do printf "."; sleep 1; done
echo " ready."

# ---- 2. Backend ----
say "Starting FastAPI backend (http://localhost:8000)"
( cd backend && source .venv/bin/activate && exec uvicorn main:app --port 8000 --log-level warning ) &
BACKEND_PID=$!
printf "  waiting for backend"
until curl -sf http://localhost:8000/healthz >/dev/null 2>&1; do printf "."; sleep 1; done
echo " ready."

# ---- 3. Seed RAG (idempotent enough for a demo) ----
say "Seeding RAG with sample documents"
( cd backend && source .venv/bin/activate && python -m scripts.ingest_docs --path ./sample_docs ) || \
  echo "  (ingestion reported an issue — usually the embedding endpoint; see smoke test)"

# ---- 4. Smoke test ----
say "Running pre-demo smoke test"
( cd backend && source .venv/bin/activate && python -m scripts.smoke_test ) || \
  echo "  (smoke test reported issues — fix before presenting; see START_HERE.md)"

# ---- 5. Frontend (foreground) ----
say "Starting frontend → open http://localhost:3000"
echo "  Admin dashboard: http://localhost:3000/admin"
echo "  Press Ctrl-C to stop everything."
cd frontend && npm run dev

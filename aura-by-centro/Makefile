# Aura (by Centro) — developer convenience targets.
# Usage: `make help`

SHELL := /bin/bash
PY := python3.11

.PHONY: help setup qdrant backend frontend ingest smoke clean

help:
	@echo "Aura (by Centro) — make targets"
	@echo "  make setup     Install backend venv + frontend deps"
	@echo "  make qdrant    Start the Qdrant vector DB (Docker, foreground)"
	@echo "  make backend   Run the FastAPI backend (uvicorn --reload)"
	@echo "  make frontend  Run the Next.js frontend (npm run dev)"
	@echo "  make ingest    Seed RAG with the sample documents"
	@echo "  make smoke     Verify LLM + embeddings + Qdrant are reachable"
	@echo ""
	@echo "Demo order: qdrant -> backend -> ingest -> smoke -> frontend"

setup:
	cd backend && $(PY) -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@echo "Done. Copy .env.local.example -> .env and set your Msty/Ollama endpoint."

qdrant:
	docker run --rm -p 6333:6333 -v "$(PWD)/qdrant_storage:/qdrant/storage" qdrant/qdrant

backend:
	cd backend && source .venv/bin/activate && uvicorn main:app --reload

frontend:
	cd frontend && npm run dev

ingest:
	cd backend && source .venv/bin/activate && $(PY) -m scripts.ingest_docs --path ./sample_docs

smoke:
	cd backend && source .venv/bin/activate && $(PY) -m scripts.smoke_test

clean:
	rm -rf backend/.venv frontend/node_modules frontend/.next qdrant_storage

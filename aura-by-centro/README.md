<div align="center">

# ✨ Aura — by Centro

**Your AI co-pilot buddy, making enterprise life easier.**

_Helping businesses drive meaningful change for growth._

<br/>

`Prussian Blue #004A59` · `Pure White #FFFFFF` · `Onyx Black #32373C` · Typeface: **Roboto**

</div>

---

Aura is an enterprise-grade, multi-tenant AI co-pilot for **Centro** — a global
BPO leader. It runs a **local Gemma-4** LLM (256K context) behind an
OpenAI-compatible endpoint, streams over **WebSockets**, integrates with **Zoho**
and **Odoo** via the **Model Context Protocol (MCP)**, and pairs **RAG** with a
semantic **CAG** cache.

Branding follows the **Centro Brand Book (by Pomelli)** — colours, Roboto
typeface, and an authoritative, professional, innovative voice grounded in
Centro's values: *Innovation, Efficiency, Operational Excellence, Accountability,
Precision.*

## Tech stack

| Layer            | Stack                                                       | Target  |
|------------------|-------------------------------------------------------------|---------|
| Frontend UI      | Next.js (App Router), React, Tailwind, Lucide               | Vercel  |
| Backend core     | Python 3.11+, FastAPI, Asyncio, WebSockets, Pydantic v2     | Railway |
| LLM engine       | Local Gemma-4 (256K) via OpenAI-compatible API              | —       |
| Vector engine    | Qdrant (ChromaDB supported), metadata filtering             | —       |
| Orchestration    | Lightweight multi-agent framework over MCP                  | —       |

## Repository layout

```text
aura-by-centro/
├── README.md · docker-compose.yml · .env.example · system_prompt.md
├── frontend/                  # Next.js [Vercel]
│   └── src/{app,components,hooks,lib}
├── backend/                   # FastAPI [Railway]
│   ├── main.py config.py models.py auth.py
│   ├── core/{agent,cache,sockets,vector_db,llm,embeddings}.py
│   └── integrations/{mcp_bridge,schema_registry}.py + schemas/ + scripts/
└── documentation/schemas_registry/   # live API contracts (Feature 4)
```

## The four core features → where they live

| # | Feature | Implementation |
|---|---------|----------------|
| 1 | **Metadata-Enforced Vector Sandboxing** — zero data leakage, filtered at the index layer | `backend/core/vector_db.py` (`_build_filter` compiles RBAC scope into a hard Qdrant filter) |
| 2 | **Semantic CAG Layer** — cosine ≥ 0.92 bypasses the LLM | `backend/core/cache.py` |
| 3 | **Interactive Action Cards** — dual confirmation before any mutation | `backend/core/agent.py` + `frontend/src/components/action-card.tsx` |
| 4 | **Dynamic API Schema Retrieval** — contracts loaded from registry, not prompts | `backend/integrations/schema_registry.py` + `documentation/schemas_registry/` |

All four obey the shared **socket contract**:

```json
{ "status": "streaming|completed|action_card|error",
  "session_id": "string",
  "payload": { "text": "string", "card_data": {} } }
```

…and **graceful fallback**: on a Gemma-4 OOM/latency event the agent serves the
CAG cache or an enterprise message — the WebSocket is never dropped.

## Quick start

```bash
cd aura-by-centro
cp .env.example .env            # fill in LLM + integration values

# Option A — full stack (Qdrant + backend + frontend)
docker compose up --build

# Option B — local dev
#   backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
#   frontend (new shell)
cd frontend && npm install && npm run dev
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000 (WS at `/ws`, health at `/healthz`)

## RBAC & data isolation

Connect with a token whose claims set `account_scope` (`coastline` | `trueblue` |
`global`), `role`, and `department`. A **Coastline** agent's queries can only ever
match documents where `account_scope ∈ {coastline, global}` — enforced inside the
vector engine, never post-filtered in Python.

## Documentation
- **[documentation/ARCHITECTURE.md](./documentation/ARCHITECTURE.md)** — CTO brief: Advanced & Agentic RAG, security, cost, stack.
- **[documentation/GUIDE.md](./documentation/GUIDE.md)** — run locally, test every feature, deploy to AWS, troubleshoot.
- **[documentation/ROADMAP.md](./documentation/ROADMAP.md)** — action items + pre-demo enhancement TODO.
- **[documentation/BRANDING.md](./documentation/BRANDING.md)** — colors, font, and which logo/favicon files to replace.
- CTO collateral: `documentation/Aura_by_Centro_CTO_Onepager.pdf` and `…_CTO_Deck.pdf`.

## Quick start (TL;DR)
```bash
OLLAMA_KEEP_ALIVE=-1 ollama serve   # terminal 1 (after: ollama pull qwen2.5:1.5b nomic-embed-text)
make setup && make demo             # terminal 2 — no Docker needed
```

> Built to the spec in [`system_prompt.md`](./system_prompt.md).

# SYSTEM ARCHITECTURE & CODE GENERATION INSTRUCTIONS: AURA (BY CENTRO)

You are an expert software architect and elite full-stack engineer. Your mission is to scaffold, build, and refine "Aura (by Centro)", an enterprise-grade, multi-tenant AI Co-Pilot built from scratch. Aura uses a local Gemma-4 LLM, uses WebSockets for real-time streaming, integrates with Zoho and Odoo via the Model Context Protocol (MCP), and implements a dual RAG (Retrieval-Augmented Generation) and CAG (Cache-Augmented Generation) memory model.

> This file is the canonical spec for the project. The architecture in this
> repository was scaffolded directly from it. See `README.md` for how each
> feature maps to the code.

---

## 1. TECH STACK & DEPLOYMENT TARGETS
*   **Frontend UI:** Next.js (App Router), React, Tailwind CSS, Lucide Icons. [Target: Vercel]
*   **Backend Core:** Python 3.11+, FastAPI, Asyncio, WebSockets. [Target: Railway]
*   **LLM Engine:** Local Gemma-4 (256K Context Window) accessed via an OpenAI-compatible API endpoint.
*   **Vector Engine:** Qdrant or ChromaDB with metadata-filtering support.
*   **Orchestration & Integration:** Custom lightweight Multi-Agent framework utilizing Model Context Protocol (MCP).

## 2. CORE FEATURES
1. **Metadata-Enforced Vector Sandboxing** — zero data leakage, enforced at the index layer (`core/vector_db.py`).
2. **Semantic CAG Layer** — cosine match >= 0.92 bypasses Gemma-4 (`core/cache.py`).
3. **Interactive Disambiguation Action Cards** — dual confirmation for mutations (`core/agent.py`, `components/action-card.tsx`).
4. **Dynamic API Schema Retrieval** — live contracts from `/documentation/schemas_registry/` (`integrations/schema_registry.py`).

## 3. CODE PATTERNS
- Async by default, Pydantic v2 DTOs, strict TypeScript.
- Every socket frame conforms to `{ status, session_id, payload }`.
- Graceful fallback on Gemma-4 OOM/latency — never drop the WebSocket.

## 4. BRAND (Centro Brand Book — Pomelli)
- Prussian Blue `#004A59`, Pure White `#FFFFFF`, Onyx Black `#32373C`.
- Primary typeface: **Roboto**.
- Voice: Professional, Strategic, Innovative, Authoritative.
- Values: Innovation, Efficiency, Operational Excellence, Accountability, Precision.

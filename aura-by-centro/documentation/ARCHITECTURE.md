# Aura (by Centro) — Technical Architecture & CTO Brief

**Aura is an enterprise, multi-tenant AI Co-Pilot that runs entirely on Centro-owned
infrastructure.** It pairs a local LLM with a state-of-the-art **Advanced & Agentic
RAG** retrieval stack, hard tenant isolation at the database layer, and human-in-the-loop
action workflows — at **$0 software licensing**.

---

## 1. The headline: a production-grade retrieval brain

Most "AI chatbots" are *Naive RAG* — embed the query, grab the nearest 5 chunks,
hope for the best. Aura goes well beyond that with a **four-pillar Advanced &
Agentic RAG pipeline**:

| Pillar | What it does | Why the CTO cares |
|--------|--------------|-------------------|
| **1 · Smart Chunking** | Header-aware Markdown splitting, JSON-object-coupled schema chunking, and **Parent-Child** retrieval (embed precise sentences, return whole sections) | Policies and API contracts never get sliced mid-thought → far higher answer accuracy |
| **2 · Hybrid Search** | **Dense** vector search (semantic) fused with **Sparse BM25** keyword search via **Reciprocal Rank Fusion** | Understands *"how do I take time off"* AND nails exact strings like *"Error 403"* or *"Agent ID TX-99"* |
| **3 · Cross-Encoder Reranking** | A second pass strictly re-orders the top candidates; only the best 5 reach the LLM | Stops the model being distracted by near-misses → **measurably fewer hallucinations** |
| **4 · Agentic Rewrite → Route → Reflect** | The agent rewrites messy prompts, routes to the right knowledge by RBAC, and **re-searches if results are weak** instead of guessing | Turns a passive search bar into an **active investigator** that refuses to make things up |

Every pillar is implemented, flag-controlled, and **degrades gracefully** — if a
heavy component is unavailable, Aura falls back to a faster path rather than failing.

### Request lifecycle
```
User ─▶ Small-talk?  ─▶ instant reply (no LLM, works offline)
          │ no
          ▼
       CAG cache  ─▶ semantic match ≥ 0.92  ─▶ instant reply (LLM bypassed)
          │ miss
          ▼
   Agentic RAG:  Rewrite ─▶ Route(RBAC) ─▶ Hybrid Search(Dense+BM25, RRF)
                        ─▶ Rerank(top 20→5) ─▶ Reflect(retry if weak)
          │ grounded context
          ▼
     Local LLM (streamed)  ─▶ answer + 📄 source citations
          │ on OOM/latency
          ▼
     Graceful fallback (cache / enterprise message — socket never drops)
```

---

## 2. Zero-trust data isolation (multi-tenant by design)

- Every chunk carries mandatory metadata: `department`, `account_scope`
  (`coastline` | `trueblue` | `global`), `min_role_required`.
- RBAC is compiled into a **hard Boolean filter executed inside the vector
  database** — on **both** the dense and the BM25 keyword paths. A Trueblue agent
  is *physically incapable* of retrieving Coastline data; isolation is never a
  fragile Python `if`-check after the fact.
- **Grounded-only:** if nothing is retrievable in the user's scope, Aura returns a
  deterministic "not in your knowledge" message — it will **not** let the LLM
  invent a policy. (This closed a real cross-tenant hallucination during testing.)
- The CAG cache is itself scope-aware and tagged by the *source document's* scope,
  so a broad-access manager can never accidentally cache tenant data as global.

---

## 3. Speed & cost engineering

- **Semantic CAG cache** + **rule-based small talk** serve common queries in
  **milliseconds with zero LLM cost**. The admin dashboard shows the live
  **"instant (no-LLM) rate"** — a direct compute-savings metric for the CTO.
- **Parent-child + reranking** keep the LLM prompt small and on-point → faster
  time-to-first-token on commodity hardware.
- **Model-agnostic:** any OpenAI-compatible endpoint. Demo runs a 0.5–1.5B model
  on a laptop; production scales to a larger (or multimodal) model on one AWS GPU.

| Cost driver | Aura |
|-------------|------|
| LLM licensing / per-token fees | **$0** — local open-weight model |
| Vector DB | **$0** — Qdrant (embedded locally, self-hosted on AWS) |
| Request store | **$0** — SQLite now; PostgreSQL/RDS at scale |
| Data egress / 3rd-party AI | **None** — data never leaves Centro |
| Real recurring cost | **only AWS GPU compute** |

---

## 4. Action workflows (human-in-the-loop)

For requests that change systems — **annual/casual leave, shift swaps, break-time
changes** — Aura renders a clean interactive form, and **only on the user's
confirmation** records the request (SQLite → CSV export for Workforce), emails the
team, and (when enabled) files it into **Zoho People via MCP**. No silent writes.

---

## 5. Stack & deployment

| Layer | Tech | AWS target |
|-------|------|------------|
| Frontend | Next.js · React · Tailwind · Roboto | Amplify / S3+CloudFront |
| Backend | FastAPI · async · WebSockets · Pydantic v2 | ECS Fargate / App Runner |
| LLM | Local open-weight (OpenAI-compatible) | EC2 GPU + vLLM |
| Retrieval | Qdrant (dense) + in-process BM25 (sparse) + reranker | Qdrant server on EC2/ECS |
| Integrations | Model Context Protocol (Zoho/Odoo/Genesys) | — |
| Delivery | Web · branded desktop client · embedded in Zoho People | — |

---

## 6. Why this wins the room
1. **It's not a wrapper** — it's a defensible retrieval architecture (hybrid +
   rerank + agentic) most vendors charge enterprise SaaS fees for.
2. **It's private and compliant** — every byte stays on Centro infrastructure;
   tenant isolation is enforced at the database index.
3. **It's safe** — grounded-only answers, no silent writes, full audit trail.
4. **It's cheap to run and easy to scale** — $0 licensing, one config flip from
   laptop to a multi-GPU AWS fleet for 1,500 users.

> Config flags for every advanced feature live in `backend/config.py`
> (`HYBRID_SEARCH_ENABLED`, `RERANK_ENABLED`, `CROSS_ENCODER_ENABLED`,
> `AGENTIC_REWRITE_ENABLED`, `CAG_AUTO_PROMOTE_GLOBAL`). Implementation in
> `core/{chunking,retrieval,rerank,agent}.py`.

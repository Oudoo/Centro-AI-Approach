# Aura (by Centro) — Roadmap & Open Action Items

A running list of decisions and upgrades. ✅ = done, 🔲 = open action item.

---

## 🔲 ACTION ITEM 1 — Upgrade to a larger, multimodal model (vision, etc.)

**Owner:** us (post-POC). **Why:** the demo runs on small local Gemma 3 for speed
on an Intel CPU. For production at 1,500 users we want stronger reasoning *and*
multimodal capability (read screenshots, ID cards, invoices, scanned HR docs).

**The good news:** Aura is **model-agnostic** — it talks to any OpenAI-compatible
endpoint. Upgrading is a config change plus infra, not a rewrite.

What an upgrade unlocks and what it needs:

| Capability | Candidate models | Requirement |
|-----------|------------------|-------------|
| Bigger/better text reasoning | Gemma 3 12B / 27B, or larger | AWS EC2 GPU (vLLM) |
| **Vision** (images, scans, screenshots) | **Gemma 3 multimodal** (4B/12B/27B vision), Llama 3.2 Vision, Qwen2-VL | GPU + add an image part to the chat payload |
| Long-context document analysis | 256K-context Gemma build | More VRAM |

Concrete steps when we pick this up:
1. Stand up **vLLM on an AWS EC2 GPU** serving the chosen model (keeps the same
   OpenAI-compatible contract).
2. Point `LLM_BASE_URL` / `LLM_MODEL` at it — no app code change for text.
3. For vision: extend the chat message builder in `core/agent.py` and the
   frontend composer to accept image uploads (OpenAI `image_url` content parts);
   add an image-capable embedding/OCR path if we want images in RAG.
4. Benchmark latency/throughput for 1,500 concurrent users; size the GPU fleet.

> Decision needed later: target model + GPU instance type + budget. Not blocking
> the POC.

---

## 🔲 ACTION ITEM 2 — Choose the per-PC desktop client packaging

Electron (scaffolded) vs Tauri vs PWA. Full analysis in
[`DESKTOP_CLIENT_OPTIONS.md`](./DESKTOP_CLIENT_OPTIONS.md). **Reply A / B / C** and
we wire the chosen path end-to-end.

---

## 🔲 ACTION ITEM 3 — Production auth / SSO

Today: dev JWT minting for local testing. Production: wire Centro SSO (e.g. Zoho
OAuth / SAML) to issue signed tokens carrying `account_scope`, `role`,
`department` so vector sandboxing maps to real identities.

---

## 🔲 ACTION ITEM 4 — Connect live MCP servers

Today: Action Cards + MCP bridge are real, but Odoo/Zoho/Genesys writes no-op
without live MCP servers. Stand up the MCP endpoints and set the `*_MCP_URL`
envs to make end-to-end mutations execute.

---

## 🔲 ACTION ITEM 5 — Configure SMTP for request emails

Today: requests run in **demo mode** — recorded to the DB and composed as an
email but only *logged* (no SMTP credentials). To actually send to
`mahmoud.hassan@centrocdx.com` (and later each reporting manager), set in `.env`:
```
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...        # use an app password / secrets manager in prod
SMTP_FROM=aura@centrocdx.com
```
Owner: you (provide the SMTP relay or a Zoho Mail app password).

---

## 🔲 ACTION ITEM 6 — Move requests store from SQLite to PostgreSQL (company scale)

Today: requests are stored in **SQLite** (free, file-based) — perfect for the
demo and single-node. SQLite is **never paid**. At company scale (1,500 users,
multiple backend instances, concurrent writes) migrate to **PostgreSQL on AWS
RDS**. The store is isolated in `backend/core/requests_store.py`, so this is a
small, contained change (swap the driver + connection string; same function
signatures). Owner: us, when we deploy to AWS.

---

## ✅ Done in the POC
- Monorepo scaffold, FastAPI WebSocket backbone, typed socket contract.
- Feature 1 — metadata-enforced vector sandboxing (index-layer isolation).
- Feature 2 — semantic CAG cache (>= 0.92 bypasses the LLM).
- Feature 3 — dual-confirmation Action Cards (now friendly request forms).
- Feature 4 — dynamic schema retrieval from the registry.
- Employee requests: leave / shift-swap / break-timing → SQLite + email + CSV export.
- Zoho People integration scaffold (MCP-backed, off by default).
- Admin dashboard + department-head document uploads (RBAC-gated).
- One-shot RAG ingestion + sample docs.
- `/embed` widget for the Zoho People Web Tab.
- Electron desktop client scaffold.
- Demo kit: smoke test, Makefile, demo guide, CTO one-pager PDF.
- Centro branding throughout (Prussian Blue / Onyx / Roboto).

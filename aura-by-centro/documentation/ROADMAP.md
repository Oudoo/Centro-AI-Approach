# Aura (by Centro) — Roadmap, Action Items & Pre-Demo TODO

✅ = done · 🔲 = open · ⛔ = must do before production

---

## A. Pre-demo enhancements (proposed) — pick what to build before CTO/HR demos

Ranked by impact-for-effort. **My top 3: A1, A2, A3.**

| # | Enhancement | Why it matters | Effort |
|---|-------------|----------------|--------|
| **A1** | **Demo identity switcher on the main chat** | Right now the main chat is anonymous (global FAQs only); tenant RAG needs the `/embed?token=` dance. A small "Acting as: Coastline Agent ▾" switcher lets HR show sandboxing live in one window. | S |
| **A2** | **Source citations under RAG answers** | Show "📄 Source: HR Handbook" beneath grounded replies → builds trust, proves it's not hallucinating. Great for the CTO. | S |
| **A3** | **Usage analytics tile on /admin** | Queries answered, **CAG hit-rate %** (cost saved), top intents. Gives the CTO concrete ROI numbers. | M |
| A4 | Request status workflow (submitted → approved/denied) + email the employee a copy | Closes the loop; HR-realistic | M |
| A5 | Suggested follow-up chips after answers | Smoother UX, guides the demo | S |
| A6 | Leave-balance preview in the leave form (mock until Zoho) | Feels production-ready | M |
| A7 | Mobile/responsive polish + the desktop client build | Broader reach | M |
| A8 | Guardrails: per-session rate limit + max message length | Safety for a live audience | S |

> Tell me which to build (e.g. "A1, A2, A3") and I'll implement them.

---

## B. Open action items

### 🔲 B1 — Choose the per-PC desktop client packaging
Thin client to the AWS backend. **Pick one:**
- **Electron** (scaffolded in `desktop/`): cross-platform `.exe`/`.dmg`, biggest ecosystem, ~150 MB. Best for a mixed Windows/Mac fleet.
- **Tauri** (Rust): tiny (~3–10 MB), low memory; needs Rust in CI.
- **PWA**: zero packaging, instant updates; least native control.

Reply **A/B/C** and I'll wire it end-to-end (icons, auto-update, baked-in AWS URL).

### 🔲 B2 — Production auth / SSO
Replace dev JWT minting with Centro SSO (Zoho OAuth / SAML) issuing signed tokens
carrying `account_scope`, `role`, `department`.

### 🔲 B3 — Connect live MCP servers
Stand up Zoho/Odoo/Genesys MCP endpoints; set `*_MCP_URL` +
`ZOHO_INTEGRATION_ENABLED=true` to file requests directly into Zoho.

### ⛔ B4 — Configure SMTP for request emails (before HR demo if real emails wanted)
Set `SMTP_*` in `.env` to actually send to `mahmoud.hassan@centrocdx.com`.

### ⛔ B5 — Move to server databases (BEFORE PRODUCTION)
Both stores are file-based/single-node today (SQLite for requests; embedded
Qdrant for vectors). SQLite is **free, never paid**, but won't scale to 1,500
users across multiple instances. Before production:
- Requests → **PostgreSQL on AWS RDS** (swap the one `requests_store.py` module).
- Vectors → **Qdrant server** (`QDRANT_LOCAL=false` + `QDRANT_URL`; Docker compose
  already wired). Keep Docker for this AWS path.

### ⛔ B6 — Keep Docker for the AWS/server deployment
Local dev needs no Docker (embedded mode). For AWS, the Qdrant server + the
backend run as containers (`docker-compose.yml`, Dockerfiles). Validate the
container build before production.

### 🔲 B7 — Upgrade to a larger / multimodal model on AWS GPU
Aura is model-agnostic. For production, serve a bigger model (and optionally a
vision model for scanned docs/IDs) on EC2 GPU via vLLM — config change, not a
rewrite.

---

## ✅ Done in the POC
- WebSocket backbone + typed contract; CAG cache; sandboxed RAG; grounded-only (no hallucination).
- Interactive request forms (swap shift / annual / casual leave / break timing) → SQLite + email + CSV export; Zoho integration scaffold (off by default).
- Admin dashboard (RBAC) + department-head uploads; embeddable Zoho People widget.
- Embedded vector store (no Docker for local dev) with first-run auto-seed.
- Centro branding (Prussian/Onyx/Roboto, Aura logo + favicon, branded API docs).
- Demo kit: smoke test, diag, Makefile (`make demo`), CTO one-pager + deck PDFs.

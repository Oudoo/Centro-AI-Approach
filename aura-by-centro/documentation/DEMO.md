# Aura (by Centro) — Demo Playbook

Your single guide for the CTO & HR demos: make it fast, sanity-check it, run the
script, then explain what's real, what's next (GPU/AWS), and how it ships
(Zoho People Web Tab or a desktop `.exe`/`.pkg`).

---

## 1. Make it as fast as possible (do this first)

```bash
# fastest small model + keep it warm in memory
ollama pull qwen2.5:0.5b          # (or qwen2.5:1.5b for slightly better answers)
OLLAMA_KEEP_ALIVE=-1 ollama serve
```
In `.env` (defaults are already demo-tuned):
```
LLM_MODEL=qwen2.5:0.5b
LLM_MAX_OUTPUT_TOKENS=512
HYBRID_SEARCH_ENABLED=true        # fast at demo scale
RERANK_ENABLED=true               # lexical reranker — milliseconds
AGENTIC_REWRITE_ENABLED=false     # keep OFF for speed (extra LLM call)
CROSS_ENCODER_ENABLED=false       # keep OFF (heavy model download)
LLM_WARMUP=true                   # first query won't pay the cold-load
```
Then: `make demo`. The backend warms the model on startup, so your **first**
question in front of the CTO is already fast.

> Why this is fast: greetings → instant (no model); common FAQs → CAG (no model);
> only novel questions hit the LLM, and the prompt is kept small by reranking +
> parent-child retrieval. The pure-Python hybrid/rerank adds ~milliseconds at
> demo scale — the LLM is the only meaningful cost.

---

## 2. Sanity checklist (5 minutes before, every time)

- [ ] `ollama list` shows your `LLM_MODEL` + `nomic-embed-text`.
- [ ] `make demo` reaches "Starting frontend" with **no red errors**.
- [ ] Smoke test printed all **PASS** (LLM, embeddings, vector store).
- [ ] http://localhost:3000 loads; header shows the Aura logo + "Connected".
- [ ] Tab favicon is the Centro "A" mark.
- [ ] http://localhost:3000/admin loads (dev sign-in buttons visible).
- [ ] Ask **"hi"** → instant friendly reply (proves small-talk/offline path).
- [ ] Ask **"How do I submit my resignation?"** → instant (CAG; log: `cag_hit`).

If any fail → see `GUIDE.md` §6 Troubleshooting.

---

## 3. Feature test checklist (run once before presenting)

- [ ] **CAG (instant)** — "How do I submit my resignation?" → instant.
- [ ] **Small talk / offline** — "hi", "thanks", "who are you" → instant (works even if Ollama is down).
- [ ] **RAG + citation** — "What's the expense reimbursement limit?" → streams an answer ending with "📄 Source: …".
- [ ] **Hybrid exact-match** — upload a doc mentioning a code like "TX-99", then ask for it → retrieved precisely.
- [ ] **Grounded-only** — ask something not in any doc → "I couldn't find anything in your knowledge…", no hallucination.
- [ ] **Sandboxing (A1 switcher)** — header dropdown **Acting as → Coastline Manager**, ask the Coastline overtime rule → answers; switch to **Trueblue Agent**, ask again → refused.
- [ ] **Action request** — "I want to request an annual leave" → fill form → **Submit** → confirmation → row in **/admin → Employee Requests** → **Export CSV**.
- [ ] **Admin analytics** — tiles show Queries / Instant-rate % / RAG / Requests.
- [ ] **Self-service upload** — upload a global `.md`; a matching question now answers instantly (auto-promoted to CAG).
- [ ] **Embed** — open `/embed?session=demo` → chrome-less widget.

---

## 4. The live demo script (what to click + what to say)

**Opening (30s).** "Aura is Centro's own AI co-pilot. It runs entirely on our
infrastructure — no data leaves Centro, no per-message AI fees."

1. **Say hi.** Type "hi" → instant. *"Greetings never even touch the model — and
   they work even if the AI engine is offline."*
2. **Ask an HR FAQ** ("How do I submit my resignation?") → instant. *"Common
   questions are served from a semantic cache in milliseconds — zero GPU cost.
   The dashboard tracks this 'instant rate' as real compute savings."*
3. **Ask a document question** ("What's the expense reimbursement limit?") →
   streams, ends with 📄 Source. *"This is Retrieval-Augmented Generation:
   it answers only from Centro's approved documents, and cites the source so
   it's auditable — it does not make things up."*
4. **Show the security story.** Header dropdown → **Coastline Manager**, ask the
   Coastline overtime rule → answers. Switch → **Trueblue Agent**, same question
   → refused. *"Tenant isolation is enforced inside the database — a Trueblue
   user is physically unable to retrieve Coastline data."*
5. **File a request.** "I want to request an annual leave" → form → Submit.
   Open **/admin** → the request is logged + exportable to Excel. *"Anything that
   changes a system needs a human confirmation, and everything is audited."*
6. **(Optional) Architecture slide.** Show the deck's *Advanced & Agentic RAG*
   slide. *"Under the hood this is hybrid search + reranking + an agentic loop —
   the retrieval stack vendors charge enterprise fees for, running at $0
   licensing on our own hardware."*

Keep `documentation/ARCHITECTURE.md` open for deep-dive questions.

---

## 5. How it behaves after the demo (what's real vs. staged)

| Capability | Status today |
|------------|--------------|
| Chat, CAG, RAG, hybrid+rerank, sandboxing, grounded-only | **Real & working** |
| Document upload + per-tenant scoping | **Real** |
| Requests → SQLite + CSV export | **Real** |
| Email to `mahmoud.hassan@centrocdx.com` | **Real if SMTP set**, else demo-logged |
| Zoho People filing of requests | **Scaffolded** — turns on with a live Zoho MCP server |
| Identity / login | **Dev tokens** today → real SSO at production |
| Model | small local model for laptop speed → bigger/multimodal on GPU |

---

## 6. Next stages — after the GPUs & AWS

Aura is **model-agnostic and config-driven**, so going to production is config +
infra, not a rewrite.

1. **GPU model upgrade (biggest visible win).** Serve a larger (and optionally
   **multimodal/vision**) model on an **AWS EC2 GPU via vLLM**. Same
   OpenAI-compatible contract — just point `LLM_BASE_URL`/`LLM_MODEL` at it.
   Result: **much faster** responses and stronger reasoning (clean age math,
   document understanding, reading scanned IDs/invoices).
2. **Production retrieval.** Flip on the **cross-encoder reranker** and switch to
   **Qdrant server** (`QDRANT_LOCAL=false`); optionally enable **agentic query
   rewrite** now that latency is cheap on GPU.
3. **Scale-out.** Backend on **ECS Fargate**, frontend on **Amplify/CloudFront**,
   requests in **PostgreSQL on RDS**, secrets in **Secrets Manager**. Size the GPU
   fleet for ~1,500 concurrent users.
4. **SSO + live integrations.** Wire Centro SSO for real per-employee identity;
   enable the Zoho/Odoo/Genesys MCP servers so requests post directly into Zoho.

(See `ROADMAP.md` for the tracked action items, including the pre-production gates.)

---

## 7. How it ships to employees

**Option A — Embedded in Zoho People (fastest rollout).**
Aura has a chrome-less widget at `/embed`. In **Zoho People → Settings →
Customization → Web Tabs → Add Web Tab → External URL**:
```
https://aura.centro.example/embed?session=${EmployeeID}&token=${SignedJWT}
```
The signed token carries the employee's account/role, so sandboxing applies
automatically. Employees use Aura **without leaving their HR portal**. Zero
install.

**Option B — Desktop app per PC (`.exe` / `.pkg`/`.dmg`).**
A branded thin-client (Electron, scaffolded in `desktop/`) that connects to the
same AWS backend, with a tray icon + global hotkey. Build installers:
```
AURA_URL=https://aura.centro.example npm run dist:win   # Windows .exe
AURA_URL=https://aura.centro.example npm run dist:mac   # macOS .dmg/.pkg
```
The model never runs on the PC — it's just the UI talking to AWS.

> Recommendation: **lead with the Zoho People Web Tab** (instant, nothing to
> install), and offer the desktop app for power users / always-on access.
> Packaging choice (Electron vs Tauri vs PWA) is tracked in `ROADMAP.md` B1.

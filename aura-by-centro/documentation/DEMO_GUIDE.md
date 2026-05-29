# Aura (by Centro) — Demo & Proof-of-Concept Guide

## 0. Are you understanding the git model right? (Yes — with one nuance)

You're safe. Here's exactly what's happening:

- **`main`** = your stable Centro AI "big project" branch. **Untouched.** Nothing
  you've done has changed it.
- **`claude/aura-centro-chatbot-SqC64`** = the feature branch where *all* of Aura
  lives. Every commit so far is here.
- **PR #5** is only a *proposal* to merge this branch into `main`. `main` does not
  change until someone explicitly clicks "Merge". You can leave the PR open
  indefinitely.

**The nuance:** a *branch* and a *sub-project* are two different ideas, and right
now you're using both:

| Concept | What it is here |
|--------|------------------|
| **Branch** (`claude/aura-...`) | A parallel line of development. Keeps Aura's history separate from `main` until you're ready. |
| **Sub-project folder** (`aura-by-centro/`) | Aura is a self-contained app living in its own folder inside the same repo (a *monorepo* sub-project). |

So: **Aura is a sub-project (folder) being developed on its own branch.** That's a
clean, normal pattern. When the CTO is happy, you merge the branch → `main` and
`aura-by-centro/` becomes a permanent part of the big project. If you'd rather it
be a *fully separate repository* later, that's a one-time "extract to new repo"
step — tell me and I'll do it.

### How to keep committing to the branch (you already are)
```bash
git checkout claude/aura-centro-chatbot-SqC64   # make sure you're on it
git pull origin claude/aura-centro-chatbot-SqC64 # get my latest commits
# ...make changes...
git add -A && git commit -m "your message"
git push origin claude/aura-centro-chatbot-SqC64 # never touches main
```
As long as you push to this branch (not `main`), the big project's stable line is
never at risk.

---

## 1. Fastest reliable demo setup (Intel Mac)

**Demo on the Gemma you already have.** Aura doesn't care which app serves the
model — it only needs an **OpenAI-compatible endpoint**, and Msty Studio provides
exactly that. So your local **Gemma 3** and **Gemma 4** are fully demo-ready.

There is exactly **one** extra requirement beyond your chat model: Aura's CAG
cache and RAG retrieval need a small **embedding model**. Pull one inside Msty
(e.g. `nomic-embed-text`, 768-dim) and you're done — no other tool required.

> Which model to demo on? Use **`qwen2.5:1.5b`** — since CAG + RAG supply the
> facts, a small instruction model only needs to phrase the answer, so it's fast
> and accurate on an Intel CPU. `qwen2.5:0.5b` is even faster; `llama3.2:1b` and
> `gemma3:1b` also work. Switch by changing one line (`LLM_MODEL`) in `.env`.

```bash
# 1. Start Ollama warm and pull the models:
OLLAMA_KEEP_ALIVE=-1 ollama serve
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text       # 768-dim embeddings (CAG + RAG)

# 2. Point Aura at Ollama (.env)
cd aura-by-centro && cp .env.local.example .env
#   LLM_BASE_URL=http://127.0.0.1:11434/v1
#   LLM_MODEL=qwen2.5:1.5b
#   EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
#   EMBEDDING_MODEL=nomic-embed-text

# 3. One-time install
make setup

# 4. Start the stack (4 terminals, or use the make targets)
make qdrant        # terminal 1 — vector DB
make backend       # terminal 2 — FastAPI
make ingest        # terminal 3 — seed RAG with sample docs (run once)
make smoke         # terminal 3 — VERIFY everything is green before you demo
make frontend      # terminal 4 — Next.js UI
```

> Not using Msty? Any OpenAI-compatible server works the same way (Ollama, vLLM,
> LM Studio). Just set `LLM_BASE_URL`/`EMBEDDING_BASE_URL` to that server. The
> app is engine-agnostic by design.


Open:
- **http://localhost:3000** — chat
- **http://localhost:3000/admin** — knowledge-base dashboard
- **http://localhost:8000/docs** — API (good for showing the backend is real)

> ⏱️ **Always run `make smoke` right before the demo.** It checks the LLM,
> embeddings, and Qdrant and prints PASS/FAIL so there are no surprises.

---

## 2. Proof-of-Concept script — one demo per feature

Run these in order. Each line is what to *do*, followed by what to *point out*.

### ✅ Feature 2 — Semantic CAG (instant, LLM bypassed)
1. In chat, click the suggestion **"How do I submit my resignation?"**
2. **Point out:** the answer returns *instantly* — the backend log shows
   `cag_hit score=0.9x`. This query never touched Gemma. "This is how we keep
   common HR questions free and sub-second at 1,500 users."

### ✅ Feature 1 — Metadata-enforced sandboxing (zero data leakage)
This is the headline security feature. Show it with two identities:
1. Go to **/admin**, click **"Sign in as Coastline Manager"**.
2. Back in chat (open `http://localhost:3000/?token=...` isn't needed for the
   scripted version — use the embed URL trick below), ask:
   *"What is the overtime authorization rule for Coastline?"* → **answers** (the
   `coastline-shift-ops` doc is in scope).
3. Now demonstrate isolation: a **Trueblue** or **global agent** asking the same
   question gets *"no documents in your access scope"*.
4. **Point out:** the filter is applied **inside the vector database**, not in
   Python — a Coastline query is *physically incapable* of matching Trueblue
   data. (Show `core/vector_db.py::_build_filter`.)

> To act as a specific user in the chat UI, open:
> `http://localhost:3000/embed?session=demo&token=<JWT>`
> Get a JWT from **/admin** dev sign-in (it's stored in localStorage as
> `aura.token`), or call `POST /admin/dev-token` with a role/scope from
> http://localhost:8000/docs.

### ✅ Feature 3 — Action Cards (dual confirmation before any write)
1. In chat, click **"Run the Odoo payroll sync for Trueblue"**.
2. **Point out:** Aura does **not** execute. It renders an isolated card showing
   **Target System** (Odoo Payroll), **API Payload**, and a **HIGH risk**
   assessment, with **Confirm / Cancel**.
3. Click **Cancel** → "Action cancelled, no changes." Then try again and
   **Confirm** → it attempts the MCP call (no-op without a live Odoo server, but
   the contract path is real).
4. **Point out:** "No destructive action ever fires without a human confirming
   the exact payload. This is our guardrail for payroll, scheduling, approvals."

### ✅ Feature 4 — Dynamic schema retrieval (no prompt hardcoding)
1. Open `documentation/schemas_registry/odoo_payroll.json`.
2. **Point out:** the Action Card's target system, payload shape, and risk text
   all came from this file — not from a prompt. "When Odoo changes an endpoint,
   we drop a new JSON here (or sync it from WorkDrive) — no code change, no
   redeploy."

### ✅ Streaming + graceful fallback (enterprise resilience)
1. Ask any open question, e.g. *"Summarize our remote work policy."* → watch
   tokens **stream** in live.
2. (Optional) Stop Ollama mid-demo and ask again → instead of crashing, Aura
   serves a cached/enterprise fallback message and the socket stays alive.
3. **Point out:** "If the GPU cluster OOMs or spikes, users get a graceful
   message or a cached answer — the app never goes dark."

### ✅ Dynamic uploads (self-service for department heads)
1. On **/admin**, upload any `.md`/`.txt` (set Department=hr, Scope=global,
   Min role=agent).
2. Ask Aura a question answered by that file → it's retrieved live.
3. **Point out:** "Each department head curates their own knowledge, scoped to
   their account, with zero engineering involvement."

### ✅ Embed anywhere (Zoho People Web Tab)
1. Open `http://localhost:3000/embed?session=demo` — the chrome-less widget.
2. **Point out:** "This same widget drops into Zoho People as a Web Tab so agents
   never leave their HR portal." (See `SETUP_AND_DEPLOY.md` §4.)

---

## 3. CTO talking points (the "why it matters")

- **Cost:** $0 software licensing — all open-source; only real spend is the AWS
  GPU. Runs entirely on infrastructure we own. No per-token vendor billing.
- **Data sovereignty:** local Gemma + self-hosted vector DB = no customer/HR data
  leaves Centro. Tenant isolation is enforced at the database layer.
- **Safety:** every mutating action requires explicit human confirmation.
- **Maintainability:** integrations and knowledge update via files/uploads, not
  code — department heads self-serve.
- **Reach:** one UI, delivered three ways — web, branded desktop app per PC, and
  embedded inside Zoho People.

---

## 4. Troubleshooting (have this open during the demo)

| Symptom | Fix |
|--------|-----|
| `make smoke` fails on LLM | Is `ollama serve` running? Is `LLM_MODEL` (e.g. `qwen2.5:1.5b`) pulled? Run `ollama list`. |
| `make smoke` fails on embeddings | `ollama pull nomic-embed-text`; check `EMBEDDING_DIM=768`. |
| `make smoke` fails on Qdrant | Is `make qdrant` running / Docker Desktop started? |
| Chat connects but no answer | Run `make ingest`; check the backend terminal for errors. |
| Admin upload returns 403 | Sign in via /admin dev login (needs role ≥ manager). |
| Answers are slow | Use `qwen2.5:1.5b` (or `qwen2.5:0.5b`) and start Ollama with `OLLAMA_KEEP_ALIVE=-1` to keep the model warm. |

> Pro tip: do a **full dry run tonight** end-to-end, exactly as you'll present it.
> The first model load is the slowest; after that responses are warm.

# START HERE — Install, Run & Test Aura (by Centro) Yourself

A single, copy-paste path to get everything running on your MacBook and verify
**every feature** before you show the CTO. Budget ~30 minutes the first time.

We use **Ollama** as the engine — it's the cleanest workflow: one endpoint serves
both chat *and* embeddings, it's reliable on Intel, and it's fully scriptable.
(If you'd rather use Msty, see the note at the very bottom — the app is
engine-agnostic.)

---

## STEP 0 — Install prerequisites (once)

```bash
# Homebrew packages
brew install python@3.11 node ollama git

# Docker Desktop (for the Qdrant vector DB) — install + launch it:
#   https://www.docker.com/products/docker-desktop/
# Make sure the Docker whale icon is running before Step 3.
```

Verify:
```bash
python3.11 --version    # 3.11.x
node --version          # v20+ (any recent LTS is fine)
docker --version        # any
ollama --version        # any
```

## STEP 1 — Get the code (the Aura branch)

```bash
git clone https://github.com/Oudoo/Centro-AI-Approach.git
cd Centro-AI-Approach
git checkout claude/aura-centro-chatbot-SqC64   # the Aura branch (main is untouched)
cd aura-by-centro
```

## STEP 2 — Start the AI engine + pull models

```bash
ollama serve                    # leave running in its own terminal
# in another terminal:
ollama pull gemma3:1b           # chat model — fast on Intel CPU (use for the demo)
ollama pull nomic-embed-text    # embedding model — powers CAG + RAG (required)
```
> Optional: `ollama pull gemma3` (the larger 4B/8B) for higher quality — slower
> on CPU. You switch models by editing one line (`LLM_MODEL`) in `.env`.

## STEP 3 — Configure environment

```bash
cp .env.local.example .env
```
Open `.env` and set these four lines for Ollama (everything else can stay):
```
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=gemma3:1b
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_MODEL=nomic-embed-text
```

## STEP 4 — Install dependencies

```bash
make setup        # creates backend venv + installs frontend deps
```

## STEP 5 — Bring up the stack (4 terminals)

Run each in its own terminal, from `aura-by-centro/`:
```bash
make qdrant       # T1: vector DB  (needs Docker running)
make backend      # T2: FastAPI    (http://localhost:8000)
make ingest       # T3: seed RAG with sample docs — run ONCE, then close
make smoke        # T3: health check — must print all PASS before you continue
make frontend     # T4: the UI     (http://localhost:3000)
```

`make smoke` must show:
```
PASS  LLM chat endpoint
PASS  Embeddings endpoint
PASS  Qdrant vector DB
All systems go. You're ready to demo.
```
If anything says FAIL, jump to **Troubleshooting** below.

Now open in your browser:
- **http://localhost:3000** — the chat
- **http://localhost:3000/admin** — knowledge-base dashboard
- **http://localhost:8000/docs** — backend API (proof the backend is real)

---

## STEP 6 — Test every feature yourself (your checklist)

Tick each one off. This is the same script you'll run for the CTO.

- [ ] **CAG cache (instant, no LLM).** In chat, click the suggestion
      *"How do I submit my resignation?"* → answer appears **instantly**. In the
      backend terminal you'll see a `cag_hit` log line. ✅ *This query never hit
      Gemma.*

- [ ] **RAG (grounded answers).** Ask *"What's the expense reimbursement limit?"*
      → it answers from the ingested HR handbook, streaming token-by-token.

- [ ] **Vector sandboxing (zero data leakage).** Open **/admin**, click
      **"Sign in as Coastline Manager"**. Then open
      `http://localhost:3000/embed?session=demo&token=PASTE_TOKEN` (copy the token
      from your browser's devtools → Application → Local Storage → `aura.token`,
      or from `POST /admin/dev-token` in http://localhost:8000/docs).
      - As **Coastline**: ask *"What is the overtime authorization rule for
        Coastline?"* → **answers**.
      - Mint a **Trueblue** or **global agent** token the same way and ask the
        same question → *"no documents in your access scope."* ✅ *Isolation is
        enforced inside the database.*

- [ ] **Action Cards (dual confirmation).** In chat ask
      *"Run the Odoo payroll sync for Trueblue."* → Aura does **not** execute; it
      shows a card with **Target System / API Payload / HIGH risk** + Confirm /
      Cancel. Click **Cancel** → "Action cancelled." ✅ *No write without consent.*

- [ ] **Dynamic schemas.** Open
      `documentation/schemas_registry/odoo_payroll.json` and note the card's
      payload/risk came from this file, not a prompt. Edit `risk_assessment`, save,
      restart backend, re-trigger the card → the text changes. ✅ *No code change.*

- [ ] **Self-service upload.** On **/admin** (as manager), upload any `.md`/`.txt`
      (Department=`hr`, Scope=`global`, Min role=`agent`). Then ask Aura a
      question answered by that file → it's retrieved live.

- [ ] **Graceful fallback.** Stop `ollama serve` (Ctrl-C in T-engine), ask a new
      question → instead of crashing you get a cached/enterprise fallback and the
      connection stays alive. Restart Ollama to resume. ✅ *Never goes dark.*

- [ ] **Embed (Zoho People).** Open `http://localhost:3000/embed?session=demo`
      → the chrome-less widget that drops into Zoho People as a Web Tab.

When all boxes are ticked, you've personally verified the full POC.

---

## Daily restart (after the first setup)

You don't repeat Steps 0–4. Just:
```bash
ollama serve          # T-engine
make qdrant           # T1
make backend          # T2
make smoke            # verify green
make frontend         # T4
```
(`make ingest` only needs re-running if you wiped the vector store.)

---

## Troubleshooting

| `make smoke` says… | Fix |
|---|---|
| FAIL LLM chat endpoint | Is `ollama serve` running? Is `LLM_MODEL` exactly `gemma3:1b` and pulled? |
| FAIL Embeddings endpoint | `ollama pull nomic-embed-text`; keep `EMBEDDING_DIM=768`. |
| FAIL Qdrant | Is Docker Desktop running and `make qdrant` up? |
| Chat connects, no answer | Did you run `make ingest`? Check the backend terminal for errors. |
| Admin upload → 403 | Sign in via /admin dev login (role must be ≥ manager). |
| Answers slow | Use `gemma3:1b` for the live demo; the first response after start is the slowest (model load). |
| Port already in use | Something else is on 8000/3000/6333 — stop it or change the port. |

> **Do a full dry run tonight**, exactly as you'll present. The first model load
> is slow; after that, responses are warm and snappy.

---

## Prefer Msty instead of Ollama?

Totally fine — Aura only needs an OpenAI-compatible endpoint. In Msty: confirm
the Local AI endpoint is running and **pull an embedding model** (e.g.
`nomic-embed-text`). Then in `.env` set `LLM_BASE_URL`/`EMBEDDING_BASE_URL` to the
Msty endpoint (often `http://localhost:10000/v1` — verify the port in Msty
settings) and `LLM_MODEL` to your `gemma3`/`gemma4`. Everything else is identical.

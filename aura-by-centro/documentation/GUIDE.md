# Aura (by Centro) — Run, Test & Deploy Guide

Everything you need to run Aura locally, test every feature, and deploy to AWS.
(Merges the former START_HERE / DEMO_GUIDE / SETUP_AND_DEPLOY docs.)

---

## 1. Run locally (Intel Mac, no Docker)

The vector store runs **embedded** by default — you only need Python, Node, and
Ollama. **One‑time setup:**

```bash
brew install python@3.11 node ollama git

# get the code
git clone https://github.com/Oudoo/Centro-AI-Approach.git
cd Centro-AI-Approach && git checkout claude/aura-centro-chatbot-SqC64
cd aura-by-centro

# install backend venv + frontend deps
make setup
```

Pull the models (CAG + RAG supply the facts, so a small model is fast on CPU):

```bash
OLLAMA_KEEP_ALIVE=-1 ollama serve     # keeps the model warm = much faster
ollama pull qwen2.5:1.5b              # chat model (qwen2.5:0.5b = fastest)
ollama pull nomic-embed-text          # embeddings for CAG + RAG (required)
```

**Run it — two terminals:**

```bash
OLLAMA_KEEP_ALIVE=-1 ollama serve     # terminal 1
make demo                             # terminal 2  (auto-creates .env, seeds docs, smoke-tests, starts UI)
```

Open:
- **http://localhost:3000** — chat
- **http://localhost:3000/admin** — knowledge base + employee requests
- **http://localhost:8000/docs** — API

> `make demo` requires **no Docker**. Docker is only used if you opt into a
> Qdrant *server* (`QDRANT_LOCAL=false`) — see §4.

Diagnostics if anything's off: `cd backend && source .venv/bin/activate &&
python -m scripts.diag_llm` (checks model + embeddings + streaming).

---

## 2. Test every feature (demo checklist)

- [ ] **CAG (instant, no LLM)** — "How do I submit my resignation?" → instant; backend logs `cag_hit`.
- [ ] **RAG (grounded)** — "What's the expense reimbursement limit?" → streams from the HR handbook.
- [ ] **Grounded-only (no hallucination)** — an out-of-scope question → "I couldn't find anything in your knowledge…".
- [ ] **Vector sandboxing** — sign in at `/admin` as **Coastline Manager**, copy `aura.token` (devtools → Local Storage), open `/embed?session=demo&token=PASTE`; ask the Coastline overtime question → answers. Repeat as **Trueblue Agent** → refused.
- [ ] **Requests** — "I want to request an annual leave" → fill the form → **Submit Request** → confirmation in chat → row appears in **/admin → Employee Requests** → **Export CSV (Excel)**.
- [ ] **Self-service upload** — `/admin` (manager) → upload a `.md` → ask about it.
- [ ] **Embed** — `/embed?session=demo` is the chrome-less widget for Zoho People.

Available request intents: **swap shift**, **annual leave**, **casual leave**,
**update break timing**.

---

## 3. Requests → email + Zoho + export

- Submitted requests are stored in SQLite (`backend/data/requests.db`) and
  exportable as CSV from the admin dashboard (opens in Excel).
- **Email** (demo phase): set SMTP in `.env` to actually send to
  `REQUEST_NOTIFY_EMAIL` (default `mahmoud.hassan@centrocdx.com`):
  ```
  SMTP_HOST=…  SMTP_PORT=587  SMTP_USER=…  SMTP_PASSWORD=…  SMTP_FROM=aura@centrocdx.com
  ```
  Leave `SMTP_HOST` blank → demo mode (recorded + logged, not sent).
- **Zoho People**: set `ZOHO_INTEGRATION_ENABLED=true` + point `ZOHO_MCP_URL` at a
  live Zoho People MCP server to file requests directly into Zoho. Off by default.

---

## 4. Embed inside Zoho People (Web Tab)

Deploy the frontend, then in **Zoho People → Settings → Customization → Web Tabs
→ Add Web Tab → External URL**:
```
https://aura.centro.example/embed?session=${EmployeeID}&token=${SignedJWT}
```
Issue the signed JWT (with `account_scope`, `role`, `department`) from your SSO so
the widget inherits the user's permissions. Set backend `ALLOWED_ORIGINS`
accordingly.

---

## 5. Deploy on AWS

| Piece | AWS service | Notes |
|------|-------------|-------|
| Gemma/Qwen inference | **EC2 GPU** (g5/g4dn) + **vLLM** | the one real cost; OpenAI-compatible |
| Backend (FastAPI) | **ECS Fargate** / App Runner | container from `backend/Dockerfile`; WebSocket via ALB |
| Frontend | **Amplify** / S3+CloudFront | Next.js |
| Vector DB | **Qdrant server on EC2/ECS** | set `QDRANT_LOCAL=false` + `QDRANT_URL` (Docker via `docker-compose.yml`) |
| Requests DB | **PostgreSQL on RDS** | swap the SQLite store (see ROADMAP item 6) |
| Secrets | **Secrets Manager / SSM** | JWT, SMTP, Zoho creds |

> Self-hosting = $0 software licensing. SQLite and Qdrant are free; the only
> recurring cost is GPU compute.

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `diag_llm`/smoke fails on LLM | `ollama serve` running? `LLM_MODEL` pulled? (`ollama list`) |
| fails on embeddings | `ollama pull nomic-embed-text`; keep `EMBEDDING_DIM=768` |
| chat answers but slowly | use `qwen2.5:0.5b`; run Ollama with `OLLAMA_KEEP_ALIVE=-1` |
| "An unexpected error" | the engine is down — start Ollama, restart backend |
| admin upload → 403 | sign in as a manager (dev login on `/admin`) |
| port in use (8000/3000) | stop the other process |

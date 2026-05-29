# Aura (by Centro) — Setup, Ingestion & Deployment

## 1. Run locally on an Intel MacBook with Msty Studio

Your machine isn't Apple Silicon, so we lean on Msty's CPU-friendly local server
and your already-installed models (`gemma3:1b`, `gemma4`).

```bash
# 0. Prereqs (Intel macOS): Python 3.11, Node 20, Docker Desktop
brew install python@3.11 node
# Docker Desktop: https://www.docker.com/products/docker-desktop/

# 1. In Msty Studio: Settings > Local AI — confirm the OpenAI-compatible
#    "Service Endpoint" is running, and pull an embedding model
#    (e.g. nomic-embed-text) so CAG + RAG can embed text.

# 2. Configure env (preconfigured for Msty)
cd aura-by-centro
cp .env.local.example .env
#   -> edit LLM_BASE_URL / EMBEDDING_BASE_URL to the exact Msty endpoint
#   -> LLM_MODEL=gemma3:1b is the light default; switch to gemma4 for quality

# 3. Vector DB
docker run -p 6333:6333 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant

# 4. Backend
cd backend && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# 5. Seed RAG with real answers (one-shot ingestion)
python -m scripts.ingest_docs --path ./sample_docs

# 6. Frontend (new terminal)
cd ../frontend && npm install && npm run dev
```

Open:
- **http://localhost:3000** — chat
- **http://localhost:3000/admin** — knowledge-base dashboard (dev sign-in)
- **http://localhost:8000/docs** — backend API (Swagger)

> Intel CPU note: `gemma4` (8B) runs but is slow on CPU. Use `gemma3:1b` for
> snappy testing; reserve `gemma4` for quality checks.

## 2. One-shot document ingestion

`scripts/ingest_docs.py` chunks → embeds → upserts with the mandatory sandbox
metadata. Scope/role can come from the filename or flags:

```bash
# Filename convention: <name>.<account_scope>.<min_role>.md
#   leave-policy.global.agent.md          -> everyone
#   coastline-shift-ops.coastline.team_lead.md -> Coastline TLs+ only
python -m scripts.ingest_docs --path ./sample_docs

# Or a whole folder with explicit metadata:
python -m scripts.ingest_docs --path ./hr_docs \
  --department hr --account-scope coastline --min-role agent
```

Ask Aura *"How do I submit my resignation?"* or *"What's the overtime rule for
Coastline?"* and you'll get grounded answers. A Trueblue user will **not** see
the Coastline doc — isolation is enforced in the vector index.

## 3. Dynamic uploads per department head (no code, no redeploy)

Department heads (role ≥ **manager**) manage knowledge from the **/admin**
dashboard:
- Upload `.md/.txt/.csv/.json`, set **Department**, **Account scope**, and
  **Min role required**.
- Each upload is chunked, embedded, and tagged so FEATURE 1 isolation applies
  automatically.
- List and delete documents; live chunk/doc counts.

Backend endpoints (all gated by `role >= manager`):
`POST /admin/documents`, `GET /admin/documents`, `DELETE /admin/documents/{id}`,
`GET /admin/stats`. Dev tokens: `POST /admin/dev-token` (disabled in production).

> Production: replace the dev sign-in with your SSO/JWT so a Coastline HR head
> can only ever publish into the Coastline scope.

## 4. Embed inside Zoho People (Web Tab)

There's a chrome-less widget route at **`/embed`** designed for an iframe.

1. Deploy the frontend (AWS Amplify / S3+CloudFront, or the desktop app).
2. In **Zoho People → Settings → Customization → Web Tabs → Add Web Tab**, choose
   **External URL** and point it at:
   ```
   https://aura.centro.example/embed?session=${EmployeeID}&token=${SignedJWT}
   ```
   Zoho merge fields populate the employee id; issue the signed JWT (carrying
   `account_scope`, `role`, `department`) from your SSO so the widget inherits
   the user's permissions.
3. To embed elsewhere (intranet/portal), use a plain iframe:
   ```html
   <iframe src="https://aura.centro.example/embed?session=USER&token=JWT"
           style="width:420px;height:680px;border:0;border-radius:16px"
           allow="clipboard-write"></iframe>
   ```

> Make sure the deployed origin is allowed: set `ALLOWED_ORIGINS` (backend CORS)
> and ensure your host permits framing by Zoho (CSP `frame-ancestors`).

## 5. Deploy on AWS

You have AWS, so self-host the whole stack — no per-seat SaaS fees:

| Piece | AWS service | Notes |
|------|-------------|-------|
| Gemma inference | **EC2 GPU** (g5 / g4dn) running **vLLM** | The one real cost. Autoscale by concurrency. |
| Backend (FastAPI) | **ECS Fargate** or **App Runner** | Container from `backend/Dockerfile`. WebSocket-friendly behind an ALB. |
| Frontend | **Amplify Hosting** or **S3 + CloudFront** | Static/SSR Next.js. |
| Vector DB | **Qdrant on EC2/ECS** + EBS volume | Self-hosted = free software. |
| Secrets | **AWS Secrets Manager / SSM** | JWT secret, Zoho/Odoo creds. |
| Desktop client | build installers, point `AURA_URL` at the ALB/CloudFront URL | see `desktop/`. |

## 6. "What is Qdrant Cloud for?"

Qdrant (the vector database) is **open-source and free to self-host** — that's
what `docker-compose`/AWS use. **Qdrant Cloud** is the company's *managed,
hosted* version: they run, scale, back up, and monitor the cluster for you for a
monthly fee. You **don't need it** — since you have AWS, self-host Qdrant and pay
nothing for the software. Consider Cloud only later if you want to offload ops.

"""
Aura (by Centro) — FastAPI application & WebSocket backbone.

Wires together the full request lifecycle:

    Client --(SocketMessage)--> /ws --> ConnectionManager --> ManagerAgent
        -> CAG cache (Feature 2)
        -> mutation Action Card + dual confirm (Feature 3)
        -> sandboxed RAG retrieval (Feature 1) + dynamic schemas (Feature 4)
        -> streamed Gemma-4 tokens with graceful fallback (Pattern 4)

Run locally:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from api_admin import router as admin_router
from auth import resolve_user, verify_action_signature
from config import Brand, get_settings
from core.agent import get_agent
from core.cache import get_semantic_cache
from core.sockets import manager
from core.vector_db import get_vector_sandbox
from integrations.schema_registry import get_schema_registry
from models import ClientActionResponse, ClientMessageType, ClientQuery

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
log = structlog.get_logger("aura.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm caches, vector collection, and the schema registry on boot."""
    log.info("aura_startup", brand=Brand.FULL_NAME)
    await get_schema_registry()
    try:
        await get_vector_sandbox()  # ensure collection + payload indexes
    except Exception as exc:  # vector engine may be offline in pure-frontend dev
        log.warning("vector_init_deferred", error=str(exc))
    try:
        await get_semantic_cache()  # pre-embed FAQ corpus
    except Exception as exc:
        log.warning("cache_warm_deferred", error=str(exc))
    yield
    log.info("aura_shutdown")


settings = get_settings()
app = FastAPI(
    title="Aura by Centro",
    description=Brand.TAGLINE,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin / document-management routes (department-head uploads).
app.include_router(admin_router)


# -----------------------------------------------------------------------------
# Health & metadata routers
# -----------------------------------------------------------------------------
@app.get("/")
async def root() -> dict:
    return {
        "name": Brand.FULL_NAME,
        "tagline": Brand.TAGLINE,
        "status": "online",
        "model": settings.llm_model,
        "context_window": settings.llm_context_window,
    }


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


# -----------------------------------------------------------------------------
# WebSocket backbone
# -----------------------------------------------------------------------------
@app.websocket("/ws")
async def chat_socket(websocket: WebSocket) -> None:
    # Resolve RBAC context once at connect-time from the auth token.
    token = websocket.query_params.get("token")
    user = resolve_user(token)
    session_id = websocket.query_params.get("session_id") or user.user_id
    conn = await manager.connect(session_id, websocket)
    agent = get_agent()
    log.info("ws_connect", session=session_id, scope=user.account_scope, role=user.role)

    try:
        while True:
            raw = await websocket.receive_json()
            msg_type = raw.get("type", ClientMessageType.QUERY.value)

            if msg_type == ClientMessageType.ACTION_RESPONSE.value:
                # FEATURE 3: only a signed, confirmed reply may unblock a write.
                try:
                    resp = ClientActionResponse.model_validate(raw)
                except ValidationError as exc:
                    await conn.error(f"Malformed action response: {exc.errors()}")
                    continue
                signature_ok = verify_action_signature(
                    session_id, resp.action_id, resp.signature
                )
                confirmed = resp.action_confirmed and signature_ok
                if not conn.resolve_action(resp.action_id, confirmed):
                    log.warning("stale_action_response", action_id=resp.action_id)
                continue

            # Default: a chat query.
            try:
                query = ClientQuery.model_validate(raw)
            except ValidationError as exc:
                await conn.error(f"Malformed query: {exc.errors()}")
                continue

            await agent.handle_query(conn, user, query.text)

    except WebSocketDisconnect:
        log.info("ws_disconnect", session=session_id)
    except Exception as exc:  # never let an unhandled error kill the worker
        log.error("ws_unhandled", session=session_id, error=str(exc))
        try:
            await conn.error("An unexpected error occurred. Your session is still open.")
        except Exception:
            pass
    finally:
        await manager.disconnect(session_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )

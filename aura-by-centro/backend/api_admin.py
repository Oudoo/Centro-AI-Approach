"""
Aura (by Centro) — Admin & document-management API.

Lets department heads (role >= manager) upload, list, and remove knowledge
documents. Every uploaded chunk is stamped with the mandatory sandbox metadata
(department, account_scope, min_role_required) so FEATURE 1 isolation holds for
anything ingested through the UI — exactly like the seed corpus.

Routes (mounted under /admin in main.py):
    POST   /admin/documents     multipart upload -> chunk -> embed -> upsert
    GET    /admin/documents     per-document listing for the dashboard
    DELETE /admin/documents/{doc_id}
    GET    /admin/stats
"""
from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from auth import mint_token, resolve_user
from config import ROLE_RANK, AccountScope, Role, get_settings
from core.chunking import chunk_text
from core.vector_db import get_vector_sandbox
from models import UserContext

log = structlog.get_logger("aura.admin")
router = APIRouter(prefix="/admin", tags=["admin"])

# Department heads and above may manage the knowledge base.
MIN_UPLOAD_RANK = ROLE_RANK[Role.MANAGER.value]
# Text formats we can ingest without extra parsers.
TEXT_SUFFIXES = (".md", ".markdown", ".txt", ".csv", ".json")


def require_manager(authorization: str | None = Header(default=None)) -> UserContext:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    user = resolve_user(token)
    if ROLE_RANK.get(user.role, 0) < MIN_UPLOAD_RANK:
        raise HTTPException(
            status_code=403,
            detail="Document management requires a department-head (manager) role or above.",
        )
    return user


@router.post("/dev-token")
async def dev_token(
    role: str = Form(Role.MANAGER.value),
    account_scope: str = Form(AccountScope.GLOBAL.value),
    department: str = Form("general"),
    name: str = Form("Centro Admin"),
) -> dict:
    """
    DEV ONLY: mint a signed token with chosen RBAC claims so you can exercise
    the admin dashboard and scoped chat locally. Disabled in production.
    """
    if get_settings().app_env == "production":
        raise HTTPException(404, "Not found.")
    if role not in ROLE_RANK:
        raise HTTPException(400, f"Invalid role '{role}'.")
    token = mint_token(
        user_id=f"dev-{role}", role=role, account_scope=account_scope,
        department=department, name=name,
    )
    return {"token": token, "role": role, "account_scope": account_scope}


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    department: str = Form(...),
    account_scope: str = Form(...),
    min_role_required: str = Form(Role.AGENT.value),
    user: UserContext = Depends(require_manager),
) -> dict:
    # Validate the RBAC metadata up front.
    if account_scope not in {s.value for s in AccountScope}:
        raise HTTPException(400, f"Invalid account_scope '{account_scope}'.")
    if min_role_required not in ROLE_RANK:
        raise HTTPException(400, f"Invalid min_role_required '{min_role_required}'.")

    name = file.filename or "upload"
    if not name.lower().endswith(TEXT_SUFFIXES):
        raise HTTPException(
            400,
            f"Unsupported file type. Allowed: {', '.join(TEXT_SUFFIXES)}.",
        )

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "File must be UTF-8 encoded text.")

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(400, "File appears to be empty.")

    doc_id = str(uuid.uuid4())
    metadata = {
        "doc_id": doc_id,
        "source": name,
        "department": department,
        "account_scope": account_scope,
        "min_role_required": min_role_required,
        "uploaded_by": user.display_name,
    }

    sandbox = await get_vector_sandbox()
    for chunk in chunks:
        await sandbox.ingest(chunk, metadata)

    log.info("doc_uploaded", doc_id=doc_id, source=name, chunks=len(chunks),
             scope=account_scope, by=user.user_id)
    return {"doc_id": doc_id, "source": name, "chunks": len(chunks), "metadata": metadata}


@router.get("/documents")
async def list_documents(user: UserContext = Depends(require_manager)) -> dict:
    sandbox = await get_vector_sandbox()
    return {"documents": await sandbox.list_documents()}


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str, user: UserContext = Depends(require_manager)
) -> dict:
    sandbox = await get_vector_sandbox()
    await sandbox.delete_document(doc_id)
    log.info("doc_deleted", doc_id=doc_id, by=user.user_id)
    return {"deleted": doc_id}


@router.get("/stats")
async def stats(user: UserContext = Depends(require_manager)) -> dict:
    sandbox = await get_vector_sandbox()
    return {
        "total_chunks": await sandbox.count(),
        "documents": len(await sandbox.list_documents()),
    }

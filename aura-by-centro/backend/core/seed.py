"""
Aura (by Centro) — Auto-seed the knowledge base on first run.

In embedded vector mode the DB is owned by the backend process, so we can't run
a separate ingestion process against it. Instead, on startup we seed the sample
documents directly if the collection is empty. Idempotent: does nothing once the
KB has content (or once a department head has uploaded their own docs).

Filename convention encodes scope/role:  <name>.<account_scope>.<min_role>.md
"""
from __future__ import annotations

from pathlib import Path

import structlog

from config import ROLE_RANK, AccountScope
from core.chunking import chunk_text
from core.vector_db import get_vector_sandbox

log = structlog.get_logger("aura.seed")

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_docs"
_SCOPES = {s.value for s in AccountScope}


def _metadata_for(path: Path) -> dict:
    account_scope, min_role = "global", "agent"
    parts = path.stem.split(".")
    if len(parts) >= 3 and parts[-1] in ROLE_RANK and parts[-2] in _SCOPES:
        account_scope, min_role = parts[-2], parts[-1]
    elif len(parts) >= 2 and parts[-1] in _SCOPES:
        account_scope = parts[-1]
    return {
        "department": "general",
        "account_scope": account_scope,
        "min_role_required": min_role,
        "source": path.name,
        "doc_id": path.stem,
    }


async def seed_if_empty() -> None:
    sandbox = await get_vector_sandbox()
    try:
        if await sandbox.count() > 0:
            return  # already has content
    except Exception:
        pass
    if not SAMPLE_DIR.exists():
        return
    files = [p for p in sorted(SAMPLE_DIR.glob("*")) if p.suffix.lower() in (".md", ".txt")]
    total = 0
    for path in files:
        meta = _metadata_for(path)
        for chunk in chunk_text(path.read_text(encoding="utf-8")):
            await sandbox.ingest(chunk, meta)
            total += 1
    if total:
        log.info("seeded_sample_docs", files=len(files), chunks=total)

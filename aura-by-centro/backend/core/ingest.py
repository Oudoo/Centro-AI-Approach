"""
Aura (by Centro) — Document ingestion helper (uses smart chunking).

One place that turns a raw file into sandboxed, parent-child vector points:
- Markdown -> header-aware sections; JSON -> object-coupled; else -> paragraphs.
- Each child text is embedded; the parent section is stored for retrieval.
- (a) GLOBAL markdown sections are auto-promoted into the CAG cache
  (heading -> section body) so common global FAQs answer instantly, no LLM.
"""
from __future__ import annotations

import structlog

from config import get_settings
from core.cache import get_semantic_cache
from core.chunking import smart_chunks
from core.vector_db import get_vector_sandbox

log = structlog.get_logger("aura.ingest")


async def ingest_document(filename: str, text: str, metadata: dict) -> int:
    """Chunk + embed + upsert a document. Returns the number of chunks stored."""
    sandbox = await get_vector_sandbox()
    chunks = smart_chunks(filename, text)
    for ch in chunks:
        meta = {
            **metadata,
            "parent_text": ch.get("parent_text", ch["text"]),
            "section": ch.get("section", ""),
        }
        await sandbox.ingest(ch["text"], meta)

    s = get_settings()
    if (
        s.cag_auto_promote_global
        and metadata.get("account_scope") == "global"
        and filename.lower().endswith((".md", ".markdown"))
    ):
        cache = await get_semantic_cache()
        seen: set[str] = set()
        promoted = 0
        for ch in chunks:
            heading = (ch.get("section") or "").strip()
            parent = ch.get("parent_text", "")
            if heading and parent and heading not in seen:
                seen.add(heading)
                try:
                    await cache.add(heading, parent, "global")
                    promoted += 1
                except Exception as exc:
                    log.warning("cag_promote_failed", section=heading, error=str(exc))
        if promoted:
            log.info("cag_auto_promoted", sections=promoted, source=metadata.get("source"))

    return len(chunks)

"""
Aura (by Centro) — Lightweight text chunking for RAG ingestion.

Paragraph-aware splitter with overlap so retrieved chunks keep enough context
to ground an answer. Dependency-free; good enough for handbooks, policies, and
markdown/plain-text documents.
"""
from __future__ import annotations


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    # Split on blank lines first to respect natural paragraph boundaries.
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer = ""

    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= max_chars:
            buffer = f"{buffer}\n\n{para}".strip()
            continue
        if buffer:
            chunks.append(buffer)
        # A single oversized paragraph is hard-split with overlap.
        if len(para) > max_chars:
            start = 0
            while start < len(para):
                chunks.append(para[start : start + max_chars])
                start += max_chars - overlap
            buffer = ""
        else:
            buffer = para

    if buffer:
        chunks.append(buffer)
    return chunks

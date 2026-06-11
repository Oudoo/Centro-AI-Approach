"""
Aura (by Centro) — Reranking (Pillar 3: Post-Retrieval Layer).

Re-orders hybrid-search candidates so only the most relevant chunks reach the
LLM (less context noise => fewer hallucinations). Default is a fast, dependency-
free lexical reranker. An optional cross-encoder (e.g. BAAI/bge-reranker-v2-m3
via fastembed) is used when CROSS_ENCODER_ENABLED=true and fastembed is
installed — otherwise we degrade gracefully to lexical.
"""
from __future__ import annotations

import re

import structlog

from config import get_settings
from models import RetrievedChunk

log = structlog.get_logger("aura.rerank")
_TOKEN = re.compile(r"[a-z0-9]+")
_ce = None  # cached cross-encoder


def _tok(s: str) -> set[str]:
    return set(_TOKEN.findall((s or "").lower()))


def _lexical_score(q_tokens: set[str], chunk: RetrievedChunk) -> float:
    if not q_tokens:
        return 0.0
    doc = _tok(chunk.context)
    if not doc:
        return 0.0
    overlap = len(q_tokens & doc)
    return overlap / len(q_tokens)  # containment of the query in the chunk


def _maybe_cross_encoder():
    global _ce
    if _ce is not None:
        return _ce
    s = get_settings()
    if not s.cross_encoder_enabled:
        return None
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _ce = TextCrossEncoder(model_name=s.cross_encoder_model)
        log.info("cross_encoder_loaded", model=s.cross_encoder_model)
        return _ce
    except Exception as exc:  # not installed / failed -> lexical fallback
        log.warning("cross_encoder_unavailable", error=str(exc))
        return None


def rerank(query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Return chunks ordered best-first, with `score` set to the rerank score."""
    if not chunks:
        return []
    ce = _maybe_cross_encoder()
    if ce is not None:
        try:
            scores = list(ce.rerank(query, [c.context for c in chunks]))
            for c, sc in zip(chunks, scores):
                c.score = float(sc)
            return sorted(chunks, key=lambda c: c.score, reverse=True)
        except Exception as exc:
            log.warning("cross_encoder_failed", error=str(exc))
    # Lexical fallback
    q = _tok(query)
    for c in chunks:
        c.score = _lexical_score(q, c)
    return sorted(chunks, key=lambda c: c.score, reverse=True)

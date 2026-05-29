"""
Aura (by Centro) — Hybrid retrieval (Pillar 2: Retrieval Layer).

Fuses Dense vector search (semantic, via Qdrant) with Sparse BM25 keyword search
(exact matches like "Error 403" or "Agent ID TX-99") using Reciprocal Rank
Fusion, then reranks (Pillar 3). RBAC is enforced at the Qdrant layer on BOTH
paths: the BM25 index is built only from the user's scope-visible chunks.

Pure-Python BM25 (no extra dependency) keeps `make setup` light.
"""
from __future__ import annotations

import math
import re

from config import get_settings
from core.rerank import rerank
from core.vector_db import get_vector_sandbox
from models import RetrievedChunk, UserContext

_TOKEN = re.compile(r"[a-z0-9]+")


def _tok(s: str) -> list[str]:
    return _TOKEN.findall((s or "").lower())


class _BM25:
    """Minimal BM25 Okapi over an in-memory corpus."""

    def __init__(self, corpus_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = corpus_tokens
        self.n = len(corpus_tokens)
        self.avgdl = (sum(len(d) for d in corpus_tokens) / self.n) if self.n else 0.0
        self.df: dict[str, int] = {}
        for d in corpus_tokens:
            for t in set(d):
                self.df[t] = self.df.get(t, 0) + 1
        self.idf = {
            t: math.log(1 + (self.n - f + 0.5) / (f + 0.5)) for t, f in self.df.items()
        }

    def scores(self, query_tokens: list[str]) -> list[float]:
        out: list[float] = []
        for d in self.docs:
            if not d:
                out.append(0.0)
                continue
            freq: dict[str, int] = {}
            for t in d:
                freq[t] = freq.get(t, 0) + 1
            dl = len(d)
            s = 0.0
            for t in query_tokens:
                if t not in freq:
                    continue
                idf = self.idf.get(t, 0.0)
                tf = freq[t]
                s += idf * (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
                )
            out.append(s)
        return out


def _key(c: RetrievedChunk) -> str:
    return f"{c.doc_id}|{(c.parent_text or c.text)[:80]}"


def _rrf_fuse(ranked_lists: list[list[RetrievedChunk]], k: int = 60) -> list[RetrievedChunk]:
    """Reciprocal Rank Fusion across multiple ranked candidate lists."""
    scores: dict[str, float] = {}
    chunks: dict[str, RetrievedChunk] = {}
    for lst in ranked_lists:
        for rank, c in enumerate(lst):
            key = _key(c)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            chunks.setdefault(key, c)
    order = sorted(scores, key=lambda kk: scores[kk], reverse=True)
    return [chunks[kk] for kk in order]


def _dedupe_parents(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Keep one chunk per parent section so we don't send duplicate context."""
    seen: set[str] = set()
    out: list[RetrievedChunk] = []
    for c in chunks:
        key = f"{c.doc_id}|{c.parent_text[:60]}"
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


async def hybrid_search(query: str, user: UserContext) -> list[RetrievedChunk]:
    """Dense + BM25 (RRF) -> rerank -> top-k distinct parent sections."""
    s = get_settings()
    sandbox = await get_vector_sandbox()
    pool = s.rag_candidates

    dense = await sandbox.search(query, user=user, limit=pool)

    if s.hybrid_search_enabled:
        corpus = await sandbox.scope_chunks(user)
        if corpus:
            bm25 = _BM25([_tok(c.text) for c in corpus])
            scored = sorted(
                zip(corpus, bm25.scores(_tok(query))),
                key=lambda x: x[1],
                reverse=True,
            )
            sparse = [c for c, sc in scored[:pool] if sc > 0]
        else:
            sparse = []
        fused = _rrf_fuse([dense, sparse]) if sparse else dense
    else:
        fused = dense

    if s.rerank_enabled:
        fused = rerank(query, fused)

    return _dedupe_parents(fused)[: s.rag_top_k]

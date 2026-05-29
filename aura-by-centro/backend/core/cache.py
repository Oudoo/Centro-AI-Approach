"""
Aura (by Centro) — FEATURE 2: Semantic Cache-Augmented Generation (CAG).

An async, in-memory semantic cache of pre-embedded GLOBAL FAQ answers (HR
handbook, holiday calendar, resignation flow, ...). On every inbound message we
embed the query and compare (cosine) against the cache. If the top match scores
>= CAG_SIMILARITY_THRESHOLD (default 0.92) we return the cached answer and the
Gemma-4 inference pipeline is bypassed entirely.
"""
from __future__ import annotations

import asyncio

import numpy as np

from config import get_settings
from core.embeddings import get_embedding_client

# Seed FAQ knowledge — global, role-agnostic answers safe for every tenant.
SEED_FAQS: list[dict[str, str]] = [
    {
        "question": "How do I submit my resignation?",
        "answer": (
            "To submit your resignation, open Zoho People > Self Service > "
            "Separation, fill in your notice period and last working day, and "
            "submit. Your reporting manager and HR are notified automatically. "
            "Standard notice is 30 days unless your contract states otherwise."
        ),
    },
    {
        "question": "What is the holiday calendar / list of public holidays?",
        "answer": (
            "The official Centro holiday calendar lives in Zoho People > "
            "Leave Tracker > Holidays. Holidays are localized per account and "
            "region; check the filter at the top of the page for your location."
        ),
    },
    {
        "question": "How many annual leave days do I get and how do I apply?",
        "answer": (
            "Apply for leave in Zoho People > Leave Tracker > Apply Leave. "
            "Annual entitlement depends on your contract and tenure; your "
            "current balance is shown on the same screen before you submit."
        ),
    },
    {
        "question": "How do I reset my password or get IT support?",
        "answer": (
            "For password resets and IT support, raise a ticket in the Centro "
            "Service Desk or contact the IT helpdesk. Most password resets are "
            "self-service via the SSO portal's 'Forgot password' link."
        ),
    },
]


class _Entry:
    __slots__ = ("vector", "answer", "question")

    def __init__(self, vector: np.ndarray, answer: str, question: str) -> None:
        self.vector = vector
        self.answer = answer
        self.question = question


class SemanticCache:
    def __init__(self) -> None:
        s = get_settings()
        self._threshold = s.cag_similarity_threshold
        self._max = s.cag_max_entries
        self._entries: list[_Entry] = []
        self._matrix: np.ndarray | None = None  # normalized stacked vectors
        self._lock = asyncio.Lock()
        self._ready = False

    @staticmethod
    def _normalize(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        return v / norm if norm else v

    async def warm(self) -> None:
        """Pre-embed the seed FAQ corpus at startup."""
        if self._ready:
            return
        embedder = await get_embedding_client()
        async with self._lock:
            if self._ready:
                return
            vectors = await embedder.embed_batch([f["question"] for f in SEED_FAQS])
            for faq, vec in zip(SEED_FAQS, vectors):
                self._entries.append(
                    _Entry(self._normalize(np.asarray(vec, dtype=np.float32)),
                           faq["answer"], faq["question"])
                )
            self._rebuild_matrix()
            self._ready = True

    def _rebuild_matrix(self) -> None:
        self._matrix = (
            np.vstack([e.vector for e in self._entries]) if self._entries else None
        )

    async def add(self, question: str, answer: str) -> None:
        """Promote a fresh LLM answer into the cache for future fast-paths."""
        embedder = await get_embedding_client()
        vec = self._normalize(
            np.asarray(await embedder.embed(question), dtype=np.float32)
        )
        async with self._lock:
            self._entries.append(_Entry(vec, answer, question))
            if len(self._entries) > self._max:
                self._entries.pop(0)  # simple FIFO eviction
            self._rebuild_matrix()

    async def lookup(self, query: str) -> tuple[str, float] | None:
        """
        Return (answer, score) when the best cosine match clears the threshold,
        else None so the caller proceeds to the RAG/LLM pipeline.
        """
        if self._matrix is None:
            return None
        embedder = await get_embedding_client()
        q = self._normalize(np.asarray(await embedder.embed(query), dtype=np.float32))
        # Vectors are normalized -> dot product == cosine similarity.
        scores = self._matrix @ q
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])
        if best_score >= self._threshold:
            return self._entries[best_idx].answer, best_score
        return None


_cache: SemanticCache | None = None


async def get_semantic_cache() -> SemanticCache:
    global _cache
    if _cache is None:
        _cache = SemanticCache()
        await _cache.warm()
    return _cache

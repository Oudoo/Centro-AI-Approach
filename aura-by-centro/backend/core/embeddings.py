"""
Aura (by Centro) — Async embedding client (OpenAI-compatible).

Shared by the RAG ingestion path, the vector retriever, and the CAG cache so
that every component embeds queries with the exact same model + dimensionality.
"""
from __future__ import annotations

import asyncio

import httpx

from config import get_settings


class EmbeddingClient:
    def __init__(self) -> None:
        s = get_settings()
        self._url = f"{s.embedding_base_url.rstrip('/')}/embeddings"
        self._model = s.embedding_model
        self._headers = {"Authorization": f"Bearer {s.llm_api_key}"}
        self._client = httpx.AsyncClient(timeout=30.0)

    async def embed(self, text: str) -> list[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.post(
            self._url,
            headers=self._headers,
            json={"model": self._model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        # Preserve request ordering.
        return [item["embedding"] for item in sorted(data, key=lambda d: d["index"])]

    async def aclose(self) -> None:
        await self._client.aclose()


_client: EmbeddingClient | None = None
_lock = asyncio.Lock()


async def get_embedding_client() -> EmbeddingClient:
    global _client
    async with _lock:
        if _client is None:
            _client = EmbeddingClient()
    return _client

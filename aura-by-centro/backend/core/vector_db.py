"""
Aura (by Centro) — FEATURE 1: Metadata-Enforced Vector Sandboxing.

Zero data leakage is guaranteed at the *index layer*: the authenticated user's
RBAC scope is compiled into a hard Boolean metadata filter that is handed to the
vector engine itself. We NEVER fetch broadly and post-filter in Python memory.

Every ingested chunk carries mandatory metadata:
    - department
    - account_scope   (coastline | trueblue | global)
    - min_role_required
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from qdrant_client import AsyncQdrantClient, models as qm

from config import ROLE_RANK, get_settings, scopes_visible_to
from core.embeddings import get_embedding_client
from models import RetrievedChunk, UserContext

MANDATORY_METADATA = ("department", "account_scope", "min_role_required")


class VectorSandbox:
    """Async wrapper around Qdrant that enforces tenant isolation on every query."""

    def __init__(self) -> None:
        s = get_settings()
        self._collection = s.vector_collection
        self._dim = s.embedding_dim
        if s.qdrant_local:
            # Embedded, on-disk Qdrant — no Docker, no server. One process only.
            Path(s.qdrant_path).mkdir(parents=True, exist_ok=True)
            self._client = AsyncQdrantClient(path=s.qdrant_path)
        else:
            self._client = AsyncQdrantClient(
                url=s.qdrant_url, api_key=s.qdrant_api_key or None
            )

    async def ensure_collection(self) -> None:
        existing = {c.name for c in (await self._client.get_collections()).collections}
        if self._collection not in existing:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qm.VectorParams(
                    size=self._dim, distance=qm.Distance.COSINE
                ),
            )
        # Payload indexes make the metadata filter cheap and enforceable.
        for field in (*MANDATORY_METADATA, "doc_id"):
            try:
                await self._client.create_payload_index(
                    collection_name=self._collection,
                    field_name=field,
                    field_schema=qm.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass  # index already exists

    # -- Ingestion -----------------------------------------------------------
    async def ingest(self, text: str, metadata: dict[str, Any]) -> str:
        missing = [k for k in MANDATORY_METADATA if not metadata.get(k)]
        if missing:
            raise ValueError(
                f"Refusing ingest: missing mandatory sandbox metadata {missing}"
            )
        embedder = await get_embedding_client()
        vector = await embedder.embed(text)
        point_id = str(uuid.uuid4())
        await self._client.upsert(
            collection_name=self._collection,
            points=[
                qm.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"text": text, **metadata},
                )
            ],
        )
        return point_id

    # -- Retrieval (sandboxed) ----------------------------------------------
    def _build_filter(self, user: UserContext) -> qm.Filter:
        """
        Compile the RBAC scope into a HARD Boolean filter applied *during*
        retrieval. A Coastline agent can only ever match documents whose
        account_scope is in {coastline, global}.
        """
        visible_scopes = scopes_visible_to(user.account_scope)
        user_rank = ROLE_RANK.get(user.role, 0)
        allowed_roles = [r for r, rank in ROLE_RANK.items() if rank <= user_rank]

        return qm.Filter(
            must=[
                qm.FieldCondition(
                    key="account_scope",
                    match=qm.MatchAny(any=visible_scopes),
                ),
                qm.FieldCondition(
                    key="min_role_required",
                    match=qm.MatchAny(any=allowed_roles),
                ),
            ]
        )

    async def search(
        self, query: str, user: UserContext, limit: int = 6
    ) -> list[RetrievedChunk]:
        embedder = await get_embedding_client()
        vector = await embedder.embed(query)
        hits = await self._client.query_points(
            collection_name=self._collection,
            query=vector,
            query_filter=self._build_filter(user),  # enforced at the index layer
            limit=limit,
            with_payload=True,
        )
        results: list[RetrievedChunk] = []
        for h in hits.points:
            p = h.payload or {}
            results.append(
                RetrievedChunk(
                    text=p.get("text", ""),
                    score=h.score,
                    department=p.get("department", ""),
                    account_scope=p.get("account_scope", ""),
                    min_role_required=p.get("min_role_required", ""),
                    source=p.get("source", ""),
                )
            )
        return results

    # -- Admin / document management ----------------------------------------
    async def count(self) -> int:
        result = await self._client.count(self._collection, exact=True)
        return result.count

    async def list_documents(self, limit: int = 1000) -> list[dict[str, Any]]:
        """
        Aggregate stored chunks into a per-document view (grouped by doc_id).
        Suitable for the admin dashboard; scale-bounded by `limit`.
        """
        points, _ = await self._client.scroll(
            collection_name=self._collection,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        docs: dict[str, dict[str, Any]] = {}
        for pt in points:
            p = pt.payload or {}
            doc_id = p.get("doc_id", str(pt.id))
            entry = docs.setdefault(
                doc_id,
                {
                    "doc_id": doc_id,
                    "source": p.get("source", "untitled"),
                    "department": p.get("department", ""),
                    "account_scope": p.get("account_scope", ""),
                    "min_role_required": p.get("min_role_required", ""),
                    "uploaded_by": p.get("uploaded_by", ""),
                    "chunks": 0,
                },
            )
            entry["chunks"] += 1
        return sorted(docs.values(), key=lambda d: d["source"])

    async def delete_document(self, doc_id: str) -> None:
        """Remove every chunk belonging to a document."""
        await self._client.delete(
            collection_name=self._collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="doc_id", match=qm.MatchValue(value=doc_id)
                        )
                    ]
                )
            ),
        )

    async def aclose(self) -> None:
        await self._client.close()


_sandbox: VectorSandbox | None = None


async def get_vector_sandbox() -> VectorSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = VectorSandbox()
        await _sandbox.ensure_collection()
    return _sandbox

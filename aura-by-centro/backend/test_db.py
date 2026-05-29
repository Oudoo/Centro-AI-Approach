import asyncio
import json
from config import get_settings
from qdrant_client import AsyncQdrantClient

async def main():
    s = get_settings()
    client = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
    points, _ = await client.scroll(
        collection_name=s.vector_collection,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )
    docs = {}
    for pt in points:
        p = pt.payload or {}
        doc_id = p.get("doc_id", str(pt.id))
        if doc_id not in docs:
            docs[doc_id] = {
                "source": p.get("source"),
                "account_scope": p.get("account_scope")
            }
    print(json.dumps(docs, indent=2))
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())

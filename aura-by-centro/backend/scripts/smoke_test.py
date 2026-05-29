"""
Aura (by Centro) — Pre-demo smoke test.

Run this 5 minutes before any demo. It verifies every external dependency is
reachable and prints a clear PASS/FAIL per check so you never get surprised in
front of an audience.

    python -m scripts.smoke_test
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from config import get_settings  # noqa: E402

GREEN = "\033[92m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"


def ok(label: str, detail: str = "") -> None:
    print(f"  {GREEN}PASS{RESET}  {label} {DIM}{detail}{RESET}")


def fail(label: str, detail: str = "") -> None:
    print(f"  {RED}FAIL{RESET}  {label} {DIM}{detail}{RESET}")


async def check_llm(s) -> bool:
    url = f"{s.llm_base_url.rstrip('/')}/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                url,
                headers={"Authorization": f"Bearer {s.llm_api_key}"},
                json={
                    "model": s.llm_model,
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 5,
                },
            )
        if r.status_code == 200:
            ok("LLM chat endpoint", f"{s.llm_model} @ {s.llm_base_url}")
            return True
        fail("LLM chat endpoint", f"HTTP {r.status_code} @ {url}")
    except Exception as e:
        fail("LLM chat endpoint", f"{type(e).__name__}: {e}")
    return False


async def check_embeddings(s) -> bool:
    url = f"{s.embedding_base_url.rstrip('/')}/embeddings"
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                url,
                headers={"Authorization": f"Bearer {s.llm_api_key}"},
                json={"model": s.embedding_model, "input": ["hello"]},
            )
        if r.status_code == 200:
            dim = len(r.json()["data"][0]["embedding"])
            note = f"{s.embedding_model}, dim={dim}"
            if dim != s.embedding_dim:
                fail("Embeddings endpoint", f"dim {dim} != EMBEDDING_DIM {s.embedding_dim}")
                return False
            ok("Embeddings endpoint", note)
            return True
        fail("Embeddings endpoint", f"HTTP {r.status_code} @ {url}")
    except Exception as e:
        fail("Embeddings endpoint", f"{type(e).__name__}: {e}")
    return False


async def check_qdrant(s) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{s.qdrant_url.rstrip('/')}/collections")
        if r.status_code == 200:
            ok("Qdrant vector DB", s.qdrant_url)
            return True
        fail("Qdrant vector DB", f"HTTP {r.status_code}")
    except Exception as e:
        fail("Qdrant vector DB", f"{type(e).__name__}: {e}")
    return False


async def main() -> None:
    s = get_settings()
    print(f"\nAura (by Centro) — smoke test [{s.app_env}]\n")
    results = await asyncio.gather(
        check_llm(s), check_embeddings(s), check_qdrant(s)
    )
    print()
    if all(results):
        print(f"{GREEN}All systems go. You're ready to demo.{RESET}\n")
        sys.exit(0)
    print(f"{RED}One or more checks failed — fix before demoing (see DEMO_GUIDE.md).{RESET}\n")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

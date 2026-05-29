"""
Aura (by Centro) — LLM/Embeddings diagnostic.

Hits your configured endpoints EXACTLY like the app does and prints the raw
results, so a failing chat is never a mystery. Run it whenever "the bot won't
answer":

    cd backend && source .venv/bin/activate && python -m scripts.diag_llm
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from config import get_settings  # noqa: E402

G, R, Y, D, X = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"


async def main() -> None:
    s = get_settings()
    print(f"\n{Y}Aura LLM diagnostic{X}")
    print(f"{D}  LLM_BASE_URL      = {s.llm_base_url}{X}")
    print(f"{D}  LLM_MODEL         = {s.llm_model}{X}")
    print(f"{D}  EMBEDDING_BASE_URL= {s.embedding_base_url}{X}")
    print(f"{D}  EMBEDDING_MODEL   = {s.embedding_model}{X}")
    print(f"{D}  EMBEDDING_DIM     = {s.embedding_dim}{X}\n")

    headers = {"Authorization": f"Bearer {s.llm_api_key}"}

    # 1) List models the server actually has
    async with httpx.AsyncClient(timeout=15) as c:
        try:
            r = await c.get(f"{s.llm_base_url.rstrip('/')}/models", headers=headers)
            ids = [m.get("id") for m in r.json().get("data", [])]
            print(f"{G}Models available:{X} {ids}")
            if s.llm_model not in ids:
                print(f"{R}  ⚠ Your LLM_MODEL '{s.llm_model}' is NOT in that list. "
                      f"Set LLM_MODEL to one of the above.{X}")
        except Exception as e:
            print(f"{R}Could not list models: {e}{X}")
            print(f"{R}→ Is your engine (Ollama) running at {s.llm_base_url}?{X}")
            return

    # 2) Embeddings
    async with httpx.AsyncClient(timeout=30) as c:
        try:
            r = await c.post(
                f"{s.embedding_base_url.rstrip('/')}/embeddings",
                headers=headers,
                json={"model": s.embedding_model, "input": ["hello"]},
            )
            r.raise_for_status()
            dim = len(r.json()["data"][0]["embedding"])
            tag = G if dim == s.embedding_dim else R
            print(f"{tag}Embeddings OK — dim={dim} (expected {s.embedding_dim}){X}")
        except Exception as e:
            print(f"{R}Embeddings FAILED: {e}{X}")

    # 3) Streaming chat (the actual chat path)
    print(f"\n{Y}Streaming a test completion…{X}")
    payload = {
        "model": s.llm_model,
        "messages": [{"role": "user", "content": "Reply with one short sentence."}],
        "stream": True,
        "max_tokens": 64,
    }
    tokens = 0
    text = ""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=15, read=300, write=30, pool=15)) as c:
            async with c.stream("POST", f"{s.llm_base_url.rstrip('/')}/chat/completions",
                                 headers=headers, json=payload) as resp:
                print(f"{D}  HTTP {resp.status_code}{X}")
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content", "")
                        if delta:
                            tokens += 1
                            text += delta
                    except Exception:
                        pass
        if tokens:
            print(f"{G}Chat OK — streamed {tokens} tokens:{X} {text!r}\n")
            print(f"{G}✅ Your LLM is answering. The app should work.{X}\n")
        else:
            print(f"{R}Chat returned 0 tokens. The model accepted the request but "
                  f"produced nothing — try a different/smaller model.{X}\n")
    except Exception as e:
        print(f"{R}Chat FAILED: {type(e).__name__}: {e}{X}\n")


if __name__ == "__main__":
    asyncio.run(main())

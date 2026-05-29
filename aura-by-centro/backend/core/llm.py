"""
Aura (by Centro) — Async Gemma-3 client over an OpenAI-compatible endpoint.

Exposes a streaming token generator. Raises `LLMUnavailable` on OOM / latency /
connection failures so the orchestrator can trigger graceful fallback
(CODE PATTERN #4) without dropping the WebSocket.
"""
from __future__ import annotations

from typing import AsyncIterator

import httpx

from config import get_settings


class LLMUnavailable(RuntimeError):
    """Raised on OOM, timeout, or transport failure from the local cluster."""


class GemmaClient:
    def __init__(self) -> None:
        s = get_settings()
        self._url = f"{s.llm_base_url.rstrip('/')}/chat/completions"
        self._model = s.llm_model
        self._headers = {"Authorization": f"Bearer {s.llm_api_key}"}
        self._timeout = s.llm_request_timeout
        self._temperature = s.llm_temperature
        self._max_tokens = s.llm_max_output_tokens
        # Granular timeouts: fail fast if the server is unreachable (connect),
        # but allow a slow local CPU plenty of time to produce/stream tokens
        # (read) so we don't raise a false "heavy load" on a 2019 Intel Mac.
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=15.0, read=max(self._timeout, 300.0), write=60.0, pool=15.0
            )
        )

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": True,
        }
        try:
            async with self._client.stream(
                "POST", self._url, headers=self._headers, json=payload
            ) as resp:
                if resp.status_code >= 500:
                    # 500/503 from local inference servers usually == OOM/overload.
                    raise LLMUnavailable(f"Gemma-3 cluster error {resp.status_code}")
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    token = _extract_token(data)
                    if token:
                        yield token
        except httpx.TimeoutException as exc:
            raise LLMUnavailable(f"Gemma-3 latency/timeout: {exc}") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailable(f"Gemma-3 transport failure: {exc}") from exc

    async def generate(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": 15,
            "stream": False,
        }
        try:
            resp = await self._client.post(self._url, headers=self._headers, json=payload)
            if resp.status_code >= 500:
                raise LLMUnavailable(f"Gemma-3 cluster error {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"].get("content", "").strip()
        except Exception as exc:
            raise LLMUnavailable(f"Gemma-3 generation failure: {exc}") from exc

    async def aclose(self) -> None:
        await self._client.aclose()


def _extract_token(data: str) -> str:
    import json

    try:
        delta = json.loads(data)["choices"][0]["delta"]
        return delta.get("content", "") or ""
    except (KeyError, IndexError, ValueError):
        return ""


_llm: GemmaClient | None = None


def get_llm() -> GemmaClient:
    global _llm
    if _llm is None:
        _llm = GemmaClient()
    return _llm

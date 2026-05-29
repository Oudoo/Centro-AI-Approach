"""
Aura (by Centro) — Central Manager Agent & orchestration.

Pipeline for every inbound query (see main.py wiring):

    1. CAG fast-path  (FEATURE 2) — semantic cache hit >= 0.92 bypasses the LLM.
    2. Intent routing (FEATURE 3) — mutation intents emit an Action Card and
       block on dual confirmation before any write executes.
    3. Dynamic schema retrieval (FEATURE 4) — integration contracts are pulled
       from the technical vector space, never hard-coded into prompts.
    4. RAG answer    (FEATURE 1) — sandboxed retrieval + streamed Gemma-3 answer
       with graceful fallback (PATTERN #4) on OOM/latency.
"""
from __future__ import annotations

import uuid

import structlog

from config import MUTATION_INTENTS, get_settings
from core.cache import get_semantic_cache
from core.llm import LLMUnavailable, get_llm
from core.sockets import Connection
from core.vector_db import get_vector_sandbox
from integrations.mcp_bridge import MCPError, get_mcp_bridge
from integrations.schema_registry import get_schema_registry
from models import ActionCardData, RiskLevel, UserContext

log = structlog.get_logger("aura.agent")

SYSTEM_PROMPT = (
    "You are Aura, the enterprise AI co-pilot by Centro. "
    "Your voice is friendly, helpful, and professional. You act as a supportive "
    "buddy who makes the workday easier. Answer concisely and ground every statement in "
    "the provided CONTEXT. If the context is insufficient, say so plainly rather "
    "than inventing details."
)

FALLBACK_MESSAGE = (
    "Aura is experiencing heavy load on the local model cluster right now. "
    "I've logged the issue and your session is still active — please retry your "
    "request in a moment, or rephrase it so I can serve it from cached knowledge."
)


class ManagerAgent:
    """Stateless orchestrator; per-request state lives on the Connection."""

    def __init__(self) -> None:
        self._settings = get_settings()

    # ---- Intent routing (lightweight, deterministic) ----------------------
    def detect_intent(self, text: str) -> str | None:
        """
        Map a query to a known mutation intent. Kept rule-based for determinism
        and auditability; swap for an LLM classifier later if needed.
        """
        t = text.lower()
        if "swap" in t and "shift" in t:
            return "swap_shift"
        if "leave" in t:
            if "annual" in t:
                return "annual_leave_request"
            if "casual" in t:
                return "casual_leave_request"
        if "break" in t and ("timing" in t or "update" in t):
            return "update_break_timing"
        return None

    # ---- Main entrypoint ---------------------------------------------------
    async def handle_query(self, conn: Connection, user: UserContext, text: str) -> None:
        # 1) CAG fast-path -------------------------------------------------
        cache = await get_semantic_cache()
        hit = await cache.lookup(text, user.account_scope)
        if hit is not None:
            answer, score = hit
            log.info("cag_hit", session=conn.session_id, score=round(score, 4))
            await conn.stream_token(answer)
            await conn.complete()
            return

        # 2) Mutation intent -> dual-confirmation Action Card --------------
        intent = self.detect_intent(text)
        if intent in MUTATION_INTENTS:
            await self._handle_mutation(conn, user, intent, text)
            return

        # 4) RAG answer (default path) -------------------------------------
        await self._handle_rag(conn, user, text)

    # ---- FEATURE 3: dual confirmation -------------------------------------
    async def _handle_mutation(
        self, conn: Connection, user: UserContext, intent: str, text: str
    ) -> None:
        registry = await get_schema_registry()
        # FEATURE 4: pull the live contract instead of hard-coding it.
        contract = await registry.resolve(intent, user)
        card = ActionCardData(
            action_id=str(uuid.uuid4()),
            intent=intent,
            target_system=contract.get("target_system", intent),
            summary=contract.get("summary", f"Execute '{intent}' as requested."),
            api_payload=contract.get("example_payload", {"request": text}),
            form_fields=contract.get("form_fields"),
            risk_level=RiskLevel(contract.get("risk_level", "high")),
            risk_assessment=contract.get(
                "risk_assessment",
                "This operation mutates a production system and requires explicit "
                "confirmation. Review the target system and payload before approving.",
            ),
        )
        future = await conn.request_action(card)

        try:
            form_data = await future
        except Exception:  # cancelled on disconnect
            return

        if form_data is None:
            await conn.stream_token("Action cancelled. No changes were made.")
            await conn.complete()
            return

        # Write only fires here, after a signed action_confirmed=true reply.
        # Overlay user input on top of the base payload
        card.api_payload.update(form_data)
        await self._execute_mutation(conn, contract, card)

    async def _execute_mutation(
        self, conn: Connection, contract: dict, card: ActionCardData
    ) -> None:
        bridge = get_mcp_bridge()
        try:
            result = await bridge.call_tool(
                system=contract.get("mcp_system", "odoo"),
                tool=contract.get("mcp_tool", card.intent),
                arguments=card.api_payload,
            )
            log.info("mutation_executed", intent=card.intent, action_id=card.action_id)
            await conn.stream_token(
                f"✅ Done. Your request for `{card.intent}` was processed successfully. "
                f"An email notification has been sent to mahmoud.hassan@centrocdx.com for demo purposes.\n\nResult: {result}"
            )
            await conn.complete()
        except MCPError as exc:
            log.error("mutation_failed", intent=card.intent, error=str(exc))
            await conn.error(
                f"The action could not be completed on {card.target_system}: {exc}"
            )

    # ---- FEATURES 1 + 4 + PATTERN 4: sandboxed RAG with fallback ----------
    async def _handle_rag(self, conn: Connection, user: UserContext, text: str) -> None:
        sandbox = await get_vector_sandbox()
        try:
            # Keep retrieval tight: fewer, clipped chunks => a smaller prompt =>
            # a much faster time-to-first-token on a local CPU.
            chunks = await sandbox.search(text, user=user, limit=4)
        except Exception as exc:  # vector engine unavailable
            log.error("vector_search_failed", error=str(exc))
            chunks = []

        def _clip(t: str, n: int = 700) -> str:
            return t if len(t) <= n else t[:n].rstrip() + "…"

        context_block = "\n\n".join(
            f"[{c.source or c.department}] {_clip(c.text)}" for c in chunks
        ) or "No internal documents matched within your access scope."

        # FEATURE 1 + 2: decide a SAFE scope to cache this answer under. We tag
        # the cache by the retrieved documents' scope — NOT the asker's scope —
        # so a broad-scope viewer (e.g. global manager) can never cache a
        # tenant-specific answer as "global" and leak it to other tenants.
        tenant_scopes = {
            c.account_scope
            for c in chunks
            if c.account_scope and c.account_scope != "global"
        }
        if len(tenant_scopes) == 1:
            cache_scope: str | None = next(iter(tenant_scopes))
        elif not tenant_scopes:
            cache_scope = "global"
        else:
            cache_scope = None  # mixed tenants -> never cache

        messages = [
            {
                "role": "system",
                "content": (
                    SYSTEM_PROMPT
                    + f"\n\nUser scope: account={user.account_scope}, role={user.role}, "
                    + f"department={user.department}.\n\nCONTEXT:\n{context_block}"
                )
            },
            {"role": "user", "content": text},
        ]

        llm = get_llm()
        full: list[str] = []
        try:
            async for token in llm.stream(messages):
                full.append(token)
                await conn.stream_token(token)
            
            if not full:
                raise LLMUnavailable("LLM returned 0 tokens")
                
            await conn.complete()
            # Promote successful answers into the CAG cache for next time,
            # tagged with the SOURCE documents' scope (see above) — never the
            # asker's scope. Skip caching when sources span multiple tenants.
            if full and cache_scope is not None:
                cache = await get_semantic_cache()
                await cache.add(text, "".join(full), cache_scope)
        except LLMUnavailable as exc:
            # PATTERN #4: never drop the socket. Try cache, else enterprise message.
            log.error("llm_unavailable", error=str(exc), session=conn.session_id)
            cache = await get_semantic_cache()
            fallback = await cache.lookup(text, user.account_scope)
            if fallback is not None:
                await conn.stream_token(fallback[0])
                await conn.complete()
            else:
                await conn.error(FALLBACK_MESSAGE)


_agent: ManagerAgent | None = None


def get_agent() -> ManagerAgent:
    global _agent
    if _agent is None:
        _agent = ManagerAgent()
    return _agent

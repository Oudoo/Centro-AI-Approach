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
from core.notifier import notify_request
from core.requests_store import record_request
from core.sockets import Connection
from core.vector_db import get_vector_sandbox
from integrations.schema_registry import get_schema_registry
from models import ActionCardData, RiskLevel, UserContext

log = structlog.get_logger("aura.agent")

SYSTEM_PROMPT = (
    "You are Aura, the friendly AI co-pilot by Centro — warm, concise and helpful, "
    "like a supportive colleague who makes the workday easier.\n"
    "CRITICAL RULES:\n"
    "1. Answer ONLY using the information in the CONTEXT provided below.\n"
    "2. NEVER invent company policies, numbers, names, dates, or procedures. If the "
    "CONTEXT does not contain the answer, say you don't have that information in "
    "their knowledge base — do not guess from general knowledge.\n"
    "3. Format answers cleanly with Markdown (bold, bullet lists, and tables) when "
    "it improves readability."
)

OUT_OF_SCOPE_MESSAGE = (
    "I couldn't find anything in the knowledge available to your role and account "
    "that covers that. I can only answer from Centro's approved documents — try "
    "rephrasing, or ask your admin to add the relevant document to my knowledge base."
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
        try:
            # 1) CAG fast-path ---------------------------------------------
            # A cache/embedding hiccup must never crash the turn — treat as miss.
            try:
                cache = await get_semantic_cache()
                hit = await cache.lookup(text, user.account_scope)
            except Exception as exc:
                log.warning("cag_lookup_failed", error=str(exc))
                hit = None
            if hit is not None:
                answer, score = hit
                log.info("cag_hit", session=conn.session_id, score=round(score, 4))
                await conn.stream_token(answer)
                await conn.complete()
                return

            # 2) Mutation intent -> dual-confirmation Action Card ----------
            intent = self.detect_intent(text)
            if intent in MUTATION_INTENTS:
                await self._handle_mutation(conn, user, intent, text)
                return

            # 4) RAG answer (default path) ---------------------------------
            await self._handle_rag(conn, user, text)
        except Exception as exc:
            # Last line of defence: a friendly fallback, never a raw error.
            log.error("handle_query_failed", session=conn.session_id, error=str(exc))
            await conn.error(FALLBACK_MESSAGE)

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
            summary=contract.get("summary", "Please fill in the details below."),
            api_payload={},  # no raw API payload shown to the user
            form_fields=contract.get("form_fields"),
            # These are kept for the data contract but are no longer surfaced to
            # the user — this assistant only files safe, reviewable requests.
            risk_level=RiskLevel(contract.get("risk_level", "low")),
            risk_assessment="",
        )
        future = await conn.request_action(card)

        try:
            form_data = await future
        except Exception:  # cancelled on disconnect
            return

        if form_data is None:
            await conn.stream_token("No problem — I've cancelled that request. 👍")
            await conn.complete()
            return

        await self._submit_request(conn, user, contract, card, form_data or {})

    async def _submit_request(
        self,
        conn: Connection,
        user: UserContext,
        contract: dict,
        card: ActionCardData,
        form_data: dict,
    ) -> None:
        """Persist the request and notify the team (email in demo phase)."""
        request_type = card.intent
        target = card.target_system
        details = {k: v for k, v in form_data.items() if v not in (None, "")}
        try:
            await record_request(request_type, target, user, details)
            sent, to_addr = await notify_request(request_type, target, user, details)
        except Exception as exc:
            log.error("request_submit_failed", intent=request_type, error=str(exc))
            await conn.error(
                "I couldn't file that request just now — please try again in a moment."
            )
            return

        log.info("request_submitted", intent=request_type, emailed=sent)
        pretty = request_type.replace("_", " ").title()
        detail_lines = "\n".join(
            f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in details.items()
        ) or "- (no extra details)"
        notice = (
            f"and a notification was emailed to **{to_addr}**"
            if sent
            else f"and logged for the team to action (routing to **{to_addr}**)"
        )
        await conn.stream_token(
            f"✅ **Done!** Your **{pretty}** request has been recorded {notice}.\n\n"
            f"{detail_lines}\n\nYou'll hear back once it's reviewed. Anything else?"
        )
        await conn.complete()

    # ---- FEATURES 1 + 4 + PATTERN 4: sandboxed RAG with fallback ----------
    async def _handle_rag(self, conn: Connection, user: UserContext, text: str) -> None:
        sandbox = await get_vector_sandbox()
        # Keep retrieval tight: fewer, clipped chunks => a smaller prompt => a
        # much faster time-to-first-token on a local CPU. If the vector engine
        # or embeddings are DOWN this raises and the outer handler shows the
        # graceful fallback (not a misleading "no documents" message).
        chunks = await sandbox.search(text, user=user, limit=3)

        # GROUNDED-ONLY: if retrieval found nothing in the user's scope, do NOT
        # call the LLM (which would hallucinate, e.g. inventing a Coastline
        # policy for a Trueblue agent). Return a deterministic, instant message.
        if not chunks:
            log.info("rag_no_context", session=conn.session_id, scope=user.account_scope)
            await conn.stream_token(OUT_OF_SCOPE_MESSAGE)
            await conn.complete()
            return

        def _clip(t: str, n: int = 500) -> str:
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

"""
Aura (by Centro) — Rule-based small talk (no LLM, no embeddings).

Runs BEFORE the CAG/RAG pipeline so greetings, thanks, farewells and "who are
you" are answered instantly — and keep working even if the local model engine
(which also serves embeddings) is offline. Conservative matching: only fires on
short messages so it never hijacks a real question.
"""
from __future__ import annotations

import re

GREETING = (
    "Hi there! 👋 I'm **Aura**, your Co-Pilot by Centro. How can I help today — "
    "an HR or policy question, your schedule, or a quick request like leave or a "
    "shift swap?"
)
HOW_ARE_YOU = (
    "I'm doing great, thanks for asking! 😊 I'm ready to help. What can I do for "
    "you — a policy question, leave, your schedule, or a request?"
)
IDENTITY = (
    "I'm **Aura**, your AI Co-Pilot by Centro 😊. I help you with HR and policy "
    "questions from Centro's knowledge base, and I can file requests for you — "
    "annual or casual leave, shift swaps, and break-time changes. What would you "
    "like to do?"
)
THANKS = "You're very welcome! 🙌 Is there anything else I can help you with?"
FAREWELL = "Take care! 👋 I'm here whenever you need me — just say hi."

_PUNCT = re.compile(r"[^\w\s']")


def _norm(text: str) -> str:
    return _PUNCT.sub("", (text or "").lower()).strip()


def smalltalk_response(text: str) -> str | None:
    """Return a canned reply for conversational openers/closers, else None."""
    t = _norm(text)
    if not t:
        return None
    words = t.split()
    short = len(words) <= 6

    # Identity / capabilities — safe to match even in longer phrasing.
    if any(p in t for p in (
        "who are you", "what are you", "your name", "introduce yourself",
        "what can you do", "what do you do", "how can you help", "what is aura",
        "tell me about yourself",
    )):
        return IDENTITY

    if not short:
        return None  # avoid hijacking real questions

    greet_exact = {
        "hi", "hii", "hiii", "hello", "helo", "hey", "hey", "heya", "hiya",
        "yo", "hi there", "hello there", "hey there", "good morning",
        "good afternoon", "good evening", "greetings", "sup", "whats up",
    }
    if t in greet_exact or t.startswith((
        "hi ", "hii", "hey ", "hello ", "good morning", "good afternoon",
        "good evening",
    )):
        return GREETING

    if any(p in t for p in ("how are you", "how r u", "how are u", "hows it going",
                            "how is it going", "how do you do", "how you doing")):
        return HOW_ARE_YOU

    if t.startswith(("thank", "thanks", "thx", "ty ")) or t in {"ty", "thanks", "thank you"} \
            or "thank you" in t or "thanks" in t:
        return THANKS

    if t in {"bye", "goodbye", "good bye", "see you", "see ya", "cya", "take care",
             "thats all", "that is all", "im done", "i am done"} \
            or t.startswith(("bye", "goodbye", "see you", "see ya")):
        return FAREWELL

    return None

"""
Aura (by Centro) — lightweight in-memory usage analytics.

Powers the admin dashboard tile (queries answered, CAG hit-rate = cost saved,
top intents). In-memory and resets on restart — fine for the demo; swap for a
persisted table when we move to Postgres (ROADMAP B5).
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

_counts: Counter = Counter()
_intents: Counter = Counter()
_started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")


def incr(key: str, n: int = 1) -> None:
    _counts[key] += n


def incr_intent(intent: str) -> None:
    _intents[intent] += 1


def snapshot() -> dict:
    total = _counts.get("queries", 0)
    cag = _counts.get("cag_hits", 0)
    smalltalk = _counts.get("smalltalk", 0)
    instant = cag + smalltalk
    return {
        "since": _started_at,
        "queries": total,
        "cag_hits": cag,
        "smalltalk": smalltalk,
        "rag_answered": _counts.get("rag_answered", 0),
        "out_of_scope": _counts.get("out_of_scope", 0),
        "requests_submitted": _counts.get("requests_submitted", 0),
        # % of queries served instantly without invoking the LLM (cost saved).
        "instant_rate": round(100 * instant / total, 1) if total else 0.0,
        "top_intents": _intents.most_common(5),
    }

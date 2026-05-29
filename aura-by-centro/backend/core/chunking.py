"""
Aura (by Centro) — Smart chunking (Pillar 1: Ingestion Layer).

Semantic-aware partitioning by document type, replacing naive fixed-size slicing:

- Markdown handbooks  -> header-aware split (#/##/###), each policy section stays
  whole. Parent-Child: embed smaller child windows, return the full parent section.
- Integration schemas -> JSON-aware chunker that never splits mid-object; an
  endpoint's structure/payload/response stay coupled.
- Fallback            -> paragraph splitter with overlap.

Each chunk is a dict: {"text": <embed this>, "parent_text": <return this>,
"section": <heading/label>}.
"""
from __future__ import annotations

import json
import re

_SENT = re.compile(r"(?<=[.!?])\s+")
_HEADER = re.compile(r"^(#{1,6})\s+(.*)$")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text) if s.strip()]


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    """Paragraph-aware splitter with overlap (generic fallback)."""
    text = (text or "").strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= max_chars:
            buffer = f"{buffer}\n\n{para}".strip()
            continue
        if buffer:
            chunks.append(buffer)
        if len(para) > max_chars:
            start = 0
            while start < len(para):
                chunks.append(para[start : start + max_chars])
                start += max_chars - overlap
            buffer = ""
        else:
            buffer = para
    if buffer:
        chunks.append(buffer)
    return chunks


def markdown_header_split(text: str) -> list[dict]:
    """Split markdown into sections by headers; keep each section intact."""
    lines = (text or "").splitlines()
    sections: list[dict] = []
    heading = ""
    body: list[str] = []

    def flush():
        content = "\n".join(body).strip()
        if heading or content:
            sections.append({"heading": heading.strip(), "body": content})

    for line in lines:
        m = _HEADER.match(line)
        if m:
            flush()
            heading = m.group(2)
            body = []
        else:
            body.append(line)
    flush()
    return [s for s in sections if s["body"] or s["heading"]]


def _parent_child(section: dict, child_chars: int = 320) -> list[dict]:
    """
    Parent = the whole section (heading + body) -> returned to the LLM.
    Children = smaller sentence windows -> embedded for sharper recall.
    """
    heading = section["heading"]
    body = section["body"]
    parent_text = (f"## {heading}\n{body}" if heading else body).strip()
    sents = _sentences(body) or ([heading] if heading else [])
    children: list[str] = []
    buf = ""
    for s in sents:
        cand = f"{buf} {s}".strip()
        if len(cand) <= child_chars:
            buf = cand
        else:
            if buf:
                children.append(buf)
            buf = s
    if buf:
        children.append(buf)
    if not children:
        children = [parent_text]
    # Prefix the heading into each child so a section title boosts recall.
    prefix = f"{heading}. " if heading else ""
    return [
        {"text": (prefix + c).strip(), "parent_text": parent_text, "section": heading}
        for c in children
    ]


def json_schema_chunks(text: str) -> list[dict]:
    """JSON-aware: keep each integration contract object coupled (never split)."""
    try:
        data = json.loads(text)
    except ValueError:
        return [{"text": text, "parent_text": text, "section": ""}]
    objects = data if isinstance(data, list) else [data]
    chunks: list[dict] = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        name = obj.get("name") or obj.get("target_system") or "schema"
        intents = ", ".join(obj.get("intents", []) or [])
        # A compact, search-friendly summary; the full object is the parent.
        summary = (
            f"{name}. Intents: {intents}. "
            f"Endpoint: {obj.get('endpoint', '')}. "
            f"Target system: {obj.get('target_system', '')}. "
            f"{obj.get('summary', '')}"
        ).strip()
        pretty = json.dumps(obj, indent=2, ensure_ascii=False)
        chunks.append({"text": summary, "parent_text": pretty, "section": name})
    return chunks or [{"text": text, "parent_text": text, "section": ""}]


def smart_chunks(filename: str, text: str) -> list[dict]:
    """Dispatch to the right chunker by file type. Returns parent-child dicts."""
    name = (filename or "").lower()
    if name.endswith((".md", ".markdown")):
        out: list[dict] = []
        for section in markdown_header_split(text):
            out.extend(_parent_child(section))
        return out or [{"text": text, "parent_text": text, "section": ""}]
    if name.endswith(".json"):
        return json_schema_chunks(text)
    return [{"text": c, "parent_text": c, "section": ""} for c in chunk_text(text)]

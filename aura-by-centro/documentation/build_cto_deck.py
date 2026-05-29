"""
Generates the 3-slide CTO deck for Aura (by Centro) as a branded 16:9 PDF.

  Slide 1  Title
  Slide 2  Architecture diagram
  Slide 3  Roadmap

Centro Brand Book (Pomelli): Prussian Blue #004A59, Onyx #32373C, White, Roboto
(Helvetica substituted as the metric-compatible system face for portability).

    python3 documentation/build_cto_deck.py
Outputs: documentation/Aura_by_Centro_CTO_Deck.pdf
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PRUSSIAN = HexColor("#004A59")
PRUSSIAN_700 = HexColor("#063b47")
PRUSSIAN_900 = HexColor("#042830")
ONYX = HexColor("#32373C")
ONYX_60 = HexColor("#6b7177")
ACCENT = HexColor("#1A7A9E")
MIST = HexColor("#E8EEF0")
WHITE = HexColor("#FFFFFF")

OUT = Path(__file__).resolve().parent / "Aura_by_Centro_CTO_Deck.pdf"
PAGE_W, PAGE_H = 338.667 * mm, 190.5 * mm  # 16:9


# ---------------------------------------------------------------- helpers
def logo(c: canvas.Canvas, cx: float, cy: float, r: float, color=WHITE) -> None:
    c.setStrokeColor(color)
    c.setLineWidth(r * 0.18)
    c.line(cx - r, cy - r * 0.8, cx, cy + r)
    c.line(cx, cy + r, cx + r, cy - r * 0.8)
    c.line(cx - r * 0.5, cy, cx + r * 0.5, cy)


def box(c, x, y, w, h, title, lines, fill=MIST, bar=PRUSSIAN,
        title_color=PRUSSIAN, text_color=ONYX, ts=10, ls=7.8):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, 2.5, fill=1, stroke=0)
    c.setFillColor(bar)
    c.roundRect(x, y, 2.4 * mm, h, 1.2, fill=1, stroke=0)
    c.setFillColor(title_color)
    c.setFont("Helvetica-Bold", ts)
    c.drawString(x + 6 * mm, y + h - 6 * mm, title)
    c.setFillColor(text_color)
    c.setFont("Helvetica", ls)
    ty = y + h - 11 * mm
    for ln in lines:
        c.drawString(x + 6 * mm, ty, ln)
        ty -= 4.4 * mm


def arrow(c, x1, y1, x2, y2, color=ACCENT, w=1.6):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(w)
    c.line(x1, y1, x2, y2)
    # simple arrowhead
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    hl = 2.6 * mm
    for da in (math.radians(160), math.radians(-160)):
        c.line(x2, y2, x2 + hl * math.cos(ang + da), y2 + hl * math.sin(ang + da))


# ---------------------------------------------------------------- slides
def slide_title(c):
    c.setFillColor(PRUSSIAN)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(PRUSSIAN_900)
    c.rect(0, 0, PAGE_W, 14 * mm, fill=1, stroke=0)

    logo(c, 40 * mm, PAGE_H - 52 * mm, 11 * mm)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 52)
    c.drawString(58 * mm, PAGE_H - 60 * mm, "Aura")
    c.setFont("Helvetica", 30)
    c.drawString(132 * mm, PAGE_H - 60 * mm, "by Centro")

    c.setFont("Helvetica-Bold", 18)
    c.drawString(58 * mm, PAGE_H - 76 * mm, "Enterprise AI Co-Pilot")
    c.setFillColor(MIST)
    c.setFont("Helvetica-Oblique", 13)
    c.drawString(58 * mm, PAGE_H - 86 * mm,
                 "Helping businesses drive meaningful change for growth.")

    # chips
    chips = ["Local Gemma LLM", "Multi-tenant & sandboxed", "RAG + CAG memory",
             "Zoho · Odoo · Genesys (MCP)"]
    cx = 58 * mm
    c.setFont("Helvetica-Bold", 9)
    for ch in chips:
        w = c.stringWidth(ch, "Helvetica-Bold", 9) + 10 * mm
        c.setFillColor(PRUSSIAN_700)
        c.roundRect(cx, PAGE_H - 104 * mm, w, 9 * mm, 4, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.drawCentredString(cx + w / 2, PAGE_H - 101 * mm, ch)
        cx += w + 4 * mm

    c.setFillColor(MIST)
    c.setFont("Helvetica", 10)
    c.drawString(58 * mm, 20 * mm, "CTO Briefing  ·  Proof of Concept")
    c.drawRightString(PAGE_W - 18 * mm, 20 * mm, "Confidential")


def slide_architecture(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # header
    c.setFillColor(PRUSSIAN)
    c.rect(0, PAGE_H - 22 * mm, PAGE_W, 22 * mm, fill=1, stroke=0)
    logo(c, 16 * mm, PAGE_H - 11 * mm, 6 * mm)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(26 * mm, PAGE_H - 14 * mm, "How Aura works")
    c.setFont("Helvetica", 10)
    c.drawRightString(PAGE_W - 16 * mm, PAGE_H - 14 * mm,
                      "One request, end to end")

    mid = 95 * mm  # vertical center of the flow band

    # Zone 1 — Clients
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(16 * mm, mid + 40 * mm, "CLIENTS")
    box(c, 14 * mm, mid + 20 * mm, 52 * mm, 16 * mm, "Web dashboard", [], fill=MIST)
    box(c, 14 * mm, mid + 1 * mm, 52 * mm, 16 * mm, "Desktop app", ["per-PC, branded"], fill=MIST)
    box(c, 14 * mm, mid - 22 * mm, 52 * mm, 18 * mm, "Zoho People", ["embedded Web Tab"], fill=MIST)

    # Zone 2 — Backbone
    box(c, 84 * mm, mid - 14 * mm, 30 * mm, 44 * mm, "FastAPI",
        ["WebSocket", "/ws", "typed", "contract"], fill=PRUSSIAN,
        bar=PRUSSIAN_900, title_color=WHITE, text_color=MIST, ts=10, ls=8)

    # Zone 3 — Agent
    box(c, 130 * mm, mid - 16 * mm, 52 * mm, 48 * mm, "Manager Agent",
        ["Routes every query:", "1 CAG fast-path", "2 mutation? -> card", "3 else -> RAG"],
        fill=HexColor("#dfeaed"), title_color=PRUSSIAN, ts=10, ls=8)

    # Zone 4 — Engines (stacked)
    box(c, 198 * mm, mid + 18 * mm, 64 * mm, 16 * mm, "Semantic CAG cache",
        [">=0.92 -> skip LLM"], fill=MIST, ls=7.5)
    box(c, 198 * mm, mid - 1 * mm, 64 * mm, 16 * mm, "Vector DB (Qdrant)",
        ["scope-filtered, no leak"], fill=MIST, ls=7.5)
    box(c, 198 * mm, mid - 20 * mm, 64 * mm, 16 * mm, "MCP bridge",
        ["dual-confirm writes"], fill=MIST, ls=7.5)

    # Zone 5 — backends
    box(c, 278 * mm, mid + 12 * mm, 48 * mm, 22 * mm, "Gemma LLM",
        ["local / AWS GPU", "streams tokens"], fill=PRUSSIAN, bar=PRUSSIAN_900,
        title_color=WHITE, text_color=MIST, ls=7.8)
    box(c, 278 * mm, mid - 20 * mm, 48 * mm, 24 * mm, "Systems",
        ["Zoho · Odoo", "Genesys", "(via MCP)"], fill=ONYX, bar=PRUSSIAN,
        title_color=WHITE, text_color=MIST, ls=7.8)

    # arrows
    arrow(c, 66 * mm, mid + 6 * mm, 84 * mm, mid + 6 * mm)
    arrow(c, 114 * mm, mid + 6 * mm, 130 * mm, mid + 6 * mm)
    arrow(c, 182 * mm, mid + 6 * mm, 198 * mm, mid + 24 * mm)
    arrow(c, 182 * mm, mid + 6 * mm, 198 * mm, mid + 7 * mm)
    arrow(c, 182 * mm, mid + 6 * mm, 198 * mm, mid - 12 * mm)
    arrow(c, 262 * mm, mid + 24 * mm, 278 * mm, mid + 22 * mm)   # cache->? (visual)
    arrow(c, 262 * mm, mid - 12 * mm, 278 * mm, mid - 10 * mm)   # mcp->systems

    # footer note
    c.setFillColor(ONYX)
    c.rect(0, 0, PAGE_W, 9 * mm, fill=1, stroke=0)
    c.setFillColor(MIST)
    c.setFont("Helvetica", 8)
    c.drawString(16 * mm, 3.2 * mm,
                 "Graceful fallback: if the GPU OOMs/spikes, Aura serves the cache "
                 "or an enterprise message — the WebSocket never drops.")


def slide_roadmap(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(PRUSSIAN)
    c.rect(0, PAGE_H - 22 * mm, PAGE_W, 22 * mm, fill=1, stroke=0)
    logo(c, 16 * mm, PAGE_H - 11 * mm, 6 * mm)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(26 * mm, PAGE_H - 14 * mm, "Where we are & what's next")

    # Left — delivered
    c.setFillColor(HexColor("#0a7d52"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(18 * mm, PAGE_H - 36 * mm, "DELIVERED  (working POC)")
    done = [
        "Multi-tenant vector sandboxing (zero data leakage)",
        "Semantic CAG cache — instant, LLM-bypassing answers",
        "Dual-confirmation Action Cards for all writes",
        "Dynamic API schemas (no prompt hardcoding)",
        "Admin dashboard + self-service document uploads",
        "Embeddable in Zoho People; branded desktop client",
        "Runs on local Gemma — $0 software licensing",
    ]
    c.setFillColor(ONYX)
    c.setFont("Helvetica", 10)
    y = PAGE_H - 46 * mm
    for d in done:
        c.setFillColor(HexColor("#0a7d52"))
        c.drawString(18 * mm, y, "v")
        c.setFillColor(ONYX)
        c.drawString(24 * mm, y, d)
        y -= 8 * mm

    # divider
    c.setStrokeColor(MIST)
    c.setLineWidth(1)
    c.line(PAGE_W / 2, 16 * mm, PAGE_W / 2, PAGE_H - 30 * mm)

    # Right — next
    rx = PAGE_W / 2 + 12 * mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(rx, PAGE_H - 36 * mm, "NEXT  (to production)")
    nxt = [
        ("Bigger + multimodal model", "Gemma 3 12B/27B or vision model on AWS GPU"),
        ("Production SSO", "Centro identity issues scoped tokens"),
        ("Live MCP integrations", "Real Odoo/Zoho/Genesys writes"),
        ("Desktop packaging", "Electron / Tauri / PWA — decision pending"),
        ("Scale on AWS", "vLLM GPU fleet sized for 1,500 users"),
    ]
    c.setFont("Helvetica", 10)
    y = PAGE_H - 46 * mm
    for t, sub in nxt:
        c.setFillColor(ACCENT)
        c.drawString(rx, y, ">")
        c.setFillColor(ONYX)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(rx + 6 * mm, y, t)
        c.setFillColor(ONYX_60)
        c.setFont("Helvetica", 8.6)
        c.drawString(rx + 6 * mm, y - 4 * mm, sub)
        c.setFont("Helvetica", 10)
        y -= 11 * mm

    c.setFillColor(ONYX)
    c.rect(0, 0, PAGE_W, 9 * mm, fill=1, stroke=0)
    c.setFillColor(MIST)
    c.setFont("Helvetica", 8)
    c.drawString(16 * mm, 3.2 * mm,
                 "Values: Innovation · Efficiency · Operational Excellence · "
                 "Accountability · Precision")


def slide_agentic_rag(c):
    c.setFillColor(WHITE); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(PRUSSIAN); c.rect(0, PAGE_H - 22 * mm, PAGE_W, 22 * mm, fill=1, stroke=0)
    logo(c, 16 * mm, PAGE_H - 11 * mm, 6 * mm)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 18)
    c.drawString(26 * mm, PAGE_H - 14 * mm, "Advanced & Agentic RAG — beyond a naive chatbot")

    mid = 112 * mm
    pillars = [
        ("1 · Smart Chunking", ["Header-aware Markdown,", "JSON-coupled schemas,", "Parent-Child retrieval"]),
        ("2 · Hybrid Search", ["Dense (semantic) +", "Sparse BM25 (exact),", "fused via RRF"]),
        ("3 · Reranking", ["Cross-encoder re-orders", "top 20 → best 5", "→ fewer hallucinations"]),
        ("4 · Agentic Loop", ["Rewrite → Route(RBAC)", "→ Reflect & re-search;", "never guesses"]),
    ]
    n = len(pillars)
    gap = 6 * mm
    bw = (PAGE_W - 32 * mm - gap * (n - 1)) / n
    x = 16 * mm
    for i, (title, lines) in enumerate(pillars):
        box(c, x, mid, bw, 40 * mm, title, lines, fill=HexColor("#dfeaed"), ls=8.4)
        if i < n - 1:
            arrow(c, x + bw, mid + 20 * mm, x + bw + gap, mid + 20 * mm)
        x += bw + gap

    # input/output rail
    c.setFillColor(ONYX_60); c.setFont("Helvetica-Oblique", 10)
    c.drawString(16 * mm, mid + 46 * mm, "Messy human question  →  optimized query  →  sandboxed, reranked context  →  grounded answer with 📄 citations")

    # impact band
    c.setFillColor(HexColor("#0a7d52"))
    c.roundRect(16 * mm, mid - 30 * mm, PAGE_W - 32 * mm, 22 * mm, 4, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 11)
    c.drawString(22 * mm, mid - 16 * mm, "IMPACT")
    c.setFont("Helvetica", 10)
    c.drawString(40 * mm, mid - 14 * mm,
                 "Exact-match + semantic recall · sharply reduced hallucinations · RBAC enforced on every path · "
                 "graceful degradation if any component is offline.")
    c.drawString(40 * mm, mid - 20 * mm,
                 "All pillars are config-flagged in backend/config.py and implemented in core/{chunking,retrieval,rerank,agent}.py.")

    c.setFillColor(ONYX); c.rect(0, 0, PAGE_W, 9 * mm, fill=1, stroke=0)
    c.setFillColor(MIST); c.setFont("Helvetica", 8)
    c.drawString(16 * mm, 3.2 * mm, "Most vendors charge enterprise SaaS fees for this retrieval stack. Aura runs it on Centro hardware at $0 licensing.")


def slide_why(c):
    c.setFillColor(WHITE); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(PRUSSIAN); c.rect(0, PAGE_H - 22 * mm, PAGE_W, 22 * mm, fill=1, stroke=0)
    logo(c, 16 * mm, PAGE_H - 11 * mm, 6 * mm)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 18)
    c.drawString(26 * mm, PAGE_H - 14 * mm, "Why Aura wins the room")

    quad = [
        ("Not a wrapper", "Hybrid + rerank + agentic retrieval — a defensible architecture, not a thin API shim."),
        ("Private & compliant", "Every byte stays on Centro infra; tenant isolation enforced at the DB index."),
        ("Safe by design", "Grounded-only answers, no silent writes, full audit trail + CSV export."),
        ("Cheap & scalable", "$0 software licensing; one config flip from laptop to a multi-GPU AWS fleet."),
    ]
    xw = (PAGE_W - 32 * mm - 6 * mm) / 2
    coords = [(16 * mm, 95 * mm), (16 * mm + xw + 6 * mm, 95 * mm),
              (16 * mm, 58 * mm), (16 * mm + xw + 6 * mm, 58 * mm)]
    for (title, body), (x, y) in zip(quad, coords):
        box(c, x, y, xw, 30 * mm, title, [body[:58], body[58:]], fill=MIST, ls=9)

    c.setFillColor(ONYX); c.rect(0, 0, PAGE_W, 9 * mm, fill=1, stroke=0)
    c.setFillColor(MIST); c.setFont("Helvetica", 8)
    c.drawString(16 * mm, 3.2 * mm, "Local LLM · Qdrant (dense) + BM25 (sparse) · cross-encoder rerank · MCP integrations · WebSocket streaming.")


def main():
    c = canvas.Canvas(str(OUT), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Aura by Centro — CTO Deck")
    slide_title(c); c.showPage()
    slide_architecture(c); c.showPage()
    slide_agentic_rag(c); c.showPage()
    slide_why(c); c.showPage()
    slide_roadmap(c); c.showPage()
    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

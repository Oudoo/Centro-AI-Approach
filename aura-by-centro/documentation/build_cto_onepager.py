"""
Generates the one-page CTO brief for Aura (by Centro) as a branded PDF.

Centro Brand Book (Pomelli): Prussian Blue #004A59, Onyx #32373C, White, Roboto
(Helvetica is substituted as the metric-compatible system face for portability).

    python3 documentation/build_cto_onepager.py
Outputs: documentation/Aura_by_Centro_CTO_Onepager.pdf
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PRUSSIAN = HexColor("#004A59")
PRUSSIAN_700 = HexColor("#063b47")
ONYX = HexColor("#32373C")
ONYX_60 = HexColor("#6b7177")
ACCENT = HexColor("#1A7A9E")
MIST = HexColor("#E8EEF0")
WHITE = HexColor("#FFFFFF")

OUT = Path(__file__).resolve().parent / "Aura_by_Centro_CTO_Onepager.pdf"
PAGE_W, PAGE_H = landscape(A4)  # 297 x 210 mm


def draw(c: canvas.Canvas) -> None:
    # ---- Header band ----
    c.setFillColor(PRUSSIAN)
    c.rect(0, PAGE_H - 34 * mm, PAGE_W, 34 * mm, fill=1, stroke=0)

    # Logo mark
    c.setFillColor(WHITE)
    cx, cy = 22 * mm, PAGE_H - 17 * mm
    c.setLineWidth(2.2)
    c.setStrokeColor(WHITE)
    c.line(cx - 6 * mm, cy - 5 * mm, cx, cy + 6 * mm)
    c.line(cx, cy + 6 * mm, cx + 6 * mm, cy - 5 * mm)
    c.line(cx - 3 * mm, cy, cx + 3 * mm, cy)

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(34 * mm, PAGE_H - 16 * mm, "Aura  by Centro")
    c.setFont("Helvetica", 11)
    c.drawString(34 * mm, PAGE_H - 22 * mm,
                 "Enterprise AI Co-Pilot  ·  CTO Briefing  ·  Proof of Concept")
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(MIST)
    c.drawString(34 * mm, PAGE_H - 28 * mm,
                 "Helping businesses drive meaningful change for growth.")

    # Right-aligned status chip
    c.setFillColor(PRUSSIAN_700)
    c.roundRect(PAGE_W - 70 * mm, PAGE_H - 22 * mm, 56 * mm, 11 * mm, 3, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PAGE_W - 42 * mm, PAGE_H - 18.2 * mm, "STATUS: WORKING PROTOTYPE")

    # ---- Body columns ----
    top = PAGE_H - 44 * mm
    col_w = (PAGE_W - 30 * mm) / 2
    left_x = 15 * mm
    right_x = 15 * mm + col_w + 0 * mm

    # Left column: What it is + stack
    y = top
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x, y, "WHAT IT IS")
    y -= 6 * mm
    c.setFillColor(ONYX)
    c.setFont("Helvetica", 9.5)
    for line in [
        "A multi-tenant AI co-pilot for Centro's BPO operations. Runs a local",
        "Gemma LLM, streams over WebSockets, and integrates with Zoho / Odoo /",
        "Genesys via the Model Context Protocol. Dual RAG + CAG memory model.",
    ]:
        c.drawString(left_x, y, line)
        y -= 5 * mm

    y -= 3 * mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x, y, "STACK & DEPLOYMENT")
    y -= 6 * mm
    c.setFillColor(ONYX)
    c.setFont("Helvetica", 9.5)
    for line in [
        "Frontend  Next.js + Tailwind  ->  AWS (Amplify / CloudFront)",
        "Backend   FastAPI (async)     ->  AWS ECS / App Runner",
        "LLM       Local Gemma (vLLM)  ->  AWS EC2 GPU",
        "Vectors   Qdrant (self-host)  ->  zero licensing cost",
        "Clients   Web · branded desktop app · embedded in Zoho People",
    ]:
        c.drawString(left_x, y, line)
        y -= 5 * mm

    y -= 3 * mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x, y, "WHY IT MATTERS")
    y -= 6 * mm
    c.setFillColor(ONYX)
    c.setFont("Helvetica", 9.5)
    for line in [
        "Cost      $0 software licensing; only AWS GPU compute.",
        "Privacy   Data never leaves Centro; tenant isolation in-database.",
        "Safety    Every write requires explicit human confirmation.",
        "Agility   Knowledge & integrations update via files, not code.",
    ]:
        c.drawString(left_x, y, line)
        y -= 5 * mm

    # Right column: Four features as cards
    features = [
        ("1  Metadata-Enforced Sandboxing",
         "RBAC scope compiled into a hard filter inside the vector DB. A",
         "Coastline query is physically unable to match Trueblue data."),
        ("2  Semantic CAG Cache",
         "Cosine match >= 0.92 answers instantly and bypasses the LLM —",
         "sub-second, zero GPU cost for common questions."),
        ("3  Dual-Confirmation Action Cards",
         "Mutations (payroll, scheduling, approvals) render a card showing",
         "target system, payload & risk. Nothing fires without a confirm."),
        ("4  Dynamic Schema Retrieval",
         "Integration contracts live as files / WorkDrive, not in prompts.",
         "Endpoints change with no code change and no redeploy."),
    ]
    fy = top + 2 * mm
    card_h = 24 * mm
    for title, l1, l2 in features:
        c.setFillColor(MIST)
        c.roundRect(right_x, fy - card_h, col_w, card_h - 3 * mm, 3, fill=1, stroke=0)
        c.setFillColor(PRUSSIAN)
        c.rect(right_x, fy - card_h, 2.2 * mm, card_h - 3 * mm, fill=1, stroke=0)
        c.setFillColor(PRUSSIAN)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(right_x + 6 * mm, fy - 7 * mm, title)
        c.setFillColor(ONYX)
        c.setFont("Helvetica", 9)
        c.drawString(right_x + 6 * mm, fy - 12.5 * mm, l1)
        c.drawString(right_x + 6 * mm, fy - 17 * mm, l2)
        fy -= card_h

    # ---- Footer ----
    c.setFillColor(ONYX)
    c.rect(0, 0, PAGE_W, 9 * mm, fill=1, stroke=0)
    c.setFillColor(MIST)
    c.setFont("Helvetica", 8)
    c.drawString(15 * mm, 3.2 * mm,
                 "Values: Innovation · Efficiency · Operational Excellence · Accountability · Precision")
    c.drawRightString(PAGE_W - 15 * mm, 3.2 * mm,
                      "Branded per the Centro Brand Book (Pomelli)  ·  Confidential")


def main() -> None:
    c = canvas.Canvas(str(OUT), pagesize=landscape(A4))
    c.setTitle("Aura by Centro — CTO One-Pager")
    draw(c)
    c.showPage()
    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
passage_lint.py — Score prose for AI citability using the rules in the GEO plan:

  * "atomic passages": each paragraph should be a self-contained answer of
    roughly 40-80 words (configurable).
  * no empty marketing language ("innovative", "world-class", ...).
  * each passage should contain something concrete — a number, a named
    technology, a region, or a defined term — so a model can lift and cite it.

This is heuristic and advisory: it flags paragraphs to review, it does not
rewrite them. Use it as a pre-publish checklist, not a hard gate.

Usage:
    python passage_lint.py page.md
    python passage_lint.py page.md --min 40 --max 60
    python passage_lint.py page.md --strict      # exit 1 if any flag fires

Pure standard library.
"""
import argparse
import re
import sys

BUZZWORDS = [
    "innovative", "cutting-edge", "cutting edge", "world-class", "world class",
    "best-in-class", "best in class", "industry-leading", "industry leading",
    "next-generation", "next generation", "revolutionary", "game-changing",
    "game changer", "synergy", "synergies", "seamless", "seamlessly",
    "robust", "holistic", "paradigm", "turnkey", "bleeding-edge",
    "state-of-the-art", "unparalleled", "best-of-breed", "frictionless",
    "transformative", "transformative excellence", "revolutionize",
    "unlock", "passion for transformation",
]

# Signals that a passage carries concrete, citable substance.
NUM_RE = re.compile(r"\b\d[\d,.]*\s?(%|percent|x|days?|hours?|months?|years?|fte|seats?|languages?)?\b", re.I)
PROPER_RE = re.compile(
    r"\b(Zoho|Odoo|CRM|ERP|HRMS|SLA|KPI|CSAT|FCR|BPO|HRO|RPO|API|Deluge|"
    r"AI|artificial intelligence|machine learning|automation|omnichannel|"
    r"contact[- ]center|call[- ]center|customer support|customer experience|"
    r"help[- ]?desk|payroll|back[- ]office|shared services|workforce|"
    r"Egypt|Cairo|El[- ]Gouna|Philippines|Manila|Virginia|Winchester|"
    r"GCC|Saudi Arabia|UAE|United Arab Emirates|Qatar|Kuwait|Bahrain|Oman|"
    r"Africa|Europe|North America|Arabic|multilingual)\b", re.I)


def split_paragraphs(text):
    # Strip code fences and headings; split on blank lines.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for b in blocks:
        lines = [l for l in b.splitlines() if not l.strip().startswith("#")]
        joined = " ".join(l.strip() for l in lines).strip()
        # skip list-only blocks and empty
        if joined and not re.match(r"^([-*]|\d+\.)\s", joined):
            out.append(joined)
    return out


def word_count(p):
    return len(re.findall(r"\b[\w'-]+\b", p))


def main():
    ap = argparse.ArgumentParser(description="Lint prose for AI citability")
    ap.add_argument("file", help="Markdown or text file")
    ap.add_argument("--min", type=int, default=40, help="Min words per passage")
    ap.add_argument("--max", type=int, default=80, help="Max words per passage")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any flag fires")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8") as fh:
        text = fh.read()

    paras = split_paragraphs(text)
    if not paras:
        print("No prose paragraphs found.")
        return

    flagged = 0
    total = len(paras)
    print(f"Linting {total} passage(s) against {args.min}-{args.max} words.\n")

    for idx, p in enumerate(paras, 1):
        issues = []
        wc = word_count(p)
        if wc < args.min:
            issues.append(f"short ({wc}w)")
        elif wc > args.max:
            issues.append(f"long ({wc}w)")

        found_buzz = [b for b in BUZZWORDS if re.search(rf"\b{re.escape(b)}\b", p, re.I)]
        if found_buzz:
            issues.append("buzzwords: " + ", ".join(sorted(set(found_buzz))))

        if not NUM_RE.search(p) and not PROPER_RE.search(p):
            issues.append("no concrete hook (no metric/tech/region)")

        if issues:
            flagged += 1
            preview = (p[:90] + "…") if len(p) > 90 else p
            print(f"[{idx}] {wc}w  {preview}")
            for it in issues:
                print(f"      - {it}")
            print()

    clean = total - flagged
    print(f"Summary: {clean}/{total} passages clean, {flagged} flagged.")
    score = round(100 * clean / total)
    print(f"Citability pass rate: {score}%")
    if args.strict and flagged:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)

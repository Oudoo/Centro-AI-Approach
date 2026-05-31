#!/usr/bin/env python3
"""
validate_schema.py — Extract JSON-LD from a page (or HTML file) and check it
for the things that break AI/Knowledge-Graph retrieval:

  * JSON that doesn't parse
  * objects with no @type
  * objects with no @id (so nothing can link to them)
  * @id references that point to nodes that don't exist (dangling links)
  * missing required properties for the core GEO types

It does NOT try to validate the whole of schema.org — that is brittle and
low-value. It checks the structural integrity an entity graph actually needs.

Usage:
    python validate_schema.py https://centrocdx.com/services/cx-outsourcing
    python validate_schema.py ./page.html
    python validate_schema.py ./graph.jsonld        # raw JSON-LD also works

Exit code is non-zero if any ERROR-level issue is found (CI-gateable).
Pure standard library.
"""
import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from html.parser import HTMLParser

# Minimum properties we expect per type for citation-readiness.
REQUIRED = {
    "Organization": ["name", "url", "description"],
    "Service": ["name", "description", "provider", "areaServed"],
    "FAQPage": ["mainEntity"],
    "Question": ["name", "acceptedAnswer"],
    "TechArticle": ["headline", "author", "datePublished"],
    "Article": ["headline", "author", "datePublished"],
    "Person": ["name"],
    "Review": ["reviewRating", "author"],
    "BreadcrumbList": ["itemListElement"],
    "WebPage": ["name"],
}


class LDExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._grab = False
        self.blocks = []
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            attrd = {k.lower(): (v or "").lower() for k, v in attrs}
            if attrd.get("type") == "application/ld+json":
                self._grab = True
                self._buf = []

    def handle_data(self, data):
        if self._grab:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self._grab:
            self.blocks.append("".join(self._buf))
            self._grab = False


def load(target: str) -> str:
    try:
        with open(target, "r", encoding="utf-8") as fh:
            return fh.read()
    except (OSError, ValueError):
        pass
    url = target if target.startswith(("http://", "https://")) else "https://" + target
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; centro-geo-schema-check/1.0)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"ERROR: could not fetch HTML for {url}: {exc}", file=sys.stderr)
        print("HINT: a redirect into a JS-gated interstitial (or a bot challenge) "
              "means non-JS crawlers get no HTML and no JSON-LD. Verify the page "
              "renders server-side for bots, or test a local saved HTML file.",
              file=sys.stderr)
        sys.exit(2)


def extract_blocks(raw: str):
    """Return list of raw JSON-LD strings. If the input is already JSON, use it."""
    stripped = raw.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return [raw]
    p = LDExtractor()
    p.feed(raw)
    if p.blocks:
        return p.blocks
    # Fallback regex for malformed HTML the parser tripped on.
    return re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        raw, re.DOTALL | re.IGNORECASE,
    )


def iter_nodes(obj):
    """Yield every dict that looks like a schema node."""
    if isinstance(obj, dict):
        if "@graph" in obj and isinstance(obj["@graph"], list):
            for n in obj["@graph"]:
                yield from iter_nodes(n)
        else:
            yield obj
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    yield from iter_nodes(v)
    elif isinstance(obj, list):
        for n in obj:
            yield from iter_nodes(n)


def types_of(node):
    t = node.get("@type")
    if isinstance(t, list):
        return [str(x) for x in t]
    return [str(t)] if t else []


def collect_refs(obj, defined_ids, refs):
    """Walk the structure; record defined @ids and {'@id': ...} references."""
    if isinstance(obj, dict):
        if "@id" in obj and len(obj) == 1:
            refs.add(obj["@id"])
        for k, v in obj.items():
            if k == "@id" and len(obj) > 1:
                defined_ids.add(v)
            collect_refs(v, defined_ids, refs)
    elif isinstance(obj, list):
        for x in obj:
            collect_refs(x, defined_ids, refs)


def main():
    ap = argparse.ArgumentParser(description="Validate JSON-LD structure for GEO")
    ap.add_argument("target", help="URL, HTML file, or .jsonld file")
    args = ap.parse_args()

    raw = load(args.target)
    blocks = extract_blocks(raw)
    if not blocks:
        print("ERROR: no JSON-LD <script> blocks found.", file=sys.stderr)
        sys.exit(1)

    errors, warnings = [], []
    all_defined, all_refs = set(), set()
    type_count = {}

    print(f"Found {len(blocks)} JSON-LD block(s).\n")

    for i, block in enumerate(blocks):
        try:
            data = json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"block {i}: JSON does not parse ({exc})")
            continue

        collect_refs(data, all_defined, all_refs)

        for node in iter_nodes(data):
            if not isinstance(node, dict):
                continue
            tps = types_of(node)
            if not tps:
                # nested value objects without @type are fine; only flag top-ish nodes
                if any(k in node for k in ("name", "headline", "mainEntity")):
                    warnings.append(f"block {i}: a node has properties but no @type")
                continue
            for tp in tps:
                type_count[tp] = type_count.get(tp, 0) + 1
            if "@id" not in node and not any(t in ("ListItem", "Question") for t in tps):
                warnings.append(f"block {i}: {'/'.join(tps)} has no @id (cannot be linked)")
            for tp in tps:
                for prop in REQUIRED.get(tp, []):
                    if prop not in node:
                        errors.append(f"block {i}: {tp} missing required property '{prop}'")

    dangling = {r for r in all_refs if r not in all_defined}

    print("Type inventory:")
    for tp, c in sorted(type_count.items()):
        print(f"  {tp}: {c}")
    print()

    if dangling:
        for d in sorted(dangling):
            errors.append(f"dangling @id reference: '{d}' is referenced but never defined")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ! {w}")
        print()
    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  x {e}")
        print(f"\nFAIL: {len(errors)} error(s), {len(warnings)} warning(s).")
        sys.exit(1)

    print(f"PASS: structure valid. {len(warnings)} warning(s), 0 errors.")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)

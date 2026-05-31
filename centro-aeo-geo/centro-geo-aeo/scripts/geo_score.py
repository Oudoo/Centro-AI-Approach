#!/usr/bin/env python3
"""
geo_score.py — Turn the GEO scoring framework into a reproducible number.

The original brief listed weighted categories but never defined how the score
is computed, so the targets ("GEO Score above 90") were unfalsifiable. This
script fixes that: you score each category 0-100 in a YAML (or JSON) file with
evidence, and it returns a single weighted GEO score plus the derived
sub-scores. Run it monthly and the trend becomes real.

Usage:
    python geo_score.py geo_scorecard.yml
    python geo_score.py geo_scorecard.json --json     # machine-readable out

YAML needs PyYAML (`pip install pyyaml`). JSON works with the standard library.
"""
import argparse
import json
import sys

# category -> weight (must sum to 100). Mirrors the v3.0 brief's scorecard.
WEIGHTS = {
    "crawlability": 10,
    "technical_seo": 10,
    "schema_coverage": 15,
    "knowledge_graph_completeness": 15,
    "content_citability": 15,
    "ai_citation_frequency": 15,
    "commercial_visibility": 10,
    "entity_share_of_voice": 5,
    "external_authority_signals": 5,
}

# Which categories roll up into each headline sub-score.
SUBSCORES = {
    "AI Visibility": ["ai_citation_frequency", "entity_share_of_voice"],
    "Commercial Visibility": ["commercial_visibility", "ai_citation_frequency"],
    "Knowledge Graph": ["schema_coverage", "knowledge_graph_completeness"],
    "Retrieval Readiness": ["crawlability", "technical_seo", "content_citability"],
    "Entity Authority": ["entity_share_of_voice", "external_authority_signals",
                         "knowledge_graph_completeness"],
}


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if path.endswith((".yml", ".yaml")):
        try:
            import yaml
        except ImportError:
            print("ERROR: PyYAML not installed. Run: pip install pyyaml "
                  "(or pass a .json scorecard).", file=sys.stderr)
            sys.exit(2)
        return yaml.safe_load(text)
    return json.loads(text)


def get_score(data, key):
    """Accept either a flat number or {score: n, evidence: ...}."""
    val = data.get(key)
    if val is None:
        return None
    if isinstance(val, dict):
        return val.get("score")
    return val


def weighted(scores):
    total_w = sum(WEIGHTS[k] for k in scores)
    if total_w == 0:
        return 0.0
    return sum(scores[k] * WEIGHTS[k] for k in scores) / total_w


def main():
    ap = argparse.ArgumentParser(description="Compute a weighted GEO score")
    ap.add_argument("scorecard", help="Path to geo_scorecard.yml or .json")
    ap.add_argument("--json", action="store_true", help="Emit JSON only")
    args = ap.parse_args()

    data = load(args.scorecard) or {}
    cats = data.get("categories", data)

    scores, missing = {}, []
    for key in WEIGHTS:
        s = get_score(cats, key)
        if s is None:
            missing.append(key)
        else:
            scores[key] = max(0, min(100, float(s)))

    geo = round(weighted(scores), 1)
    subs = {}
    for label, keys in SUBSCORES.items():
        present = {k: scores[k] for k in keys if k in scores}
        subs[label] = round(weighted(present), 1) if present else None

    if args.json:
        print(json.dumps(
            {"geo_score": geo, "subscores": subs, "missing": missing,
             "categories": scores}, indent=2))
        return

    print("=" * 46)
    print(f"  CENTRO CDX GEO SCORE: {geo}/100")
    print("=" * 46)
    print("\nBy category (weighted):")
    for key in WEIGHTS:
        if key in scores:
            print(f"  {key:32} {scores[key]:5.0f}  (w{WEIGHTS[key]})")
        else:
            print(f"  {key:32}   n/a  (w{WEIGHTS[key]})  <- not scored")
    print("\nHeadline sub-scores:")
    for label, val in subs.items():
        print(f"  {label:22} {val if val is not None else 'n/a'}")
    if missing:
        print(f"\nNote: {len(missing)} categor(ies) unscored — GEO computed on "
              f"the rest. Fill them for a complete number.")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)

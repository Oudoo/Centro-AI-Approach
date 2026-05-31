#!/usr/bin/env python3
"""
check_ai_crawlers.py — Verify that AI answer-engine and search crawlers are
allowed to fetch a site, by parsing its robots.txt.

This is the Phase 1 (crawlability) gate from the GEO plan. If retrieval bots
cannot fetch the pages, none of the schema or content work can be cited.

Usage:
    python check_ai_crawlers.py https://centrocdx.com
    python check_ai_crawlers.py https://centrocdx.com/robots.txt --path /services/
    python check_ai_crawlers.py ./robots.txt --bots GPTBot PerplexityBot

Exit code is non-zero if any *critical* bot (see CRITICAL set) is blocked,
so this can be used as a CI gate.

Pure standard library. No third-party dependencies.
"""
import argparse
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse

# Bots that matter most for AI citation + classic search retrieval.
DEFAULT_BOTS = [
    "OAI-SearchBot",      # ChatGPT search retrieval
    "GPTBot",             # OpenAI crawler
    "ChatGPT-User",       # ChatGPT live browsing
    "PerplexityBot",      # Perplexity index
    "Perplexity-User",    # Perplexity live fetch
    "ClaudeBot",          # Anthropic crawler
    "Claude-SearchBot",   # Claude search retrieval
    "Claude-User",        # Claude live fetch
    "anthropic-ai",       # legacy Anthropic UA
    "Googlebot",          # Google search
    "Google-Extended",    # Google AI (Gemini/AI Overviews) opt-in
    "Bingbot",            # Bing / Copilot
    "Amazonbot",          # Amazon / Alexa
    "Applebot",           # Apple / Siri
    "Applebot-Extended",  # Apple AI opt-in
    "Bytespider",         # TikTok / Doubao
    "Meta-ExternalAgent", # Meta AI crawler
    "Meta-ExternalFetcher",
    "DuckAssistBot",      # DuckDuckGo AI
    "cohere-ai",
]

# If any of these are blocked, exit non-zero (hard fail for the GEO pipeline).
CRITICAL = {
    "oai-searchbot", "perplexitybot", "claude-searchbot",
    "googlebot", "google-extended", "bingbot",
}


def fetch_robots(target: str, timeout: int = 15) -> str:
    """Return robots.txt text from a URL, domain, or local file path."""
    # Local file?
    try:
        with open(target, "r", encoding="utf-8") as fh:
            return fh.read()
    except (OSError, ValueError):
        pass

    url = target
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.path.endswith("robots.txt"):
        url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    req = urllib.request.Request(
        url, headers={"User-Agent": "centro-geo-crawler-check/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_groups(text: str):
    """Parse robots.txt into [{'agents': set(), 'allow': [], 'disallow': []}]."""
    groups = []
    current = None
    expect_new = True  # whether the next User-agent starts a fresh group

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            continue
        field, value = line.split(":", 1)
        field = field.strip().lower()
        value = value.strip()

        if field == "user-agent":
            if expect_new or current is None:
                current = {"agents": set(), "allow": [], "disallow": []}
                groups.append(current)
                expect_new = False
            current["agents"].add(value.lower())
        elif field in ("allow", "disallow"):
            if current is None:
                current = {"agents": {"*"}, "allow": [], "disallow": []}
                groups.append(current)
            current[field].append(value)
            expect_new = True  # a rule line means the next UA opens a new group
    return groups


def group_for(agent: str, groups):
    """Most specific group: exact UA match wins over '*'."""
    agent = agent.lower()
    star = None
    for g in groups:
        if agent in g["agents"]:
            return g, "exact"
        if "*" in g["agents"]:
            star = g
    if star is not None:
        return star, "wildcard (*)"
    return None, "none"


def path_blocked(path: str, group):
    """Return (blocked: bool, detail: str) using longest-match precedence."""
    def match_len(patterns):
        best = -1
        for p in patterns:
            if p == "":
                continue
            stem = p.split("*", 1)[0]  # minimal wildcard handling
            if path.startswith(stem):
                best = max(best, len(stem))
        return best

    # Empty Disallow means "allow everything".
    if any(d == "" for d in group["disallow"]) and not any(
        d != "" for d in group["disallow"]
    ):
        return False, "explicit allow-all"

    dis = match_len(group["disallow"])
    alw = match_len(group["allow"])
    if dis == -1:
        return False, "no matching disallow"
    if alw >= dis:
        return False, f"allow overrides (allow≥disallow at {path})"
    return True, f"disallow matches {path}"


def main():
    ap = argparse.ArgumentParser(description="Check AI/search crawler access in robots.txt")
    ap.add_argument("target", help="URL, domain, or path to a robots.txt file")
    ap.add_argument("--path", default="/", help="Path to test (default: /)")
    ap.add_argument("--bots", nargs="*", default=DEFAULT_BOTS, help="Override bot list")
    args = ap.parse_args()

    try:
        text = fetch_robots(args.target)
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"ERROR: could not fetch robots.txt for {args.target}: {exc}", file=sys.stderr)
        # No robots.txt usually means everything is allowed — note it, don't fail.
        print("NOTE: if robots.txt is genuinely absent, all bots are allowed by default.")
        sys.exit(2)

    groups = parse_groups(text)
    print(f"Parsed {len(groups)} group(s) from robots.txt. Testing path: {args.path}\n")

    header = f"{'BOT':22} {'GROUP':14} {'STATUS':9} DETAIL"
    print(header)
    print("-" * len(header))

    blocked_critical = []
    for bot in args.bots:
        g, kind = group_for(bot, groups)
        if g is None:
            status, detail = "ALLOWED", "no matching group (default allow)"
        else:
            is_blocked, detail = path_blocked(args.path, g)
            status = "BLOCKED" if is_blocked else "ALLOWED"
            if is_blocked and bot.lower() in CRITICAL:
                blocked_critical.append(bot)
        print(f"{bot:22} {kind:14} {status:9} {detail}")

    print()
    if blocked_critical:
        print(f"FAIL: {len(blocked_critical)} critical bot(s) blocked: {', '.join(blocked_critical)}")
        print("Remediation: remove the Disallow rule for these UAs (or for '*' if they fall under it).")
        sys.exit(1)
    print("PASS: no critical AI/search crawlers are blocked.")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)

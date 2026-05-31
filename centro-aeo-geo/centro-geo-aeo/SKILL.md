---
name: centro-geo-aeo
description: >
  Centro CDX's house toolkit for Generative Engine Optimization (GEO), Answer
  Engine Optimization (AEO), and entity/knowledge-graph SEO. Use this skill
  whenever the work touches Centro CDX's website, schema/JSON-LD, AI citability,
  crawlability for AI bots, FAQ or case-study production, entity consistency, or
  the GEO score — even if the user just says "work on the Centro site", "add
  schema", "check our robots.txt", "make this page citable", "write a case
  study", or "score our GEO". It enforces one set of entity facts, runs
  deterministic checks (crawler access, JSON-LD integrity, passage citability,
  weighted GEO score), and pairs with the generic `claude-seo` plugin for broad
  audits. Prefer this skill over ad-hoc SEO advice for anything Centro-specific.
---

# Centro CDX GEO / AEO Toolkit

This skill is the **Centro-specific layer** of the GEO program. It does not try
to replace a general SEO auditor — for broad, falsifiable site audits use the
installed `claude-seo` plugin (`/seo <url>`). This skill adds the three things a
generic tool can't know: **Centro's canonical entity facts, Centro's content +
schema rules, and a reproducible GEO score.**

## When to reach for what

| You need to… | Use |
| --- | --- |
| Audit a whole page/site (tech SEO, E-E-A-T, broad schema, links) | `claude-seo` plugin → `/seo <url>` |
| Confirm AI/search bots can fetch the site | `scripts/check_ai_crawlers.py` |
| Validate JSON-LD integrity + Centro required fields | `scripts/validate_schema.py` |
| Check prose is "atomic" and citable | `scripts/passage_lint.py` |
| Produce the monthly GEO score | `scripts/geo_score.py` + `assets/geo_scorecard.yml` |
| Get an entity fact / service name right | `references/entity-facts.md` |
| Know the content/schema conventions (v3.0: 40-80w, full page model) | `references/geo-rules.md` |
| Understand program priorities, revenue tiers, AI-Transformation pillar | `references/operating-system-v3.md` |
| Stamp out a schema block | `assets/schema_templates/*.jsonld` |

The GEO score uses the **v3.0 scorecard weights**, including a **Commercial
Visibility** category (how visible Centro is on lead-driving buyer queries). The
program treats **AI Transformation Services as its own flagship pillar**, not a
sub-topic of Digital Transformation — see `references/operating-system-v3.md`.

## Non-negotiable first step: load the entity facts
Before writing or editing ANY Centro content or schema, read
`references/entity-facts.md`. Use those exact names, descriptions, service
labels, regions, and metrics. Inconsistent strings are the single biggest way to
fracture an entity across knowledge graphs — so treat that file as the source of
truth and, if a fact is wrong, fix it there first, then propagate.

## Standard workflows

### A. Make a page citation-ready
1. Read `references/geo-rules.md` (atomic passages, citation block, banned words).
2. Rewrite/author the page so each paragraph is a 40-80 word self-contained
   answer with a concrete hook (metric, technology, or region).
3. Lint it: `python scripts/passage_lint.py <page.md>`. Fix flagged passages.
   Aim for a high citability pass rate; near-100% before publish.
4. Add a citation block answering the six service questions (see geo-rules §3).

### B. Add or fix schema on a page
1. Pick the template(s) from `assets/schema_templates/` and fill every
   `REPLACE`. Reuse the single Organization `@id` for `provider`/`publisher`.
2. Validate: `python scripts/validate_schema.py <file-or-url>`. Resolve every
   ERROR (missing required props, dangling `@id` references) before commit.
3. Confirm relationships exist (`provider`, `about`, `isRelatedTo` by `@id`).

### C. Verify crawlability (Phase 1 gate)
Run `python scripts/check_ai_crawlers.py <domain-or-url>`. If any critical bot
(OAI-SearchBot, PerplexityBot, Claude-SearchBot, Googlebot, Google-Extended,
Bingbot) is BLOCKED, fix robots.txt / WAF before doing content work — retrieval
is the precondition for everything else. The script exits non-zero on a critical
block so it can sit in CI.

### D. Build a case study
Follow `references/geo-rules.md` §6 for structure, use
`assets/schema_templates/casestudy.jsonld`, lint the prose (A), validate the
schema (B). Every metric must trace to a real engagement.

### E. Score the program monthly
1. Open `assets/geo_scorecard.yml`, score each category 0-100 with evidence.
   Pull the inputs from real checks: crawlability from script C, schema_coverage
   from how many key pages pass B, content_citability from the linter, and AI
   citation/share-of-voice from the Cowork AI-visibility tracker.
2. Run `python scripts/geo_score.py assets/geo_scorecard.yml`.
3. Record the GEO score + sub-scores with the date. The trend over months is the
   signal — a single number is not.

## Scripts (all CLI, run with `python scripts/<name> --help`)
- `check_ai_crawlers.py` — robots.txt access for AI/search bots; CI-gateable.
- `validate_schema.py` — JSON-LD extraction + integrity + required-field checks.
- `passage_lint.py` — atomic-passage / citability heuristics for prose.
- `geo_score.py` — weighted GEO score from the YAML/JSON scorecard.

Only `geo_score.py` (YAML mode) needs a dependency: `pip install pyyaml`. The
rest are standard-library only. A JSON scorecard removes even that.

## What this skill deliberately does NOT do
- It does not measure what ChatGPT/Gemini/Perplexity actually say — that needs
  real query testing (done in Cowork or a third-party AI-visibility tool) fed
  back into the scorecard. Don't fabricate citation numbers.
- It does not replace `claude-seo`'s broad audits — run both; they compose.
- It does not invent metrics. Unverifiable statistics get removed, not published.
